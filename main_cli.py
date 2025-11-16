import asyncio
import sys
from pathlib import Path

# Import all the building blocks
from app.adapters.sqlite import SQLiteAdapter
from app.core.tmdl_parser import TMDLParser
from app.core.model_analyzer import ModelAnalyzer
from app.core.schema_generator import SchemaGenerator
from app.core.doc_generator import DocumentationGenerator
from app.services.ingestion_service import IngestionService
from app.pipelines.full_pipeline import FullIngestionPipeline
from app.services.semantic_service import SemanticService


def get_required_path(prompt: str) -> Path:
    while True:
        path_str = input(prompt).strip().strip("'\"")
        if not path_str:
            print("This path is required. Please enter it.")
            continue
        path = Path(path_str)
        if not path.is_dir():
            print(f"[ERROR] Path not found or is not a directory: {path}")
        else:
            return path


def get_yes_no(prompt: str) -> bool:
    while True:
        answer = input(prompt).strip().lower()
        if answer in ('y', 'yes'):
            return True
        if answer in ('n', 'no', ''):
            return False
        print("Please answer 'y' or 'n'.")


def main():
    print("--- Power BI to SQL Pipeline ---")

    # 1. Get User Input
    tmdl_path = get_required_path(
        "Enter the path to the TMDL definition folder:\n> ")
    csv_path = get_required_path(
        "Enter the path to the CSV data dump folder:\n> ")
    output_dir = get_required_path(
        "Enter the path to the output directory:\n> ")
    recreate = get_yes_no("Recreate the database? (y/n) [n]: ")

    # --- UPDATED FLAGS ---
    gen_simple_docs = get_yes_no(
        "Generate simple data_dictionary.md? (y/n) [n]: ")
    gen_ai_summary_file = get_yes_no(
        "Generate ai_model_summary.md file? (y/n) [n]: ")
    run_ai_analysis = get_yes_no(
        "Run expensive AI analysis to embed summaries in DB? (y/n) [n]: ")
    # --- END UPDATED FLAGS ---

    output_dir.mkdir(parents=True, exist_ok=True)
    db_path = output_dir / "pbi_model.sqlite"
    inc_path = output_dir / "incremental.yaml"
    idx_path = output_dir / "index_config.yaml"

    doc_path = output_dir / "data_dictionary.md" if gen_simple_docs else None
    ai_summary_file_path = output_dir / \
        "ai_model_summary.md" if gen_ai_summary_file else None

    # 2. Build the "Leaf" Components
    adapter = SQLiteAdapter(db_path=db_path, csv_path=csv_path)
    parser = TMDLParser(str(tmdl_path))
    analyzer = ModelAnalyzer()
    schema_gen = SchemaGenerator()
    doc_gen = DocumentationGenerator(adapter)  # DocGen needs an adapter

    # 3. Build the "Engines" (The Services)
    ingestion_service = IngestionService(
        tmdl_path=tmdl_path,
        csv_path=csv_path,
        adapter=adapter,
        parser=parser,
        analyzer=analyzer,
        schema_gen=schema_gen,
        doc_gen=doc_gen
    )
    # Build the new service
    semantic_service = SemanticService(adapter=adapter)

    # 4. Build the "Workflow" (The Pipeline)
    pipeline = FullIngestionPipeline(
        service=ingestion_service,
        inc_path=inc_path,
        idx_path=idx_path,
        semantic_service=semantic_service,  # Inject the new service
        doc_generator=doc_gen               # Inject the doc generator
    )

    # 5. Run the Workflow
    try:
        asyncio.run(pipeline.run(
            recreate_db=recreate,
            generate_docs_path=doc_path,
            generate_ai_summary_file_path=ai_summary_file_path,
            run_semantic_analysis=run_ai_analysis
        ))
    except Exception as e:
        print(f"\n[FATAL] An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
