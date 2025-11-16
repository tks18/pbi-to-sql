import asyncio
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from app.adapters.base import DatabaseAdapter
from app.core.tmdl_parser import TMDLParser
from app.core.model_analyzer import ModelAnalyzer
from app.core.schema_generator import SchemaGenerator
from app.core.doc_generator import DocumentationGenerator
from app.types import ModelData, ConfigData, TableDefs, CycleGroups


class IngestionService:
    """
    Provides granular, individual steps for the ingestion process.
    This is the core 'engine' that GUIs, APIs, or Pipelines will use.
    """

    def __init__(
        self,
        tmdl_path: Path,
        csv_path: Path,
        adapter: DatabaseAdapter,
        parser: TMDLParser,
        analyzer: ModelAnalyzer,
        schema_gen: SchemaGenerator,
        doc_gen: DocumentationGenerator
    ):
        self.tmdl_path = tmdl_path
        self.csv_path = csv_path
        self.adapter = adapter
        self.parser = parser
        self.analyzer = analyzer
        self.schema_gen = schema_gen
        self.doc_gen = doc_gen

    async def connect(self, recreate: bool = False):
        await self.adapter.connect(recreate)

    async def close(self):
        await self.adapter.close()

    async def parse_model(self) -> ModelData:
        """Parses the TMDL files into a structured object."""
        tables = self.parser.parse_tables()
        relationships = self.parser.parse_relationships()
        print(
            f"[info] Parsed {len(tables)} tables and {len(relationships)} relationships.")
        return ModelData(tables=tables, relationships=relationships)

    async def prepare_configs(
        self,
        model_data: ModelData,
        inc_path: Path,
        idx_path: Path
    ) -> ConfigData:
        """Loads or suggests config files."""

        def load_or_suggest(path, suggester_func, *args):
            if path.is_file():
                with open(path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}

            suggestions = suggester_func(*args)
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(suggestions, f, sort_keys=False)
            print(f"[info] Wrote suggested config to {path}. Please review.")
            return suggestions

        inc_map = load_or_suggest(
            inc_path,
            self.analyzer.suggest_primary_keys,
            model_data.tables,
            model_data.relationships
        )
        idx_cfg = load_or_suggest(
            idx_path,
            self.analyzer.infer_indexes_from_relationships,
            model_data.tables,
            model_data.relationships
        )
        return ConfigData(incremental=inc_map, index=idx_cfg)

    async def create_schema(self, model_data: ModelData) -> CycleGroups:
        """Builds and executes the schema DDL."""
        self.schema_gen.build_fk_map(model_data.relationships)
        await self.adapter.create_metadata_tables()  # Create metadata tables first

        cycles = await self.adapter.create_schema(
            self.schema_gen,
            model_data.tables,
            model_data.relationships
        )
        if cycles:
            print(
                f"[warn] Detected {len(cycles)} cycle(s). FKs will be enforced after load.")
        return cycles

    async def load_data(self, tables: TableDefs, incremental_map: Dict[str, List[str]]):
        await self.adapter.load_all_tables(tables, incremental_map)

    async def apply_cyclic_fks(self, cycles: CycleGroups, tables: TableDefs):
        if cycles:
            await self.adapter.enforce_cyclic_fks(self.schema_gen, cycles, tables)

    async def create_indexes(self, index_config: Dict[str, List[str]]):
        await self.adapter.create_indexes(index_config)

    async def populate_metadata(self, model_data: ModelData):
        """Populates all metadata and profiles the data."""
        await self.adapter.populate_model_metadata(self.tmdl_path, self.csv_path)

        for r in model_data.relationships:
            await self.adapter.populate_relationship_metadata(r)

        for t, cols in model_data.tables.items():
            await self.adapter.populate_metadata(t, cols, self.csv_path)
        print("[db] Metadata populated.")

        print("[info] Profiling data for ML metadata...")
        tasks = [self.adapter.profile_table(t)
                 for t in model_data.tables.keys()]
        await asyncio.gather(*tasks)
        print("[info] Data profiling complete.")

    async def generate_docs(self) -> str:
        """Generates the markdown doc string."""
        return await self.doc_gen.generate_markdown()
