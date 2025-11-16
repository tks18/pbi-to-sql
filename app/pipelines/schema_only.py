#!/usr/bin/env python3
from pathlib import Path
from app.pipelines.base import BasePipeline
from app.services.ingestion_service import IngestionService
from app.types import ConfigData, ModelData


class SchemaOnlyPipeline(BasePipeline):
    """
    This pipeline ONLY parses the model and builds/recreates the
    database schema, indexes, and metadata tables.
    It does NOT load any data.
    """

    def __init__(self, service: IngestionService, inc_path: Path, idx_path: Path):
        super().__init__(service)
        self.inc_path = inc_path
        self.idx_path = idx_path

    async def run(self, recreate_db: bool = True, **kwargs):
        print("--- Starting Schema-Only Pipeline ---")
        try:
            await self.service.connect(recreate=recreate_db)

            # 1. Parse
            model_data = await self.service.parse_model()

            # 2. Config (needed for index suggestions, etc.)
            config_data = await self.service.prepare_configs(
                model_data, self.inc_path, self.idx_path
            )

            # 3. Schema
            await self.service.create_schema(model_data)

            # 4. Indexes (empty tables, but schema is ready)
            await self.service.create_indexes(config_data.index)

            print("[info] Schema, indexes, and metadata tables created.")

        except Exception as e:
            print(f"[ERROR] Schema pipeline failed: {e}")
            raise
        finally:
            await self.service.close()

        print("--- Schema-Only Pipeline Complete ---")
