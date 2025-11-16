import asyncio
from pathlib import Path
from typing import List, Set

from app.adapters.base import DatabaseAdapter
from app.types import TableDefs, RelationshipDef


class MetadataManager:
    """
    Handles orchestration of metadata population.
    This class is now database-agnostic.
    """

    def __init__(self, adapter: DatabaseAdapter):
        self.adapter = adapter

    async def populate_all_metadata(self, tables: TableDefs, relationships: List[RelationshipDef], tmdl_path: Path, csv_path: Path):

        # 1. Populate top-level model info
        await self.adapter.populate_model_metadata(tmdl_path, csv_path)

        # 2. Populate relationships
        for r in relationships:
            await self.adapter.populate_relationship_metadata(r)

        # 3. Populate table and column metadata
        for t, cols in tables.items():
            await self.adapter.populate_metadata(t, cols, csv_path)

        print("[db] Metadata populated.")

        # 4. Profile data (asynchronously)
        print("[info] Profiling data for ML metadata...")
        tasks = [self.adapter.profile_table(t) for t in tables.keys()]
        await asyncio.gather(*tasks)
        print("[info] Data profiling complete.")
