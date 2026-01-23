"""
Build ChromaDB vector store from processed data files.

Usage:
    python scripts/build_vectorstore.py
    python scripts/build_vectorstore.py --collection symptoms
    python scripts/build_vectorstore.py --clear

Input:
    data/processed/symptoms.jsonl
    data/processed/medications.jsonl
    data/processed/records.jsonl

Output:
    vectorstore/  - ChromaDB persistent storage
"""

import sys
import json
import argparse
from pathlib import Path
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import (
    PROCESSED_DATA_DIR,
    VECTORSTORE_PATH,
    COLLECTIONS,
    DATA_FILES,
    EMBEDDING_MODEL,
    EMBEDDING_DIM
)


def load_jsonl(filepath):
    """Load data from a JSONL file."""
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data


def sanitize_metadata(metadata):
    """Remove None values from metadata (ChromaDB doesn't accept None)."""
    if metadata is None:
        return {}
    return {k: v for k, v in metadata.items() if v is not None}


def build_collection(collection_name, data_file, embedding_model, chroma_client, clear=False):
    """Build a single ChromaDB collection from data file."""
    print(f"\n{'='*60}")
    print(f"Building Collection: {collection_name}")
    print(f"{'='*60}")

    if not data_file.exists():
        print(f"[WARNING] Data file not found: {data_file}")
        print(f"[INFO] Run 'python scripts/download_all.py' first")
        return 0

    print(f"[INFO] Loading data from: {data_file}")
    data = load_jsonl(data_file)
    print(f"[INFO] Loaded {len(data)} records")

    if not data:
        print("[WARNING] No data to process")
        return 0

    existing_collections = [c.name for c in chroma_client.list_collections()]

    if collection_name in existing_collections:
        if clear:
            print(f"[INFO] Deleting existing collection: {collection_name}")
            chroma_client.delete_collection(collection_name)
        else:
            print(f"[INFO] Collection '{collection_name}' already exists")
            collection = chroma_client.get_collection(collection_name)
            count = collection.count()
            print(f"[INFO] Current document count: {count}")
            print("[INFO] Use --clear flag to rebuild")
            return count

    print(f"[INFO] Creating collection: {collection_name}")
    collection = chroma_client.create_collection(
        name=collection_name,
        metadata={"description": f"MedBot {collection_name} knowledge base"}
    )

    batch_size = 100
    total_added = 0

    print(f"[INFO] Embedding and storing documents...")
    print(f"[INFO] Using model: {EMBEDDING_MODEL}")

    for i in tqdm(range(0, len(data), batch_size), desc="Processing batches"):
        batch = data[i:i + batch_size]

        ids = [item["id"] for item in batch]
        documents = [item["content"] for item in batch]
        metadatas = [sanitize_metadata(item.get("metadata")) for item in batch]

        embeddings = embedding_model.encode(documents).tolist()

        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings
        )

        total_added += len(batch)

    print(f"\n[SUCCESS] Added {total_added} documents to '{collection_name}'")
    return total_added


def build_all_collections(clear=False):
    """Build all vector store collections."""
    print("\n" + "=" * 70)
    print("  MedBot Vector Store Builder")
    print("=" * 70)

    print("\n[INFO] Loading embedding model...")
    from sentence_transformers import SentenceTransformer
    embedding_model = SentenceTransformer(EMBEDDING_MODEL)
    print(f"[INFO] Model loaded: {EMBEDDING_MODEL}")
    print(f"[INFO] Embedding dimension: {embedding_model.get_sentence_embedding_dimension()}")

    print(f"\n[INFO] Initializing ChromaDB at: {VECTORSTORE_PATH}")
    import chromadb
    VECTORSTORE_PATH.mkdir(parents=True, exist_ok=True)
    chroma_client = chromadb.PersistentClient(path=str(VECTORSTORE_PATH))

    results = {}

    for feature, collection_name in COLLECTIONS.items():
        data_file = DATA_FILES.get(collection_name)
        if data_file:
            count = build_collection(
                collection_name,
                data_file,
                embedding_model,
                chroma_client,
                clear=clear
            )
            results[collection_name] = count

    print("\n" + "=" * 70)
    print("  Build Summary")
    print("=" * 70)

    total_docs = 0
    for collection_name, count in results.items():
        status = "[OK]" if count > 0 else "[--]"
        print(f"  {status} {collection_name}: {count} documents")
        total_docs += count

    print(f"\n  Total: {total_docs} documents across {len(results)} collections")
    print("=" * 70)

    return results


def main():
    parser = argparse.ArgumentParser(description="Build MedBot vector store")
    parser.add_argument(
        "--collection",
        choices=list(COLLECTIONS.keys()),
        help="Build only this collection"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing collections before building"
    )

    args = parser.parse_args()

    if args.collection:
        from sentence_transformers import SentenceTransformer
        import chromadb

        print(f"[INFO] Loading embedding model: {EMBEDDING_MODEL}")
        embedding_model = SentenceTransformer(EMBEDDING_MODEL)

        print(f"[INFO] Initializing ChromaDB at: {VECTORSTORE_PATH}")
        VECTORSTORE_PATH.mkdir(parents=True, exist_ok=True)
        chroma_client = chromadb.PersistentClient(path=str(VECTORSTORE_PATH))

        collection_name = COLLECTIONS[args.collection]
        data_file = DATA_FILES.get(collection_name)
        build_collection(collection_name, data_file, embedding_model, chroma_client, args.clear)
    else:
        build_all_collections(clear=args.clear)

    print("\n[INFO] Vector store ready!")
    print("[INFO] Run 'python app.py' to start the application")


if __name__ == "__main__":
    main()
