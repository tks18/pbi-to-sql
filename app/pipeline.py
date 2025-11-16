import yaml
import os
from pathlib import Path
from .types import TableDefs, RelationshipDef
from .tmdl_parser import TMDLParser
from .model_analyzer import ModelAnalyzer
from .schema_generator import SchemaGenerator
from .metadata_manager import MetadataManager
from .doc_generator import DocumentationGenerator
from .adapters.base import DatabaseAdapter
from typing import Dict, Any, Optional


class IngestionPipeline:
    """
    Orchestrates the entire TMDL -> SQL pipeline.
    This class is now database-agnostic and uses an adapter.
    """

    def __init__(self, tmdl_path: Path, adapter: DatabaseAdapter,
                 incremental_config_path: Path, index_config_path: Path):

        self.tmdl_path = tmdl_path
        self.csv_path = adapter.csv_path  # Get csv_path from adapter

        # The pipeline now holds the adapter
        self.adapter = adapter

        self.incremental_config_path = incremental_config_path
        self.index_config_path = index_config_path

        self.parser = TMDLParser(str(tmdl_path))
        self.analyzer = ModelAnalyzer()
        self.schema_gen = SchemaGenerator()

        # MetadataManager and DocGenerator are now simpler
        self.metadata_mgr = MetadataManager(self.adapter)
        self.doc_gen = DocumentationGenerator(self.adapter)

    async def run(self, recreate_db: bool = False, generate_docs_path: Optional[Path] = None):
        print("--- Starting Pipeline ---")

        # 1. Parse
        tables = self.parser.parse_tables()
        relationships = self.parser.parse_relationships()
        print(
            f"[info] Parsed {len(tables)} tables and {len(relationships)} relationships.")

        # 2. Analyze & Get Config
        incremental_map = self._load_or_suggest_config(
            self.incremental_config_path, "incremental.yaml",
            self.analyzer.suggest_primary_keys, tables, relationships
        )
        index_cfg = self._load_or_suggest_config(
            self.index_config_path, "index_config.yaml",
            self.analyzer.infer_indexes_from_relationships, tables, relationships
        )

        try:
            # 3. Connect (via adapter)
            await self.adapter.connect(recreate=recreate_db)

            # 4. Build FK Map
            self.schema_gen.build_fk_map(relationships)

            # 5. Create Schema (via adapter)
            cycles = await self.adapter.create_schema(self.schema_gen, tables, relationships)
            if cycles:
                print(
                    f"[warn] Detected {len(cycles)} cycle(s). FKs will be enforced after load.")

            # 6. Create Metadata Tables (via adapter)
            await self.adapter.create_metadata_tables()

            # 7. Load Data (via adapter)
            await self.adapter.load_all_tables(tables, incremental_map)

            # 8. Enforce Cyclic FKs (via adapter)
            if cycles:
                await self.adapter.enforce_cyclic_fks(self.schema_gen, cycles, tables)

            # 9. Create Indexes (via adapter)
            await self.adapter.create_indexes(index_cfg)

            # 10. Populate Metadata
            await self.metadata_mgr.populate_all_metadata(
                tables, relationships, self.tmdl_path, self.csv_path
            )

            # 11. Generate Docs
            if generate_docs_path:
                print(
                    f"[info] Generating documentation at {generate_docs_path}...")
                markdown = await self.doc_gen.generate_markdown()
                with open(generate_docs_path, "w", encoding="utf-8") as f:
                    f.write(markdown)
                print("[info] Documentation generated.")

        except Exception as e:
            print(f"[ERROR] Pipeline run failed: {e}")
            raise
        finally:
            # 12. Close
            await self.adapter.close()

        print("--- Pipeline Complete ---")

    def _load_or_suggest_config(self, path: Path, default_name: str, suggester_func, *args) -> Dict[str, Any]:
        """Helper to load config or write suggestions if it doesn't exist."""
        if path.is_file():
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}

        suggestions = suggester_func(*args)
        # We always write to the derived path
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(suggestions, f, sort_keys=False)
        print(
            f"[info] Wrote suggested config to {path}. Please review and re-run.")

        return suggestions
