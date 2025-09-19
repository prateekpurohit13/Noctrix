from pathlib import Path
from typing import List, Tuple
from src.common.models import Element, ImageElement
from src.document_processor.ocr_service import perform_ocr

def process_image(file_path: Path) -> Tuple[List[Element], int]:
    print(f"  -> Processing as Image: '{file_path.name}'")
    full_text = perform_ocr(file_path)    
    image_element = ImageElement(
        type="image", 
        image_path=str(file_path),
        text_content=full_text.strip()
    )
    
    return [image_element], 1