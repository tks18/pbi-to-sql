import re
import hashlib
import aiofiles
from typing import Tuple, Optional


def safe_name(n: Optional[str]) -> Optional[str]:
    """Cleans a string to be a safe SQL identifier."""
    if n is None:
        return None
    return str(n).replace(" ", "_").replace("-", "_").replace(".", "_").replace("'", "").replace('"', '')


async def file_sha256(path: str) -> str:
    """Async SHA256 hash of a file."""
    h = hashlib.sha256()
    async with aiofiles.open(path, "rb") as f:
        while chunk := await f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def map_dtype(dtype: str) -> str:
    """Maps TMDL data types to SQLite data types."""
    if not dtype:
        return "TEXT"
    d = str(dtype).lower()
    if d in ("int64", "int32", "int", "integer", "whole", "long"):
        return "INTEGER"
    if d in ("double", "decimal", "float", "real", "numeric"):
        return "REAL"
    if d in ("boolean", "bool"):
        return "INTEGER"
    if d in ("date", "datetime", "date/time", "datetime64"):
        return "TEXT"
    if d in ("currency",):
        return "REAL"
    return "TEXT"


def is_tf_table(name: str) -> bool:
    """Checks if a table is a 'tf' (Timeframe) table."""
    if not name:
        return False
    n = name.lower()
    return n.startswith("d_tf_") or n.startswith("f_tf_")


def _kv_from_line(line: str) -> Tuple[str, str]:
    """Simple regex parser for 'key: value' lines."""
    m = re.match(r'^\s*([A-Za-z0-9_@\-]+)\s*:\s*(.+)$', line)
    if m:
        return m.group(1), m.group(2).strip()
    m = re.match(r'^\s*([A-Za-z0-9_@\-]+)\s*=\s*(.+)$', line)
    if m:
        return m.group(1), m.group(2).strip()
    m = re.match(r'^\s*([A-Za-z0-9_@\-]+)\s+(.+)$', line)
    if m:
        return m.group(1), m.group(2).strip()
    m = re.match(r'^\s*([A-Za-z0-9_@\-]+)\s*$', line)
    if m:
        return m.group(1), ""
    return "", ""


def _split_table_column(token: str) -> Tuple[Optional[str], Optional[str]]:
    """Splits 'Table'.'Column' into (Table, Column)."""
    if not token:
        return None, None
    tkn = token.strip()
    if "." in tkn:
        left, right = tkn.split(".", 1)
        table = left.strip().strip("'\"[] ")
        col = right.strip().strip("'\"[] ")
        return table, col
    return None, tkn.strip("'\"[] ")
