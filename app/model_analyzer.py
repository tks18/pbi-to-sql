from typing import List, Dict, Set

from app.types import TableDefs, RelationshipDef
from app.utils import is_tf_table


class ModelAnalyzer:
    """
    Analyzes the parsed model to suggest PKs, indexes, etc.
    """

    def suggest_primary_keys(self, tables: TableDefs, relationships: List[RelationshipDef]) -> Dict[str, List[str]]:
        """Suggests primary keys based on relationship 'to' columns and heuristics."""
        suggestions: Dict[str, List[str]] = {}
        referenced: Dict[str, Set[str]] = {}

        for r in relationships:
            to_tbl = str(r['to_table'])
            to_col = str(r['to_col'])
            referenced.setdefault(to_tbl, set()).add(to_col)

        for t, cols in tables.items():
            if is_tf_table(t):
                continue

            names = [str(c['name']) for c in cols]
            cand: List[str] = []

            if t in referenced:
                for rc in referenced[t]:
                    if rc in names:
                        cand.append(rc)

            patterns = [f"{t}ID".lower(), f"{t}_id".lower(), "id", "uid"]
            for p in patterns:
                for col in names:
                    if col.lower() == p and col not in cand:
                        cand.append(col)

            for col in names:
                if col.lower().endswith("id") and col not in cand:
                    cand.append(col)

            if cand:
                suggestions[t] = [cand[0]]  # Suggest the first best guess
        return suggestions

    def infer_indexes_from_relationships(self, tables: TableDefs, relationships: List[RelationshipDef]) -> Dict[str, List[str]]:
        """Infers required indexes from relationships and column name heuristics."""
        idx: Dict[str, List[str]] = {}

        for r in relationships:
            from_tbl, from_col = str(r['from_table']), str(r['from_col'])
            to_tbl, to_col = str(r['to_table']), str(r['to_col'])

            idx.setdefault(from_tbl, [])
            if from_col not in idx[from_tbl]:
                idx[from_tbl].append(from_col)

            idx.setdefault(to_tbl, [])
            if to_col not in idx[to_tbl]:
                idx[to_tbl].append(to_col)

        for t, cols in tables.items():
            for c in cols:
                cname = str(c['name'])
                if cname.lower().endswith("id") or cname.lower().endswith("_id") or cname.lower().endswith("uid") or cname.lower().endswith("key"):
                    idx.setdefault(t, [])
                    if cname not in idx[t]:
                        idx[t].append(cname)
        return idx
