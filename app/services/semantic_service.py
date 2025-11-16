import json
from app.adapters.base import DatabaseAdapter
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser


class SemanticService:
    """
    This service runs the expensive AI analysis to enrich the database
    with semantic information for RAG.
    """

    def __init__(self, adapter: DatabaseAdapter, model_name: str = "gemma3:4b"):
        self.adapter = adapter
        self.llm = OllamaLLM(model=model_name)
        self.str_parser = StrOutputParser()
        # Cache for table summaries to feed to relationship prompts
        self.table_summary_cache = {}

    async def _build_full_schema_context(self) -> str:
        """Fetches all metadata and formats it for the main model summary."""
        tables = await self.adapter.fetch_all(
            "SELECT table_name, row_count FROM table_metadata;"
        )
        all_cols = await self.adapter.fetch_all(
            "SELECT table_name, column_name, data_type FROM column_metadata;"
        )
        all_rels = await self.adapter.fetch_all(
            "SELECT from_table, from_col, to_table, to_col FROM relationship_metadata;"
        )

        prompt_lines = ["## Full Schema Context\n"]
        cols_map = {}
        for tbl, col, dtype in all_cols:
            cols_map.setdefault(tbl, []).append(f"{col} ({dtype})")

        for (tbl_name, row_count) in tables:
            prompt_lines.append(f"\n* **{tbl_name}** ({row_count} rows)")
            if cols_map.get(tbl_name):
                prompt_lines.append(
                    f"    * Columns: {', '.join(cols_map[tbl_name])}")

        prompt_lines.append("\n### Core Relationships (Foreign Keys)")
        for from_tbl, from_col, to_tbl, to_col in all_rels:
            prompt_lines.append(
                f"* `{from_tbl}.{from_col}` -> `{to_tbl}.{to_col}`")

        return "\n".join(prompt_lines)

    async def _get_llm_response(self, prompt_template: str, context: str) -> str:
        """Helper to run a single LLM chain."""
        try:
            prompt = PromptTemplate.from_template(prompt_template)
            chain = prompt | self.llm | self.str_parser
            response = await chain.ainvoke({"context": context})
            return response.strip()
        except Exception as e:
            print(f"[ai] Error calling local LLM: {e}")
            return f"Error: {e}"

    async def run_semantic_analysis(self):
        """
        Main workflow to analyze and embed semantic summaries for
        the entire model, each table, and each relationship.
        """
        print("[ai] Starting Semantic Analysis Workflow...")
        self.table_summary_cache = {}  # Clear cache

        # 1. Get all base metadata from the DB
        tables = await self.adapter.fetch_all("SELECT table_name FROM table_metadata;")
        relationships = await self.adapter.fetch_all("SELECT name, from_table, from_col, to_table, to_col FROM relationship_metadata;")

        # 2. Generate and embed high-level model summary
        print("[ai] Generating high-level model summary...")
        model_context = await self._build_full_schema_context()
        model_prompt = """
        You are a data model expert. Here is a database schema:
        {context}
        
        Please provide a concise yet detailed one-paragraph summary of what this data model represents. This summary will be read 
        by data scientists and RAG AI assistants to understand the model. So please be as detailed as possible.
        Example: 'This is a personal finance data model...'
        """
        model_summary = await self._get_llm_response(model_prompt, model_context)
        await self.adapter.embed_rag_summary(model_summary)
        print("[ai] ...high-level summary embedded.")

        # 3. Generate and embed summaries for each table
        print(f"[ai] Generating summaries for {len(list(tables))} tables...")
        table_prompt = """
        You are a data model expert. Here is the context for a single table:
        {context}
        
        Based on this context, provide a concise summary with two parts:
        1.  **Purpose:** A one-sentence summary of this table's purpose.
        2.  **Classification:** Classify this table as 'Fact', 'Dimension', 'Bridge', or 'Other'.
        
        Respond in JSON format, like this:
        {{"purpose": "...", "classification": "..."}}
        """

        for (table_name,) in tables:
            # Build a richer context for the table
            cols = await self.adapter.fetch_all("SELECT column_name, data_type FROM column_metadata WHERE table_name = ?;", (table_name,))
            incoming_rels = await self.adapter.fetch_all("SELECT from_table, from_col FROM relationship_metadata WHERE to_table = ?;", (table_name,))
            outgoing_rels = await self.adapter.fetch_all("SELECT to_table, to_col FROM relationship_metadata WHERE from_table = ?;", (table_name,))

            context_lines = [
                f"Table Name: {table_name}",
                f"Columns: {', '.join([f'{c[0]} ({c[1]})' for c in cols])}",
                f"Incoming Relationships (tables that point TO this): {', '.join([f'{r[0]}.{r[1]}' for r in incoming_rels]) or 'None'}",
                f"Outgoing Relationships (tables this points TO): {', '.join([f'{r[0]}.{r[1]}' for r in outgoing_rels]) or 'None'}"
            ]
            context = "\n".join(context_lines)

            table_summary_json = await self._get_llm_response(table_prompt, context)

            # Cache the summary for the next step
            self.table_summary_cache[table_name] = table_summary_json

            await self.adapter.embed_table_summary(table_name, table_summary_json)
        print("[ai] ...table summaries embedded.")

        # 4. Generate and embed summaries for each relationship
        print(
            f"[ai] Generating summaries for {len(list(relationships))} relationships...")
        rel_prompt = """
        You are a data model expert. Here is a single relationship and the AI-generated summaries
        of the two tables it connects:
        {context}
        
        Please provide a concise, natural language summary of this relationship's *purpose*.
        Example: 'This links an expense transaction to its specific sub-category for analysis.'
        Example: 'This connects a transaction to a date, allowing for time-based reporting.'
        """
        for (name, from_tbl, from_col, to_tbl, to_col) in relationships:
            # Build a *very* rich context using the summaries we just generated
            from_table_summary = self.table_summary_cache.get(from_tbl, "{}")
            to_table_summary = self.table_summary_cache.get(to_tbl, "{}")

            context_lines = [
                f"Relationship: {from_tbl}.{from_col} -> {to_tbl}.{to_col}",
                f"From Table ('{from_tbl}') Context: {from_table_summary}",
                f"To Table ('{to_tbl}') Context: {to_table_summary}"
            ]
            context = "\n".join(context_lines)

            rel_summary = await self._get_llm_response(rel_prompt, context)
            await self.adapter.embed_relationship_summary(name, rel_summary)
        print("[ai] ...relationship summaries embedded.")

        print("[ai] Semantic Analysis Workflow Complete.")
