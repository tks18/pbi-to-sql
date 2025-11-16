from app.adapters.base import DatabaseAdapter


class DocumentationGenerator:
    """
    Generates a Markdown data dictionary from the metadata tables.
    """

    def __init__(self, db: DatabaseAdapter):
        self.db = db

    async def generate_markdown(self) -> str:
        """Queries metadata and builds a Markdown string."""

        doc = ["# Data Dictionary"]

        tables = await self.db.fetch_all("SELECT table_name, row_count FROM table_metadata ORDER BY table_name;")

        for (tbl_name, row_count) in tables:
            doc.append(f"\n## Table: `{tbl_name}`")
            doc.append(f"*Estimated Rows: {row_count}*")

            doc.append(
                "\n### Columns\n| Column | Data Type | Description |\n|---|---|---|")
            cols = await self.db.fetch_all(
                "SELECT column_name, data_type, description FROM column_metadata WHERE table_name = ? ORDER BY column_name;", (
                    tbl_name,)
            )
            for (col_name, dtype, desc) in cols:
                doc.append(f"| `{col_name}` | {dtype} | {desc or ''} |")

            doc.append(
                "\n### Relationships\n| Role | Related Table | Via Column |\n|---|---|---|")
            rels = await self.db.fetch_all(
                "SELECT role, related_table, related_column FROM table_relationships WHERE table_name = ?;", (
                    tbl_name,)
            )
            if not rels:
                doc.append("| *None* | | |")
            for (role, rel_tbl, rel_col) in rels:
                doc.append(f"| {role.upper()} | `{rel_tbl}` | `{rel_col}` |")

        return "\n".join(doc)
