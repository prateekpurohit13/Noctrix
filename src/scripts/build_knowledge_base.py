import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.rag.knowledge_builder import KnowledgeBaseBuilder
from src.rag.vector_store import VectorStoreManager

def main():
    print("="*80)
    print("Noctrix Knowledge Base Builder")
    print("="*80)
    print()
    vector_store = VectorStoreManager(persist_directory="./vector_db")
    builder = KnowledgeBaseBuilder(
        dataset_path="dataset.json",
        vector_store=vector_store
    )
    
    print("Building knowledge base from dataset.json...")
    print("This may take a few minutes...")
    print()
    
    builder.build_all(reset_existing=True)
    
    print()
    print("="*80)
    print("Knowledge Base Built Successfully!")
    print("="*80)
    print()
    print("You can now use the RAG-enhanced agents.")
    print("Run: python src/main.py")

if __name__ == "__main__":
    main()