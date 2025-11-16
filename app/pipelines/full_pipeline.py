#!/usr/bin/env python3
from pathlib import Path
from typing import Optional
from app.pipelines.base import BasePipeline
from app.services.ingestion_service import IngestionService
from app.services.semantic_service import SemanticService
from app.core.doc_generator import DocumentationGenerator


class FullIngestionPipeline(BasePipeline):

    def __init__(self,
                 service: IngestionService,
                 inc_path: Path,
                 idx_path: Path,
                 # <-- Optional service
                 semantic_service: Optional[SemanticService] = None,
                 # <-- Optional generator
                 doc_generator: Optional[DocumentationGenerator] = None
                 ):
        super().__init__(service)
        self.inc_path = inc_path
        self.idx_path = idx_path
        self.semantic_service = semantic_service
        self.doc_generator = doc_generator

    async def run(self,
                  recreate_db: bool = False,
                  generate_docs_path: Optional[Path] = None,
                  generate_ai_summary_file_path: Optional[Path] = None,
                  run_semantic_analysis: bool = False,  # <-- New flag
                  **kwargs):

        print("--- Starting Full Ingestion Pipeline ---")
        try:
            # --- Main Ingestion ---
            await self.service.connect(recreate=recreate_db)
            model_data = await self.service.parse_model()
            config_data = await self.service.prepare_configs(model_data, self.inc_path, self.idx_path)
            cycles = await self.service.create_schema(model_data)
            await self.service.load_data(model_data.tables, config_data.incremental)
            await self.service.apply_cyclic_fks(cycles, model_data.tables)
            await self.service.create_indexes(config_data.index)
            await self.service.populate_metadata(model_data)
            print("[info] Main ingestion complete.")

            # --- Optional: Simple Docs ---
            if generate_docs_path and self.doc_generator:
                print(
                    f"[info] Generating simple documentation at {generate_docs_path}...")
                markdown = await self.doc_generator.generate_markdown()
                with open(generate_docs_path, "w", encoding="utf-8") as f:
                    f.write(markdown)
                print("[info] Simple documentation generated.")

            # --- Optional: High-Level AI Summary File ---
            if generate_ai_summary_file_path and self.doc_generator:
                print(
                    f"[info] Generating AI summary file at {generate_ai_summary_file_path}...")
                ai_markdown = await self.doc_generator.generate_ai_summary_file()
                if not ai_markdown.startswith("Error:"):
                    with open(generate_ai_summary_file_path, "w", encoding="utf-8") as f:
                        f.write(ai_markdown)
                    print(f"[info] AI summary file written.")
                else:
                    print(
                        f"[warn] Failed to generate AI summary file: {ai_markdown}")

            # --- Optional: Granular AI Semantic Embedding ---
            if run_semantic_analysis and self.semantic_service:
                print("[info] Starting separate semantic analysis workflow...")
                # We don't need to re-connect, just run the analysis
                await self.semantic_service.run_semantic_analysis()

        except Exception as e:
            print(f"[ERROR] Pipeline run failed: {e}")
            raise
        finally:
            await self.service.close()

        print("--- Pipeline Complete ---")
