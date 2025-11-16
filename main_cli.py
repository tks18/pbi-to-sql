import asyncio
import sys
from pathlib import Path
from app.pipeline import IngestionPipeline
from app.adapters.sqlite import SQLiteAdapter  # We will create this next


def get_required_path(prompt: str) -> Path:
    """Asks the user for a path and loops until a valid one is given."""
    while True:
        path_str = input(prompt).strip().strip("'\"")  # Clean up quotes/spaces
        if not path_str:
            print("This path is required. Please enter it.")
            continue

        path = Path(path_str)

        if not path.is_dir():
            print(f"[ERROR] Path not found or is not a directory.")
            print(f"  -> You entered: {path}")
            print("Please check the path and try again.")
        else:
            return path


def get_yes_no(prompt: str) -> bool:
    """Asks a simple Y/N question."""
    while True:
        answer = input(prompt).strip().lower()
        if answer in ('y', 'yes', ''):  # Default to Yes
            return True
        if answer in ('n', 'no'):
            return False
        print("Please answer 'y' or 'n'.")


def main():
    print("--- Power BI to SQL Pipeline ---")

    # 1. Get the 3 required paths using interactive input
    tmdl_path = get_required_path(
        "Enter the path to the TMDL definition folder:\n> "
    )
    csv_path = get_required_path(
        "Enter the path to the CSV data dump folder:\n> "
    )
    output_dir = get_required_path(
        "Enter the path to the output directory (files will be saved here):\n> "
    )

    # 2. Get optional flags
    recreate = get_yes_no(
        "Recreate the database if it exists? (y/n) [default: n]: "
    )
    generate_docs = get_yes_no(
        "Generate a data_dictionary.md file? (y/n) [default: y]: "
    )

    # 3. Create the output directory (no harm if it exists)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 4. Derive all other paths
    db_path = output_dir / "pbi_model.sqlite"
    inc_path = output_dir / "incremental.yaml"
    idx_path = output_dir / "index_config.yaml"
    doc_path = output_dir / "data_dictionary.md" if generate_docs else None

    # 5. Initialize the DB Adapter
    db_adapter = SQLiteAdapter(
        db_path=db_path,
        csv_path=csv_path
    )

    # 6. Initialize and run the pipeline
    pipeline = IngestionPipeline(
        tmdl_path=tmdl_path,
        adapter=db_adapter,
        incremental_config_path=inc_path,
        index_config_path=idx_path
    )

    try:
        asyncio.run(pipeline.run(
            recreate_db=recreate,
            generate_docs_path=doc_path
        ))
    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
