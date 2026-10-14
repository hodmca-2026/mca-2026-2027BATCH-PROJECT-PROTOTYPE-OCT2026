"""
Dense Embedding Store (ChromaDB + Sentence-Transformers)

Embeds each report's title + text with all-MiniLM-L6-v2 and stores
in a local ChromaDB persistent collection.

Course mapping: IR Unit IV — passage retrieval & ranking using a learned scoring function.
               IR Unit V — vector DB as cluster-based retrieval architecture.
"""

import json
import os
import logging
from typing import List, Dict, Optional

from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
COLLECTION_NAME = "iapis_reports"
CHROMA_PERSIST_DIR = os.path.join(
    os.path.dirname(__file__), "..", "models_store", "chroma"
)

# Singleton instances
_embedding_model = None
_chroma_client = None
_collection = None


def _get_embedding_model() -> SentenceTransformer:
    """Load the embedding model (singleton)."""
    global _embedding_model
    if _embedding_model is None:
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        logger.info("Embedding model loaded")
    return _embedding_model


def _get_collection(persist_dir: str = None):
    """Get or create the ChromaDB collection (singleton)."""
    global _chroma_client, _collection
    if _collection is not None:
        return _collection
    
    if persist_dir is None:
        persist_dir = CHROMA_PERSIST_DIR
    
    os.makedirs(persist_dir, exist_ok=True)
    
    _chroma_client = chromadb.PersistentClient(path=persist_dir)
    _collection = _chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    logger.info(f"ChromaDB collection '{COLLECTION_NAME}' ready ({_collection.count()} docs)")
    return _collection


def build_index(reports: List[dict], persist_dir: str = None) -> None:
    """
    Embed each report's title + text and upsert into ChromaDB.
    
    Args:
        reports: List of report dicts with at least 'id', 'title', 'text'.
        persist_dir: ChromaDB persistence directory.
    """
    model = _get_embedding_model()
    collection = _get_collection(persist_dir)
    
    # Prepare documents
    ids = []
    documents = []
    metadatas = []
    
    for report in reports:
        report_id = report["id"]
        combined_text = f"{report.get('title', '')} {report.get('text', '')}"
        
        ids.append(report_id)
        documents.append(combined_text)
        metadatas.append({
            "title": report.get("title", ""),
            "type": report.get("type", ""),
            "equipment": report.get("equipment", ""),
            "hazard_type": report.get("hazard_type", ""),
            "location": report.get("location", ""),
            "date": report.get("date", ""),
            "severity": report.get("severity", ""),
            "source": report.get("source", ""),
        })
    
    # Compute embeddings
    logger.info(f"Embedding {len(documents)} documents...")
    embeddings = model.encode(documents, show_progress_bar=True, batch_size=32)
    embeddings_list = embeddings.tolist()
    
    # Upsert in batches (ChromaDB has batch limits)
    batch_size = 100
    for i in range(0, len(ids), batch_size):
        batch_end = min(i + batch_size, len(ids))
        collection.upsert(
            ids=ids[i:batch_end],
            embeddings=embeddings_list[i:batch_end],
            documents=documents[i:batch_end],
            metadatas=metadatas[i:batch_end],
        )
    
    logger.info(f"Indexed {len(ids)} reports in ChromaDB (total in collection: {collection.count()})")


def dense_search(query: str, k: int = 10, persist_dir: str = None) -> List[Dict]:
    """
    Perform dense vector search for the given query.
    
    Args:
        query: Natural language query string.
        k: Number of results to return.
        persist_dir: ChromaDB persistence directory.
    
    Returns:
        List of dicts: [{id, score, report}, ...] sorted by similarity (descending).
    """
    model = _get_embedding_model()
    collection = _get_collection(persist_dir)
    
    if collection.count() == 0:
        logger.warning("ChromaDB collection is empty. Run build_index first.")
        return []
    
    # Embed the query
    query_embedding = model.encode([query]).tolist()
    
    # Query ChromaDB
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=min(k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )
    
    # Format results
    output = []
    for i in range(len(results["ids"][0])):
        # ChromaDB cosine distance = 1 - cosine_similarity, so lower = more similar
        distance = results["distances"][0][i]
        similarity = 1.0 - distance  # Convert to similarity score
        
        output.append({
            "id": results["ids"][0][i],
            "score": round(similarity, 4),
            "document": results["documents"][0][i] if results["documents"] else "",
            "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
        })
    
    return output


def reset_index(persist_dir: str = None):
    """Delete and recreate the ChromaDB collection."""
    global _collection
    if persist_dir is None:
        persist_dir = CHROMA_PERSIST_DIR
    
    client = chromadb.PersistentClient(path=persist_dir)
    try:
        client.delete_collection(COLLECTION_NAME)
        logger.info(f"Deleted collection '{COLLECTION_NAME}'")
    except Exception:
        pass
    
    _collection = None
    return _get_collection(persist_dir)


if __name__ == "__main__":
    # Build index from reports.json
    reports_path = os.path.join(os.path.dirname(__file__), "..", "data", "reports", "reports.json")
    
    if not os.path.exists(reports_path):
        print(f"Reports file not found: {reports_path}")
        print("Run scripts/generate_synthetic_reports.py first.")
    else:
        with open(reports_path, "r", encoding="utf-8") as f:
            reports = json.load(f)
        
        build_index(reports)
        
        # Quick test search
        test_results = dense_search("overheating motor", k=3)
        print(f"\nTest query: 'overheating motor' -> {len(test_results)} results")
        for r in test_results:
            print(f"  {r['id']}: score={r['score']:.4f} — {r['metadata'].get('title', '')[:80]}")
