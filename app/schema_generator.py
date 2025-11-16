from typing import List, Dict, Optional, Set, Tuple
from .types import TableDefs, RelationshipDef, DependencyGraph, TopoSortOrder, CycleGroups, ColumnDef
from .utils import safe_name, is_tf_table


class SchemaGenerator:
    """
    Generates SQL DDL, handles dependency graphs, and detects cycles.
    """

    def __init__(self):
        self.fk_map: Dict[str, List[str]] = {}
        self.rel_map: Dict[str, List[RelationshipDef]] = {}

    def build_fk_map(self, relationships: List[RelationshipDef]):
        """Builds maps for FK clause generation."""
        for r in relationships:
            from_tbl_raw = r.get('from_table')
            from_col_raw = r.get('from_col')
            to_tbl_raw = r.get('to_table')
            to_col_raw = r.get('to_col')
            if not all([from_tbl_raw, from_col_raw, to_tbl_raw, to_col_raw]):
                continue  # Skip relationships with missing parts
            from_tbl, from_col = str(from_tbl_raw), str(from_col_raw)
            to_tbl, to_col = str(to_tbl_raw), str(to_col_raw)

            if r.get("skip_fk", False) or is_tf_table(from_tbl) or is_tf_table(to_tbl):
                continue

            clause = self.generate_fk_clause(from_col, to_tbl, to_col)
            if clause:
                self.fk_map.setdefault(from_tbl, []).append(clause)
            self.rel_map.setdefault(from_tbl, []).append(r)

    def generate_fk_clause(self, from_col: str, to_table: str, to_col: str) -> Optional[str]:
        """Generates a single, deferrable FK clause."""
        s_from_col = safe_name(from_col)
        s_to_table = safe_name(to_table)
        s_to_col = safe_name(to_col)
        if not all([s_from_col, s_to_table, s_to_col]):
            print(
                f"[warn] Skipping invalid FK: {from_col}, {to_table}, {to_col}")
            return None
        return f"FOREIGN KEY([{s_from_col}]) REFERENCES [{s_to_table}]([{s_to_col}]) DEFERRABLE INITIALLY DEFERRED"

    def generate_create_table_sql(self, table_name: str, columns: List[ColumnDef], fk_clauses: List[str]) -> Optional[str]:
        """Generates the full CREATE TABLE statement."""
        s_table_name = safe_name(table_name)
        if not s_table_name:
            print(f"[warn] Skipping table with invalid name: {table_name}")
            return None
        col_defs = []
        for c in columns:
            s_col_name = safe_name(c['name'])
            if s_col_name:
                col_defs.append(f"[{s_col_name}] {c['type']}")
            else:
                print(
                    f"[warn] Skipping invalid column {c.get('name')} in table {s_table_name}")

        col_defs.extend(fk_clauses)
        if not col_defs:
            print(
                f"[warn] Skipping table {s_table_name} as it has no valid columns.")
            return None
        return f"CREATE TABLE IF NOT EXISTS [{s_table_name}] ({', '.join(col_defs)});"

    def _build_dependency_graph(self, relationships: List[RelationshipDef]) -> DependencyGraph:
        """Builds a graph for topological sorting."""
        g: DependencyGraph = {}
        for r in relationships:
            if r.get("skip_fk", False):
                continue
            a_raw = r.get('from_table')
            b_raw = r.get('to_table')
            if not a_raw or not b_raw:
                continue
            a, b = str(a_raw), str(b_raw)
            g.setdefault(a, set()).add(b)
            g.setdefault(b, set())
        return g

    def get_schema_creation_order(self, relationships: List[RelationshipDef], all_tables: Set[str]) -> Tuple[TopoSortOrder, CycleGroups]:
        """Performs a topological sort to find creation order and cycles."""
        graph = self._build_dependency_graph(relationships)

        # Ensure all tables are in the graph
        for t in all_tables:
            graph.setdefault(t, set())

        in_deg = {u: 0 for u in graph}
        for u in graph:
            for v in graph[u]:
                in_deg[v] += 1

        q = [u for u in graph if in_deg[u] == 0]
        order: TopoSortOrder = []

        while q:
            n = q.pop(0)
            order.append(n)
            for m in list(graph.get(n, [])):
                in_deg[m] -= 1
                if in_deg[m] == 0:
                    q.append(m)

        cycles: CycleGroups = []
        remaining = set(graph.keys()) - set(order)
        if remaining:
            print(f"[warn] Detected cycles involving: {remaining}")
            # Naive cycle detection, good enough for this
            cycles.append(remaining)

        return order, cycles
