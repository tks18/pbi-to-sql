#!/usr/bin/env python3
from pathlib import Path
from app.pipelines.base import BasePipeline
from app.services.ingestion_service import IngestionService
from app.types import ConfigData, ModelData


class DataOnlyPipeline(BasePipeline):
    """
    This pipeline loads data into an EXISTING schema.
    It does NOT parse TMDL, create tables, or add indexes.
    It assumes the schema is already correct.
    """

    def __init__(self, service: IngestionService, inc_path: Path):
        super().__init__(service)
        self.inc_path = inc_path

    async def run(self, **kwargs):
        print("--- Starting Data-Only Pipeline ---")
        try:
            await self.service.connect(recreate=False)  # Must not recreate

            # 1. Parse (needed to know what tables to load)
            model_data = await self.service.parse_model()

            # 2. Config (needed for incremental keys)
            # We'll just load the incremental config, not suggest
            configData = await self.service.prepare_configs(
                model_data, self.inc_path, Path("dummy_index.yaml")
            )

            # 3. Data Load
            await self.service.load_data(model_data.tables, configData.incremental)

            # 4. Populate Metadata (updates row counts, SHAs, and profiles)
            await self.service.populate_metadata(model_data)

            print("[info] Data loaded and metadata refreshed.")

        except Exception as e:
            print(f"[ERROR] Data pipeline failed: {e}")
            raise
        finally:
            await self.service.close()

        print("--- Data-Only Pipeline Complete ---")
