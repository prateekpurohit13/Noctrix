import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import json
from pathlib import Path
from .embeddings import EmbeddingService

class VectorStoreManager:
    def __init__(self, persist_directory: str = "./vector_db"):
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        print(f"[VectorStore] Initializing ChromaDB at: {self.persist_directory}")
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        self.embedding_service = EmbeddingService()
        self.collections = {
            "entity_patterns": None,
            "compliance_rules": None,
            "contextual_patterns": None,
            "complex_scenarios": None,
            "anonymization_strategies": None,
            "validation_rules": None
        }
        
        print("[VectorStore] Initialized successfully")
    
    def create_or_get_collection(self, name: str) -> chromadb.Collection:
        if self.collections[name] is None:
            self.collections[name] = self.client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"}
            )
        return self.collections[name]
    
    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ):
        
        collection = self.create_or_get_collection(collection_name)
        
        if ids is None:
            ids = [f"{collection_name}_{i}" for i in range(len(documents))]
        embeddings = self.embedding_service.embed_texts(documents)
        collection.add(
            documents=documents,
            embeddings=embeddings.tolist(),
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"[VectorStore] Added {len(documents)} documents to '{collection_name}'")
    
    def query(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        collection = self.create_or_get_collection(collection_name)
        query_embedding = self.embedding_service.embed_text(query_text)
        results = collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results,
            where=where
        )       
        return results
    
    def get_collection_count(self, collection_name: str) -> int:
        collection = self.create_or_get_collection(collection_name)
        return collection.count()
    
    def reset_collection(self, collection_name: str):
        try:
            self.client.delete_collection(collection_name)
            print(f"[VectorStore] Deleted collection: {collection_name}")
        except:
            pass
        self.collections[collection_name] = None
        self.create_or_get_collection(collection_name)
    
    def get_stats(self) -> Dict[str, int]:
        stats = {}
        for name in self.collections.keys():
            try:
                stats[name] = self.get_collection_count(name)
            except:
                stats[name] = 0
        return stats