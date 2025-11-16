import aiosqlite
import sqlite3
import pandas as pd
import asyncio
import os
from pathlib import Path
from typing import Iterable, List, Dict, Set, Optional, Any
from app.adapters.base import DatabaseAdapter
from app.types import TableDefs, RelationshipDef, CycleGroups
from app.schema_generator import SchemaGenerator
from app.utils import safe_name, is_tf_table, file_sha256


class SQLiteAdapter(DatabaseAdapter):
    """
    Implementation of the DatabaseAdapter for SQLite.
    This class now holds all logic from db_manager and data_loader.
    """

    def __init__(self, db_path: Path, csv_path: Path):
        self.db_path_str = str(db_path)
        self._csv_path = csv_path
        self.conn: Optional[aiosqlite.Connection] = None

    @property
    def csv_path(self) -> Path:
        return self._csv_path

    async def connect(self, recreate: bool = False):
        if recreate and os.path.exists(self.db_path_str):
            os.remove(self.db_path_str)
        self.conn = await aiosqlite.connect(self.db_path_str)
        await self.conn.execute("PRAGMA foreign_keys = ON;")
        await self.conn.commit()
        print(f"[db] Connected to {self.db_path_str}")

    async def close(self):
        if self.conn:
            await self.conn.close()
            self.conn = None
            print("[db] Connection closed.")

    async def _execute(self, sql: str, params: tuple = ()):
        """Internal helper for single execute."""
        if not self.conn:
            return
        await self.conn.execute(sql, params)

    async def fetch_all(self, query: str, params: tuple = ()) -> Iterable:
        if not self.conn:
            return []
        async with self.conn.execute(query, params) as cursor:
            return await cursor.fetchall()

    # --- Schema Logic (from db_manager) ---
    async def create_schema(self, schema_gen: SchemaGenerator, tables: TableDefs, relationships: List[RelationshipDef]) -> CycleGroups:
        if not self.conn:
            raise ConnectionError("DB not connected")

        order, cycles = schema_gen.get_schema_creation_order(
            relationships, set(tables.keys()))
        created = set()

        async with self.conn.cursor() as cur:
            for t in order:
                if t not in tables:
                    continue
                in_cycle = any(t in comp for comp in cycles)
                fks = [] if (in_cycle or is_tf_table(
                    t)) else schema_gen.fk_map.get(t, [])
                sql = schema_gen.generate_create_table_sql(t, tables[t], fks)
                if sql:
                    await cur.execute(sql)
                    created.add(t)

            for t in tables.keys():
                if t in created:
                    continue
                in_cycle = any(t in comp for comp in cycles)
                fks = [] if (in_cycle or is_tf_table(
                    t)) else schema_gen.fk_map.get(t, [])
                sql = schema_gen.generate_create_table_sql(t, tables[t], fks)
                if sql:
                    await cur.execute(sql)
                    created.add(t)

        await self.conn.commit()
        return cycles

    async def enforce_cyclic_fks(self, schema_gen: SchemaGenerator, cycles: CycleGroups, tables: TableDefs):
        if not self.conn:
            return
        print("[db] Enforcing FKs for cyclic dependencies...")
        async with self.conn.cursor() as cur:
            for comp in cycles:
                for t in comp:
                    if is_tf_table(t) or t not in tables:
                        continue
                    new_table = f"__new_{safe_name(t)}"
                    cols = tables[t]
                    fk_clauses = schema_gen.fk_map.get(t, [])
                    sql_create = schema_gen.generate_create_table_sql(
                        new_table, cols, fk_clauses)
                    if not sql_create:
                        continue

                    await cur.execute(sql_create)
                    old_cols = [c for c in [
                        safe_name(c['name']) for c in cols] if c is not None]
                    s_table_name = safe_name(t)
                    if not s_table_name or not old_cols:
                        continue

                    col_list = ", ".join([f"[{c}]" for c in old_cols])
                    await cur.execute(f"INSERT INTO [{new_table}] ({col_list}) SELECT {col_list} FROM [{s_table_name}];")
                    await cur.execute(f"DROP TABLE [{s_table_name}];")
                    await cur.execute(f"ALTER TABLE [{new_table}] RENAME TO [{s_table_name}];")
        await self.conn.commit()
        print("[db] Cyclic FKs enforced.")

    async def create_indexes(self, index_config: Dict[str, List[str]]):
        if not self.conn:
            return
        print("[db] Creating indexes...")
        created_count = 0
        async with self.conn.cursor() as cur:
            await cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
            all_tables = {row[0] for row in await cur.fetchall()}
            table_cols: Dict[str, Set[str]] = {}
            for tbl_safe_name in all_tables:
                await cur.execute(f"PRAGMA table_info([{tbl_safe_name}]);")
                table_cols[tbl_safe_name] = {r[1].lower() for r in await cur.fetchall()}
            for tbl, cols in index_config.items():
                tbl_safe = safe_name(tbl)
                if tbl_safe not in all_tables:
                    continue
                for c in cols:
                    if tbl_safe:
                        col_safe = safe_name(c)
                        if not col_safe or col_safe.lower() not in table_cols[tbl_safe]:
                            continue
                        idxname = f"idx_{tbl_safe}_{col_safe}"
                        sql = f"CREATE INDEX IF NOT EXISTS [{idxname}] ON [{tbl_safe}]([{col_safe}]);"
                        try:
                            await cur.execute(sql)
                            created_count += 1
                        except Exception as e:
                            print(
                                f"[warn] failed to create index {idxname}: {e}")
        await self.conn.commit()
        print(f"[db] Created/validated {created_count} indexes.")

    # --- Data Load Logic (from data_loader) ---
    async def load_all_tables(self, tables: TableDefs, incremental_map: Dict[str, List[str]]):
        for t in tables.keys():
            csv_file = self.csv_path / f"{t}.csv"
            if not csv_file.exists():
                print(f"[warn] csv not found for {t}, skipping load")
                continue

            df = await asyncio.to_thread(pd.read_csv, csv_file, dtype=str, keep_default_na=False)
            df.columns = [safe_name(c) for c in df.columns]

            if is_tf_table(t):
                print(f"[load-full] TF table {t} (full load)")
                await asyncio.to_thread(self._load_full_sync, t, df)
                continue
            keys = incremental_map.get(t)
            if keys:
                print(f"[upsert] {t} keys={keys}")
                await asyncio.to_thread(self._upsert_sync, t, df, keys)
            else:
                print(f"[load-full] {t} (full load)")
                await asyncio.to_thread(self._load_full_sync, t, df)

    def _load_full_sync(self, table: str, df: pd.DataFrame):
        tbl_safe = safe_name(table)
        with sqlite3.connect(self.db_path_str) as conn:
            if tbl_safe:
                conn.execute("PRAGMA foreign_keys = ON;")
                conn.execute(f"DELETE FROM [{tbl_safe}];")
                df.to_sql(tbl_safe, conn, if_exists="append", index=False)
                conn.commit()

    def _upsert_sync(self, table: str, df: pd.DataFrame, key_cols: List[str]):
        tbl_safe = safe_name(table)
        tmp = f"tmp_{tbl_safe}"
        keys_safe = [k for k in [safe_name(c)
                                 for c in key_cols] if k is not None]
        with sqlite3.connect(self.db_path_str) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            idx_name = f"ux_{tbl_safe}_{'_'.join(keys_safe)}"
            cols_sql = ", ".join([f"[{c}]" for c in keys_safe])
            conn.execute(
                f"CREATE UNIQUE INDEX IF NOT EXISTS [{idx_name}] ON [{tbl_safe}] ({cols_sql});")
            df.to_sql(tmp, conn, if_exists="replace", index=False)
            all_cols = ", ".join([f"[{c}]" for c in df.columns])
            conn.execute(
                f"INSERT OR REPLACE INTO [{tbl_safe}] ({all_cols}) SELECT {all_cols} FROM [{tmp}];")
            conn.execute(f"DROP TABLE IF EXISTS [{tmp}];")
            conn.commit()

    # --- Metadata Logic (from metadata_manager) ---
    async def create_metadata_tables(self):
        if not self.conn:
            return
        sql_statements = [
            "CREATE TABLE IF NOT EXISTS model_metadata (model_name TEXT, created_at TEXT DEFAULT (datetime('now')), tmdl_path TEXT, csv_path TEXT);",
            "CREATE TABLE IF NOT EXISTS table_metadata (table_name TEXT PRIMARY KEY, row_count INTEGER, sample_json TEXT, csv_sha256 TEXT, last_loaded TEXT);",
            "CREATE TABLE IF NOT EXISTS column_metadata (table_name TEXT, column_name TEXT, data_type TEXT, description TEXT, PRIMARY KEY (table_name, column_name));",
            "CREATE TABLE IF NOT EXISTS relationship_metadata (name TEXT PRIMARY KEY, from_table TEXT, from_col TEXT, to_table TEXT, to_col TEXT, cardinality TEXT);",
            "CREATE TABLE IF NOT EXISTS table_relationships (table_name TEXT, relationship_name TEXT, role TEXT, related_table TEXT, related_column TEXT);",
            "CREATE TABLE IF NOT EXISTS column_statistics (table_name TEXT, column_name TEXT, total_count INTEGER, missing_count INTEGER, missing_percent REAL, unique_count INTEGER, unique_percent REAL, mean REAL, std_dev REAL, min REAL, max REAL, PRIMARY KEY (table_name, column_name));"
        ]
        async with self.conn.cursor() as cur:
            for sql in sql_statements:
                await cur.execute(sql)
        await self.conn.commit()
        print("[db] Metadata tables created/validated.")

    async def populate_model_metadata(self, tmdl_path: Path, csv_path: Path):
        if self.conn:
            await self._execute(
                "INSERT INTO model_metadata (model_name, tmdl_path, csv_path) VALUES (?, ?, ?)",
                ("powerbi_model", str(tmdl_path), str(csv_path))
            )
            await self.conn.commit()

    async def populate_relationship_metadata(self, r: RelationshipDef):
        if self.conn:
            try:
                await self._execute(
                    "INSERT OR REPLACE INTO relationship_metadata (name, from_table, from_col, to_table, to_col, cardinality) VALUES (?, ?, ?, ?, ?, ?)",
                    (r.get("name"), r.get("from_table"), r.get("from_col"),
                     r.get("to_table"), r.get("to_col"), r.get("cardinality"))
                )
                await self._execute(
                    "INSERT INTO table_relationships (table_name, relationship_name, role, related_table, related_column) VALUES (?, ?, ?, ?, ?)",
                    (r.get("from_table"), r.get("name"),
                     "from", r.get("to_table"), r.get("to_col"))
                )
                await self._execute(
                    "INSERT INTO table_relationships (table_name, relationship_name, role, related_table, related_column) VALUES (?, ?, ?, ?, ?)",
                    (r.get("to_table"), r.get("name"), "to",
                     r.get("from_table"), r.get("from_col"))
                )
                await self.conn.commit()
            except Exception as e:
                print(
                    f"[warn] failed to insert relationship metadata for {r.get('name')}: {e}")

    async def populate_metadata(self, table: str, cols: List[Dict[str, Any]], csv_path: Path):
        if not self.conn:
            return
        csv_file = csv_path / f"{table}.csv"
        row_count, sample_json, sha = None, None, None

        if csv_file.exists():
            try:
                # Run sync pandas read in a thread
                df = await asyncio.to_thread(pd.read_csv, csv_file, dtype=str, keep_default_na=False, nrows=5)
                sample_json = df.to_json(orient="records")
                sha = await file_sha256(str(csv_file))
                row_count = sum(1 for _ in open(
                    csv_file, "r", encoding="utf-8")) - 1
            except Exception as e:
                print(
                    f"[warn] Could not read CSV for table metadata {table}: {e}")

        await self._execute(
            "INSERT OR REPLACE INTO table_metadata (table_name, row_count, sample_json, csv_sha256, last_loaded) VALUES (?, ?, ?, ?, datetime('now'))",
            (table, row_count, sample_json, sha)
        )
        for c in cols:
            await self._execute(
                "INSERT OR REPLACE INTO column_metadata (table_name, column_name, data_type, description) VALUES (?, ?, ?, ?)",
                (table, c['name'], c['type'], None)
            )
        await self.conn.commit()

    def _profile_table_sync(self, table_name: str, db_path: str):
        tbl_safe = safe_name(table_name)
        stats_to_insert = []
        try:
            with sqlite3.connect(db_path) as conn:
                df = pd.read_sql_query(f"SELECT * FROM [{tbl_safe}];", conn)
                for col in df.columns:
                    col_data = df[col]
                    total_count, missing_count, unique_count = len(col_data), int(
                        col_data.isnull().sum()), int(col_data.nunique())
                    missing_pct = (missing_count /
                                   total_count) if total_count > 0 else 0
                    unique_pct = (
                        unique_count / total_count) if total_count > 0 else 0
                    mean, std, min_val, max_val = None, None, None, None
                    if pd.api.types.is_numeric_dtype(col_data):
                        stats = col_data.describe()
                        raw_mean, raw_std, raw_min, raw_max = stats.get(
                            'mean'), stats.get('std'), stats.get('min'), stats.get('max')
                        mean = float(raw_mean) if pd.notna(raw_mean) else None
                        std = float(raw_std) if pd.notna(raw_std) else None
                        min_val = float(raw_min) if pd.notna(raw_min) else None
                        max_val = float(raw_max) if pd.notna(raw_max) else None
                    stats_to_insert.append((table_name, col, total_count, missing_count,
                                           missing_pct, unique_count, unique_pct, mean, std, min_val, max_val))
                conn.executemany("INSERT OR REPLACE INTO column_statistics (table_name, column_name, total_count, missing_count, missing_percent, unique_count, unique_percent, mean, std_dev, min, max) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", stats_to_insert)
                conn.commit()
        except Exception as e:
            print(f"[warn] Could not profile table {table_name}: {e}")

    async def profile_table(self, table_name: str):
        if is_tf_table(table_name):
            return
        await asyncio.to_thread(self._profile_table_sync, table_name, self.db_path_str)
