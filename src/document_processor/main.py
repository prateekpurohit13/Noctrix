import zipfile
import tempfile
import hashlib
import magic
import shutil
from pathlib import Path
from datetime import datetime
from typing import List
from src.common.models import DocumentObjectModel, Element
from src.common.exceptions import ProcessingError, UnsupportedFileTypeError
from .handlers import pdf_handler, image_handler, office_handler

def _process_single_file(file_path: Path, temp_dir_for_images: Path) -> DocumentObjectModel:
    try:
        file_content = file_path.read_bytes()
        file_hash = hashlib.sha256(file_content).hexdigest()
        processed_timestamp = datetime.now().isoformat()
        file_name = file_path.name
        mime_type = magic.from_buffer(file_content, mime=True)
    except Exception as e:
        raise ProcessingError(f"Failed to read file '{file_path.name}': {e}") from e
    sections: List[Element] = []
    page_count: int = 1
    if "pdf" in mime_type:
        sections, page_count = pdf_handler.process_pdf(file_path, temp_dir_for_images)
    elif "image" in mime_type:
        sections, page_count = image_handler.process_image(file_path)
    elif "openxmlformats-officedocument" in mime_type or file_path.suffix.lower() in ['.docx', '.xlsx', '.pptx']:
        sections, page_count = office_handler.process_office_doc(file_path, temp_dir_for_images)
    else:
        raise UnsupportedFileTypeError(f"Unsupported file type '{mime_type}' for file '{file_name}'")

    dom = DocumentObjectModel(
        file_name=file_name,
        file_hash=file_hash,
        processed_timestamp=processed_timestamp,
        page_count=page_count,
        sections=sections,
        initial_metadata={"detected_mime_type": mime_type, "original_file_size_bytes": len(file_content)}
    )
    return dom

def process_input(input_path: Path) -> List[DocumentObjectModel]:
    if not input_path.exists():
        raise FileNotFoundError(f"Input not found: {input_path}")
    processed_doms: List[DocumentObjectModel] = []
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        try:
            mime_type = magic.from_file(str(input_path), mime=True)
        except Exception as e:
            raise ProcessingError(f"Could not determine file type for {input_path.name}: {e}")

        if mime_type == "application/zip":
            print(f"Detected ZIP archive. Extracting...")
            with zipfile.ZipFile(input_path, 'r') as zip_ref:
                zip_ref.extractall(temp_path)

            for extracted_file_path in sorted(temp_path.rglob("*")):
                if extracted_file_path.is_file() and not extracted_file_path.name.startswith('.'):
                    try:
                        dom = _process_single_file(extracted_file_path, temp_path)
                        processed_doms.append(dom)
                    except (UnsupportedFileTypeError, ProcessingError) as e:
                        print(f"  -> WARNING: Skipping file '{extracted_file_path.name}'. Reason: {e}")
        else:
            print(f"Detected single file...")
            dom = _process_single_file(input_path, temp_path)
            processed_doms.append(dom)

    if not processed_doms:
        print("WARNING: No valid files were processed.")
        
    return processed_doms