from typing import List, Dict, Any, Set, Tuple, Optional, TypeAlias
from pydantic import BaseModel, Field

# --- Core Data Models ---


class ColumnDef(BaseModel):
    """Defines the structure of a single parsed column."""
    name: str
    type: str
    sourceColumn: Optional[str] = None
    sortByColumn: Optional[str] = None
    isCalculated: bool = False


class RelationshipDef(BaseModel):
    """Defines the structure of a single parsed relationship."""
    name: str
    from_table: Optional[str] = None
    from_col: Optional[str] = None
    to_table: Optional[str] = None
    to_col: Optional[str] = None
    cardinality: Optional[str] = None
    isActive: bool = True
    skip_fk: bool = False


TableDefs: TypeAlias = Dict[str, List[ColumnDef]]
DependencyGraph: TypeAlias = Dict[str, Set[str]]
TopoSortOrder: TypeAlias = List[str]
CycleGroups: TypeAlias = List[Set[str]]


class ModelData(BaseModel):
    """Holds all parsed model information."""
    tables: TableDefs = Field(default_factory=dict)
    relationships: List[RelationshipDef] = Field(default_factory=list)


class ConfigData(BaseModel):
    """Holds all config information."""
    incremental: Dict[str, List[str]] = Field(default_factory=dict)
    index: Dict[str, List[str]] = Field(default_factory=dict)
