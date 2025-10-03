from __future__ import annotations
import json
import hashlib
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Optional
from .vector_store import VectorStoreManager
from .knowledge_builder import KnowledgeBaseBuilder
from .retrieval import RAGRetriever

_DEFAULT_PERSIST_DIR = "./vector_db"
_DEFAULT_DATASET_PATH = "dataset.json"
_META_FILENAME = "knowledge_meta.json"


def _compute_dataset_signature(dataset_path: Path) -> str:
    hasher = hashlib.sha256()
    with dataset_path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def _meta_file(persist_directory: Path) -> Path:
    return persist_directory / _META_FILENAME

def _ensure_populated(
    store: VectorStoreManager,
    dataset_path: Path,
) -> None:
    dataset_signature = _compute_dataset_signature(dataset_path)
    meta_path = _meta_file(Path(store.persist_directory))
    needs_build = True

    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if meta.get("dataset_signature") == dataset_signature:
                needs_build = False
        except json.JSONDecodeError:
            needs_build = True

    if needs_build:
        print("[RAGService] Building knowledge base from dataset.json ...")
        builder = KnowledgeBaseBuilder(
            dataset_path=str(dataset_path),
            vector_store=store,
        )
        builder.build_all(reset_existing=True)
        meta_payload = {
            "dataset_signature": dataset_signature,
            "built_at": datetime.utcnow().isoformat() + "Z",
            "dataset_version": builder.dataset.get("metadata", {}).get("dataset_version"),
        }
        meta_path.write_text(json.dumps(meta_payload, indent=2), encoding="utf-8")
    else:
        stats = store.get_stats()
        if any(count == 0 for count in stats.values()):
            print("[RAGService] Detected empty collections; rebuilding knowledge base ...")
            builder = KnowledgeBaseBuilder(
                dataset_path=str(dataset_path),
                vector_store=store,
            )
            builder.build_all(reset_existing=True)
            meta_payload = {
                "dataset_signature": dataset_signature,
                "rebuilt_at": datetime.utcnow().isoformat() + "Z",
                "dataset_version": builder.dataset.get("metadata", {}).get("dataset_version"),
            }
            meta_path.write_text(json.dumps(meta_payload, indent=2), encoding="utf-8")

@lru_cache(maxsize=None)
def _get_vector_store(persist_directory: str) -> VectorStoreManager:
    return VectorStoreManager(persist_directory=persist_directory)

@lru_cache(maxsize=None)
def _get_rag_retriever(persist_directory: str) -> RAGRetriever:
    store = _get_vector_store(persist_directory)
    return RAGRetriever(vector_store=store)

def get_rag_retriever(
    persist_directory: Optional[str] = None,
    dataset_path: Optional[str] = None,
) -> RAGRetriever:
    persist_dir = persist_directory or _DEFAULT_PERSIST_DIR
    dataset = dataset_path or _DEFAULT_DATASET_PATH

    dataset_file = Path(dataset)
    if not dataset_file.exists():
        raise FileNotFoundError(f"Dataset not found at {dataset_file.resolve()}")

    store = _get_vector_store(persist_dir)
    _ensure_populated(store, dataset_file)
    return _get_rag_retriever(persist_dir)


def reset_caches() -> None:
    _get_rag_retriever.cache_clear()
    _get_vector_store.cache_clear()