from typing import List, Optional
from sentence_transformers import SentenceTransformer
import numpy as np
from functools import lru_cache

class EmbeddingService:   
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        print(f"[EmbeddingService] Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        print(f"[EmbeddingService] Model loaded. Embedding dimension: {self.dimension}")
    
    def embed_text(self, text: str) -> np.ndarray:
        return self.model.encode(text, convert_to_numpy=True)
    
    def embed_texts(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        return self.model.encode(
            texts, 
            batch_size=batch_size,
            convert_to_numpy=True,
            show_progress_bar=len(texts) > 100
        )
    
    @lru_cache(maxsize=1000)
    def embed_cached(self, text: str) -> np.ndarray:
        return self.embed_text(text)
    
    def similarity(self, text1: str, text2: str) -> float:
        emb1 = self.embed_text(text1)
        emb2 = self.embed_text(text2)
        return float(np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2)))