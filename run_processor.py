import json
from pathlib import Path
from src.document_processor.main import process_input

def main():
    input_dir = Path("data/input")
    output_dir = Path("data/output")
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    file_to_process = "File_003.png"   
    test_path = input_dir / file_to_process

    if not test_path.exists():
        print(f"ERROR: Test file '{file_to_process}' not found in '{input_dir.resolve()}'.")
        return
    try:
        print(f"Starting processing for: {test_path.name}")
        list_of_doms = process_input(test_path)        
        if not list_of_doms:
            print("Processing finished, but no documents were successfully processed.")
            return
        print(f"\nProcessing complete. {len(list_of_doms)} document(s) were processed successfully.")
        for dom in list_of_doms:
            output_file_name = f"{Path(dom.file_name).stem}_dom.json"
            output_file_path = output_dir / output_file_name
            with open(output_file_path, "w", encoding="utf-8") as f:
                f.write(dom.model_dump_json(indent=2))
            print(f"  -> Saved DOM for '{dom.file_name}' to: {output_file_path.resolve()}")
    except Exception as e:
        print(f"\nA critical error occurred during processing: {e}")

if __name__ == "__main__":
    main()