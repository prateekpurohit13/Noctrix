import fitz
from pathlib import Path
from typing import List, Tuple
from src.common.models import Element, TextElement, ImageElement, Position
from src.document_processor.ocr_service import perform_ocr

def process_pdf(file_path: Path, temp_dir: Path) -> Tuple[List[Element], int]:
    print(f"  -> Processing as PDF: '{file_path.name}'")
    elements: List[Element] = []
    doc = fitz.open(file_path)
    page_count = doc.page_count

    for page_num in range(page_count):
        page = doc.load_page(page_num)
        text = page.get_text().strip()
        if len(text) > 20:
            print(f"  -> Page {page_num+1} has native text layer. Extracting directly.")
            blocks = page.get_text("dict")["blocks"]
            for b in blocks:
                if b['type'] == 0:
                    for l in b['lines']:
                        for s in l['spans']:
                            elements.append(TextElement(type="text", text_content=s['text']))
        else:
            print(f"  -> Page {page_num+1} appears to be scanned. Performing OCR.")
            pix = page.get_pixmap(dpi=300)
            image_path = temp_dir / f"page_{page_num+1}.png"
            pix.save(str(image_path))
            ocr_text = perform_ocr(image_path)
            if ocr_text:
                elements.append(TextElement(type="paragraph", text_content=ocr_text))

        images = page.get_images(full=True)
        for img_index, img in enumerate(images):
            xref = img[0]
            try:
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                image_path = temp_dir / f"p{page_num+1}_img{img_index+1}.{image_ext}"
                with open(image_path, "wb") as f:
                    f.write(image_bytes)               
                print(f"  -> Found embedded image on page {page_num+1}. OCRing...")
                ocr_text = perform_ocr(image_path)
                elements.append(ImageElement(type="image", text_content=ocr_text, image_path=str(image_path)))
            except Exception as e:
                print(f"  -> WARNING: Could not extract embedded image on page {page_num+1}. Reason: {e}")

    doc.close()
    return elements, page_count