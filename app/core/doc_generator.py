#!/usr/bin/env python3
import json
from app.adapters.base import DatabaseAdapter
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser


class DocumentationGenerator:
    """
    Generates documentation from the metadata tables.
    - generate_markdown: Creates a simple, structured data dictionary.
    - generate_ai_summary: Uses a local LLM to create a high-level RAG summary.
    """

    def __init__(self, db: DatabaseAdapter):
        self.db = db

    async def generate_markdown(self) -> str:
        """Queries metadata and builds a simple Markdown string."""
        doc = ["# Data Dictionary"]

        tables = await self.db.fetch_all(
            "SELECT table_name, row_count FROM table_metadata ORDER BY table_name;"
        )

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

    async def _build_schema_context(self) -> str:
        """Fetches all metadata and formats it as a simple text block for the LLM."""

        # 1. Fetch all schema data
        tables = await self.db.fetch_all(
            "SELECT table_name, row_count, sample_json FROM table_metadata;"
        )
        all_cols = await self.db.fetch_all(
            "SELECT table_name, column_name, data_type FROM column_metadata;"
        )
        all_rels = await self.db.fetch_all(
            "SELECT from_table, from_col, to_table, to_col FROM relationship_metadata;"
        )

        # 2. Format it
        prompt_lines = [
            "## Schema Details\n",
            "### Tables (Name, Estimated Rows, Sample Data)",
        ]

        cols_map = {}
        for tbl, col, dtype in all_cols:
            cols_map.setdefault(tbl, []).append(f"{col} ({dtype})")

        for tbl_name, row_count, sample_json in tables:
            prompt_lines.append(f"\n* **{tbl_name}** ({row_count} rows)")
            if cols_map.get(tbl_name):
                prompt_lines.append(
                    f"    * Columns: {', '.join(cols_map[tbl_name])}")
            if sample_json:
                prompt_lines.append(f"    * Sample: {sample_json}")

        prompt_lines.append("\n### Core Relationships (Foreign Keys)")
        for from_tbl, from_col, to_tbl, to_col in all_rels:
            prompt_lines.append(
                f"* `{from_tbl}.{from_col}` -> `{to_tbl}.{to_col}`")

        return "\n".join(prompt_lines)

    async def _call_local_llm_for_summary(self, schema_context: str) -> str:
        """Calls a local LLM via LangChain (Ollama) to generate the summary."""
        print("[ai] Calling local LLM (Ollama) to generate documentation...")

        template = """
        You are a senior Data Architect. Your task is to generate a comprehensive, high-level summary 
        of the following SQLite database schema. This summary will be read by data scientists and 
        RAG AI assistants to understand the model.

        Here is the schema context you must analyze:
        {schema_context}

        ## Your Task
        
        Generate a summary in Markdown with the following *exact* structure:

        # Data Model Analysis

        ## 1. High-Level Summary
        (A one-paragraph overview of what this data model represents. Infer the domain, e.g., 'This appears to be a personal finance model...').

        ## 2. Key Entities & Classification
        (List the most important tables. *Crucially*, classify each as a 'Fact' table (storing events, transactions) or a 'Dimension' table (storing attributes, categories) and state its purpose.)
        
        * **[TABLE_NAME_1] (Dimension)**: (Purpose, e.g., "Dimension table for calendar dates.")
        * **[TABLE_NAME_2] (Fact)**: (Purpose, e.g., "Fact table for individual expense transactions.")
        * ...

        ## 3. Core Relationships & Data Flow
        (A natural language description of how the main 'fact' tables (like transactions) connect to the 'dimension' 
        tables (like categories, dates, assets). Describe the data flow.)

        ## 4. RAG Querying Guide
        (Provide 3-4 examples of how an AI should join tables to answer common questions. Be specific about the join keys.)
        
        * **Intent:** "Get total expenses by category name for a given month."
        * **Joins:** 1. `f_ExpenseTransactions` -> `d_ExpenseSubCategory` (on `CATEGORY_ID` = `UID`)
            2. `f_ExpenseTransactions` -> `d_Calendar` (on `DATE` = `Date`)
        
        * **Intent:** "Get total income by asset name."
        * **Joins:** 1. `f_IncomeTransactions` -> `d_AssetSubCategory` (on `ASSET_ID` = `UID`)

        * **Intent:** "Calculate the opening balance for all assets on a specific date."
        * **Joins:** 1. `f_OpeningBalances` -> `d_AssetSubCategory` (on `ZASSETUID` = `UID`)
            2. `f_OpeningBalances` -> `d_Calendar` (on `ZTXDATESTR` = `Date`)
        """

        prompt_template = PromptTemplate.from_template(template)

        try:
            llm = OllamaLLM(model="gemma3:4b")
            chain = prompt_template | llm | StrOutputParser()
            summary = await chain.ainvoke({"schema_context": schema_context})
            print("[ai] Successfully generated documentation from local LLM.")
            return summary

        except Exception as e:
            print(f"[ai] Error calling local LLM: {e}")
            print(
                "[ai] Make sure the Ollama server is running and the model (e.g., 'gemma:4b') is installed.")
            return f"Error: An exception occurred while calling the local LLM: {e}"

    async def generate_ai_summary_file(self) -> str:
        """
        Generates a rich, AI-powered summary markdown string.
        This method does NOT embed in the database.
        """
        context = await self._build_schema_context()
        summary = await self._call_local_llm_for_summary(context)
        return summary
