import os
import re
from typing import Any, Dict, List, Optional

from pydantic import ValidationError

from app.utils import _kv_from_line, _split_table_column, map_dtype, is_tf_table
from app.types import TableDefs, RelationshipDef, ColumnDef


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
            current_column_props: Dict[str, Any] = {}

            for ln in lines:
                s = ln.strip()
                if not s:
                    continue

                m_table = re.match(r'^\s*table\s+(.+)$',
                                   ln, flags=re.IGNORECASE)
                if m_table:
                    if current_table and current_column_props.get("name"):
                        try:
                            col_defs.append(ColumnDef(**current_column_props))
                        except ValidationError as e:
                            print(
                                f"[warn] Skipping invalid column in table {current_table}: {e}")
                    if current_table and not (current_table.upper().startswith("STG_") or current_table.upper() == "MEASURES_TABLE"):
                        result[current_table] = col_defs

                    current_table = m_table.group(1).strip()
                    col_defs = []
                    current_column = None
                    continue

                m_col = re.match(
                    r'^\s*column\s+(?:([A-Za-z0-9_@\-]+)|\'([^\']+)\'|"([^"]+)")\s*(=\s*.*)?$', ln, flags=re.IGNORECASE)
                if m_col and current_table:
                    if current_column_props.get("name"):
                        try:
                            col_defs.append(ColumnDef(**current_column_props))
                        except ValidationError as e:
                            print(
                                f"[warn] Skipping invalid column in table {current_table}: {e}")

                    colname = m_col.group(1) or m_col.group(
                        2) or m_col.group(3)
                    is_calc = m_col.group(4) is not None
                    current_column_props = {
                        "name": colname,
                        "type": "TEXT",  # Default
                        "isCalculated": is_calc
                    }
                    continue

                if current_column_props:
                    key, val = _kv_from_line(ln)
                    kl = key.lower()
                    if kl == "datatype":
                        current_column_props["type"] = map_dtype(val)
                    elif kl == "sourcecolumn":
                        current_column_props["sourceColumn"] = val.strip(
                            "[]'\" ")
                    elif kl == "sortbycolumn":
                        current_column_props["sortByColumn"] = val.strip(
                            "[]'\" ")
                    continue

            if current_column_props.get("name"):
                try:
                    col_defs.append(ColumnDef(**current_column_props))
                except ValidationError as e:
                    print(
                        f"[warn] Skipping invalid column in table {current_table}: {e}")
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
            current_rel_props: Dict[str, Any] = {}

            for ln in lines:
                s = ln.strip()
                if not s:
                    continue

                m_rel = re.match(r'^\s*relationship\s+(.+)$',
                                 s, flags=re.IGNORECASE)
                if m_rel:
                    if current_rel_props.get("name"):
                        try:
                            rel_obj = RelationshipDef(**current_rel_props)
                            if all([rel_obj.from_table, rel_obj.from_col, rel_obj.to_table, rel_obj.to_col]):
                                if rel_obj.isActive and not str(rel_obj.from_table).upper().startswith("STG_") and not str(rel_obj.to_table).upper().startswith("STG_") and str(rel_obj.from_table).upper() != "MEASURES_TABLE" and str(rel_obj.to_table).upper() != "MEASURES_TABLE":
                                    rels.append(rel_obj)
                        except ValidationError as e:
                            print(
                                f"[warn] Skipping invalid relationship {current_rel_props.get('name')}: {e}")

                    current_rel_props = {
                        "name": m_rel.group(1).strip().strip("'\"[] ")
                    }
                    continue

                if not current_rel_props:
                    continue

                key, val = _kv_from_line(ln)
                kl = key.lower()

                if kl == "isactive":
                    current_rel_props["isActive"] = val.lower() != "false"
                elif kl in ("fromcolumn", "from_column"):
                    t, c = _split_table_column(val)
                    if t:
                        current_rel_props["from_table"] = t
                    if c:
                        current_rel_props["from_col"] = c
                elif kl in ("tocolumn", "to_column"):
                    t, c = _split_table_column(val)
                    if t:
                        current_rel_props["to_table"] = t
                    if c:
                        current_rel_props["to_col"] = c
                elif kl == "cardinality":
                    current_rel_props["cardinality"] = val

            if current_rel_props.get("name"):
                try:
                    rel_obj = RelationshipDef(**current_rel_props)
                    if all([rel_obj.from_table, rel_obj.from_col, rel_obj.to_table, rel_obj.to_col]):
                        if rel_obj.isActive and not str(rel_obj.from_table).upper().startswith("STG_") and not str(rel_obj.to_table).upper().startswith("STG_") and str(rel_obj.from_table).upper() != "MEASURES_TABLE" and str(rel_obj.to_table).upper() != "MEASURES_TABLE":
                            rels.append(rel_obj)
                except ValidationError as e:
                    print(
                        f"[warn] Skipping invalid relationship {current_rel_props.get('name')}: {e}")

        for r in rels:
            if is_tf_table(str(r.from_table)) or is_tf_table(str(r.to_table)):
                r.skip_fk = True

        return rels
