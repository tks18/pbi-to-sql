#!/usr/bin/env python3
import asyncio
from pathlib import Path
from datetime import datetime

from airflow.sdk import DAG, task

from app.adapters.sqlite import SQLiteAdapter
from app.core.tmdl_parser import TMDLParser
from app.core.model_analyzer import ModelAnalyzer
from app.core.schema_generator import SchemaGenerator
from app.core.doc_generator import DocumentationGenerator
from app.services.ingestion_service import IngestionService
from app.pipelines.full_pipeline import FullIngestionPipeline
from app.services.semantic_service import SemanticService

TMDL_PATH = Path("/opt/airflow/pbi_project/SemanticModel/definition")
CSV_PATH = Path("/opt/airflow/pbi_exports/data")
OUTPUT_DIR = Path("/opt/airflow/pbi_output")

DB_PATH = OUTPUT_DIR / "pbi_model.sqlite"
INC_PATH = OUTPUT_DIR / "incremental.yaml"
IDX_PATH = OUTPUT_DIR / "index_config.yaml"
DOC_PATH = OUTPUT_DIR / "data_dictionary.md"
AI_DOC_PATH = OUTPUT_DIR / "ai_summary_for_rag.md"


def build_full_pipeline() -> FullIngestionPipeline:
    """
    Uses Dependency Injection to build the full pipeline object.
    This is the same logic as main_cli.py.
    """
    # 1. Build the "Leaf" Components
    adapter = SQLiteAdapter(db_path=DB_PATH, csv_path=CSV_PATH)
    parser = TMDLParser(str(TMDL_PATH))
    analyzer = ModelAnalyzer()
    schema_gen = SchemaGenerator()
    doc_gen = DocumentationGenerator(adapter)

    # 2. Build the "Engine" (The Service)
    service = IngestionService(
        tmdl_path=TMDL_PATH,
        csv_path=CSV_PATH,
        adapter=adapter,
        parser=parser,
        analyzer=analyzer,
        schema_gen=schema_gen,
        doc_gen=doc_gen
    )

    # Build the new service
    semantic_service = SemanticService(adapter=adapter)

    # 3. Build the "Workflow" (The Pipeline)
    pipeline = FullIngestionPipeline(
        service=service,
        inc_path=INC_PATH,
        idx_path=IDX_PATH,
        semantic_service=semantic_service,  # Inject the new service
        doc_generator=doc_gen               # Inject the doc generator
    )
    return pipeline


def pbi_ingestion_dag():
    """
    Airflow DAG for the full PBI to SQLite ingestion, including
    AI-powered documentation generation.
    """

    with DAG(
        dag_id="pbi_to_sqlite_ingestion",
        start_date=datetime(2025, 1, 1),
        schedule="@daily",
        catchup=False,
        tags=["pbi", "sqlite", "rag"]
    ) as dag:

        @task.tas
        def run_full_pbi_ingestion():
            """
            Airflow task to run the full async pipeline.
            """
            print(f"Starting PBI Ingestion. Output dir: {OUTPUT_DIR}")
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

            pipeline = build_full_pipeline()

            # Use asyncio.run() to bridge Airflow's sync world
            # with our async pipeline code.
            try:
                asyncio.run(pipeline.run(
                    recreate_db=True,
                    generate_docs_path=DOC_PATH,
                    # Note: The AI docs are now part of the main run
                    # We'll update the pipeline to handle this
                ))
                print("Pipeline run successful.")
            except Exception as e:
                print(f"Pipeline run failed: {e}")
                raise

        # Trigger the task
        run_full_pbi_ingestion()


# Make the DAG visible to Airflow
pbi_ingestion_dag()
