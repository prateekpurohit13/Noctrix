import base64
import requests
from pathlib import Path
from paddleocr import PaddleOCR
from src.common.exceptions import ProcessingError

try:
    print("Initializing PaddleOCR engine...")
    paddle_ocr_engine = PaddleOCR(use_textline_orientation=True, lang='en')
    print("PaddleOCR initialized successfully.")
except Exception as e:
    print(f"CRITICAL: Failed to initialize PaddleOCR. Error: {e}")
    paddle_ocr_engine = None

LLAVA_API_URL = "http://localhost:11434/api/generate"
CONFIDENCE_THRESHOLD = 0.88  #trigger fallback if PaddleOCR avg confidence is below this (0-1 scale)

def _ocr_image_with_paddle(image_path: Path) -> tuple[str, float]:
    if not paddle_ocr_engine:
        raise ProcessingError("PaddleOCR engine is not available.")
        
    full_text = []
    total_confidence = 0.0    
    result = paddle_ocr_engine.predict(str(image_path), use_textline_orientation=True)
    ocr_result = result[0] if result else None
    
    if not ocr_result or 'rec_texts' not in ocr_result:
        return "", 0.0
    
    texts = ocr_result['rec_texts']
    scores = ocr_result['rec_scores']
    
    if not texts or len(texts) == 0:
        return "", 0.0
    
    for i, text in enumerate(texts):
        full_text.append(text)
        if i < len(scores):
            total_confidence += float(scores[i])
    avg_confidence = (total_confidence / len(texts)) if texts else 0.0
    return "\n".join(full_text), avg_confidence

def _ocr_image_with_llava(image_path: Path) -> str:
    print(f"  -> Low confidence detected. Falling back to LLaVA for '{image_path.name}'...")
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        payload = {
            "model": "llava",
            "prompt": "Transcribe all text from this image accurately, including handwritten text. Maintain the original structure and layout where possible. Do not add any commentary or explanation, only provide the transcribed text.",
            "images": [encoded_string],
            "stream": False
        }
        response = requests.post(LLAVA_API_URL, json=payload, timeout=300)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except requests.exceptions.RequestException as e:
        print(f"  -> ERROR: LLaVA fallback request failed: {e}")
        return ""
    except Exception as e:
        print(f"  -> ERROR: An unexpected error occurred during LLaVA fallback: {e}")
        return ""

def perform_ocr(image_path: Path) -> str:
    try:
        paddle_text, paddle_confidence = _ocr_image_with_paddle(image_path)
        print(f"  -> PaddleOCR Result for '{image_path.name}': Avg Confidence = {paddle_confidence:.2f}")
    except ProcessingError as e:
        print(f"  -> ERROR: PaddleOCR failed: {e}. Cannot perform OCR.")
        return ""
    if paddle_confidence < CONFIDENCE_THRESHOLD:
        llava_text = _ocr_image_with_llava(image_path)
        return llava_text if llava_text else paddle_text
    else:
        return paddle_text