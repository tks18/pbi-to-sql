import os
import re
from typing import List, Optional
from .utils import _kv_from_line, _split_table_column, map_dtype, is_tf_table
from .types import TableDefs, RelationshipDef, ColumnDef


class TMDLParser:
    """Parses TMDL files to extract table and relationship definitions."""

    def __init__(self, tmdl_path: str):
        self.tmdl_path = tmdl_path
        self.tables_dir = os.path.join(tmdl_path, "tables")
        self.relationships_dir = os.path.join(tmdl_path, "relationships")
        self.relationships_file = os.path.join(tmdl_path, "relationships.tmdl")

    def _read_lines_clean(self, path: str) -> List[str]:
        with open(path, "r", encoding="utf-8") as fh:
            raw = fh.read()
        raw = raw.replace("\t", "    ").lstrip("\ufeff")
        raw = raw.replace("\r\n", "\n").replace("\r", "\n")
        return [ln.rstrip() for ln in raw.split("\n")]

    def parse_tables(self) -> TableDefs:
        """Parses .tmdl files under <tmdl_path>/tables"""
        if not os.path.isdir(self.tables_dir):
            raise FileNotFoundError(
                f"tables directory not found in {self.tmdl_path}")

        result: TableDefs = {}
        for fname in sorted(os.listdir(self.tables_dir)):
            if not fname.lower().endswith(".tmdl"):
                continue

            full_path = os.path.join(self.tables_dir, fname)
            lines = self._read_lines_clean(full_path)

            current_table: Optional[str] = None
            col_defs: List[ColumnDef] = []
            current_column: Optional[ColumnDef] = None

            for ln in lines:
                s = ln.strip()
                if not s:
                    continue

                m_table = re.match(r'^\s*table\s+(.+)$',
                                   ln, flags=re.IGNORECASE)
                if m_table:
                    if current_table and current_column:
                        col_defs.append(current_column)
                        current_column = None
                    if current_table and not (current_table.upper().startswith("STG_") or current_table.upper() == "MEASURES_TABLE"):
                        result[current_table] = col_defs

                    current_table = m_table.group(1).strip()
                    col_defs = []
                    current_column = None
                    continue

                m_col = re.match(
                    r'^\s*column\s+(?:([A-Za-z0-9_@\-]+)|\'([^\']+)\'|"([^"]+)")\s*(=\s*.*)?$', ln, flags=re.IGNORECASE)
                if m_col and current_table:
                    if current_column:
                        col_defs.append(current_column)

                    colname = m_col.group(1) or m_col.group(
                        2) or m_col.group(3)
                    is_calc = m_col.group(4) is not None
                    current_column = {
                        "name": str(colname).strip(),
                        "type": "TEXT",
                        "sourceColumn": None,
                        "sortByColumn": None,
                        "isCalculated": bool(is_calc)
                    }
                    continue

                if current_column:
                    key, val = _kv_from_line(ln)
                    kl = key.lower()
                    if kl == "datatype":
                        current_column["type"] = map_dtype(val)
                    elif kl == "sourcecolumn":
                        current_column["sourceColumn"] = val.strip("[]'\" ")
                    elif kl == "sortbycolumn":
                        current_column["sortByColumn"] = val.strip("[]'\" ")
                    continue

            if current_column:
                col_defs.append(current_column)
            if current_table and current_table not in result and not (current_table.upper().startswith("STG_") or current_table.upper() == "MEASURES_TABLE"):
                result[current_table] = col_defs

        return result

    def parse_relationships(self) -> List[RelationshipDef]:
        """Parses relationships from relationships/ or relationships.tmdl."""
        candidates = []
        if os.path.isdir(self.relationships_dir):
            for f in sorted(os.listdir(self.relationships_dir)):
                if f.lower().endswith(".tmdl"):
                    candidates.append(os.path.join(self.relationships_dir, f))
        if os.path.isfile(self.relationships_file):
            candidates.append(self.relationships_file)

        if not candidates:
            print("[warn] No relationship files found.")
            return []

        rels: List[RelationshipDef] = []
        for full in candidates:
            lines = self._read_lines_clean(full)
            current: Optional[RelationshipDef] = None

            for ln in lines:
                s = ln.strip()
                if not s:
                    continue

                m_rel = re.match(r'^\s*relationship\s+(.+)$',
                                 s, flags=re.IGNORECASE)
                if m_rel:
                    if current and all(current.get(k) for k in ["from_table", "from_col", "to_table", "to_col"]):
                        if current.get("isActive", True) and not str(current["from_table"]).upper().startswith("STG_") and not str(current["to_table"]).upper().startswith("STG_") and str(current["from_table"]).upper() != "MEASURES_TABLE" and str(current["to_table"]).upper() != "MEASURES_TABLE":
                            rels.append(current)

                    current = {
                        "name": m_rel.group(1).strip(),
                        "from_table": None, "from_col": None,
                        "to_table": None, "to_col": None,
                        "cardinality": None,
                        "isActive": True,
                        "skip_fk": False
                    }
                    continue

                if not current:
                    continue

                key, val = _kv_from_line(ln)
                kl = key.lower()

                if kl == "isactive":
                    current["isActive"] = val.lower() != "false"
                elif kl in ("fromcolumn", "from_column"):
                    t, c = _split_table_column(val)
                    current["from_table"], current["from_col"] = t, c
                elif kl in ("tocolumn", "to_column"):
                    t, c = _split_table_column(val)
                    current["to_table"], current["to_col"] = t, c

            if current and all(current.get(k) for k in ["from_table", "from_col", "to_table", "to_col"]):
                if current.get("isActive", True) and not str(current["from_table"]).upper().startswith("STG_") and not str(current["to_table"]).upper().startswith("STG_") and str(current["from_table"]).upper() != "MEASURES_TABLE" and str(current["to_table"]).upper() != "MEASURES_TABLE":
                    rels.append(current)

        for r in rels:
            if is_tf_table(str(r["from_table"])) or is_tf_table(str(r["to_table"])):
                r["skip_fk"] = True

        return rels
