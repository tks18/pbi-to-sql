from abc import ABC, abstractmethod
from typing import Iterable, List, Dict, Set, Optional, Any
from pathlib import Path
import pandas as pd
from app.types import TableDefs, RelationshipDef, CycleGroups
from app.schema_generator import SchemaGenerator


class DatabaseAdapter(ABC):
    """
    Abstract Base Class for all database operations.
    This makes the pipeline database-agnostic.
    """

    @property
    @abstractmethod
    def csv_path(self) -> Path:
        """The path to the source CSV data."""
        pass

    @abstractmethod
    async def connect(self, recreate: bool = False):
        """Establish the database connection."""
        pass

    @abstractmethod
    async def close(self):
        """Close the database connection."""
        pass

    @abstractmethod
    async def create_schema(self, schema_gen: SchemaGenerator, tables: TableDefs, relationships: List[RelationshipDef]) -> CycleGroups:
        """Create the table schema from TMDL definitions."""
        pass

    @abstractmethod
    async def enforce_cyclic_fks(self, schema_gen: SchemaGenerator, cycles: CycleGroups, tables: TableDefs):
        """Apply FKs for tables that were in a dependency cycle."""
        pass

    @abstractmethod
    async def create_indexes(self, index_config: Dict[str, List[str]]):
        """Create all indexes."""
        pass

    @abstractmethod
    async def load_all_tables(self, tables: TableDefs, incremental_map: Dict[str, List[str]]):
        """Load data from all CSVs into the database."""
        pass

    @abstractmethod
    async def create_metadata_tables(self):
        """Create the RAG-specific metadata tables."""
        pass

    @abstractmethod
    async def populate_metadata(self, table: str, cols: List[Dict[str, Any]], csv_path: Path):
        """Populate metadata for a single table."""
        pass

    @abstractmethod
    async def populate_relationship_metadata(self, r: RelationshipDef):
        """Populate metadata for a single relationship."""
        pass

    @abstractmethod
    async def populate_model_metadata(self, tmdl_path: Path, csv_path: Path):
        """Populate the top-level model metadata."""
        pass

    @abstractmethod
    async def profile_table(self, table_name: str):
        """Run statistical profiling on a single table."""
        pass

    @abstractmethod
    async def fetch_all(self, query: str, params: tuple = ()) -> Iterable:
        """Fetch all results for a query (for doc generator)."""
        pass
