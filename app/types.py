from typing import List, Dict, Any, Set, Tuple, TypeAlias

# A single column definition parsed from TMDL
ColumnDef = Dict[str, Any]

# A dictionary mapping table names to their list of columns
TableDefs = Dict[str, List[ColumnDef]]

# A single relationship definition parsed from TMDL
RelationshipDef = Dict[str, Any]

# A graph representation for dependencies
DependencyGraph = Dict[str, Set[str]]

# The result of a topological sort
TopoSortOrder = List[str]
CycleGroups = List[Set[str]]
