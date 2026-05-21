#!/usr/bin/env python3
"""
Knowledge Base Seeder — seeds ChromaDB with medical guideline documents.
Compatible with chromadb >= 1.0.

Usage:
    python scripts/seed_knowledge.py [--reset]
"""
from __future__ import annotations
import argparse, hashlib, sys
from pathlib import Path
from typing import Union

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from src.observability.logging import configure_logging, get_logger
configure_logging()
log = get_logger(__name__)

BUILTIN_DOCUMENTS = [
    {"id": "who-triage-001", "title": "WHO Emergency Triage Assessment", "category": "emergency",
     "content": "Emergency triage ABCDE: Airway, Breathing, Circulation, Disability, Exposure. "
                "Immediate threats: cardiac arrest, respiratory failure, severe bleeding, anaphylaxis, "
                "stroke FAST test, myocardial infarction with chest pain and arm radiation. Call 911."},
    {"id": "cardiac-001", "title": "Acute Coronary Syndrome Pre-hospital", "category": "emergency",
     "content": "ACS signs: chest pain radiating to arm jaw back, diaphoresis, nausea, shortness of breath. "
                "Pre-hospital: call 911, chew 325mg aspirin, rest, unlock door for paramedics. "
                "Do not drive yourself. Time is muscle, every minute causes irreversible cardiac damage."},
    {"id": "headache-001", "title": "Headache Assessment Protocol", "category": "urgent",
     "content": "RED FLAGS: thunderclap headache sudden worst ever, fever stiff neck rash meningitis, "
                "focal neurological symptoms stroke, new headache over age 50, post-trauma. "
                "URGENT: persisting over 72 hours, not responding to OTC medications. "
                "ROUTINE: known migraine, tension headache treat with ibuprofen rest hydration."},
    {"id": "hypertension-001", "title": "Hypertension Management Guidelines", "category": "routine",
     "content": "Blood pressure classification: Normal under 120/80, Stage 1 130-139/80-89, "
                "Stage 2 over 140/90, Hypertensive crisis over 180/120 requires emergency care. "
                "Routine management: DASH diet, low sodium, 150 minutes exercise weekly, "
                "medication adherence, follow-up every 3 months when stable."},
    {"id": "fever-001", "title": "Fever Assessment and Management", "category": "urgent",
     "content": "Emergency: temperature over 40C, fever with stiff neck and rash, confusion, "
                "difficulty breathing, infant under 3 months with any fever. "
                "Management: acetaminophen 500-1000mg every 4-6 hours, ibuprofen with food, rest, hydration."},
    {"id": "general-triage-001", "title": "General Triage Decision Framework", "category": "general",
     "content": "EMERGENCY severity 8-10: cardiac arrest, stroke, anaphylaxis, major trauma. "
                "URGENT severity 5-7: high fever, severe pain, suspected fractures, worsening chronic disease. "
                "ROUTINE severity 1-4: stable chronic disease, minor illness, prescription refills."},
]


def _make_embedding_fn():
    """Create a chromadb-compatible embedding function (no model download)."""
    from chromadb.api.types import EmbeddingFunction, Documents, Embeddings

    class SimpleEmbeddingFn(EmbeddingFunction):
        def __init__(self): pass
        def name(self) -> str: return "simple-sha256-v1"
        def __call__(self, input: Documents) -> Embeddings:
            dim = 64
            out = []
            for text in input:
                seed = hashlib.sha256(str(text).encode()).digest()
                raw = list(seed) * (dim // 32 + 1)
                vec = [(b / 127.5 - 1.0) for b in raw[:dim]]
                norm = sum(v**2 for v in vec) ** 0.5 or 1.0
                out.append([v / norm for v in vec])
            return out
        def build_from_config(self, config): return SimpleEmbeddingFn()
        def get_config(self): return {}

    return SimpleEmbeddingFn()


def seed_knowledge_base(reset: bool = False) -> None:
    try:
        import chromadb
    except ImportError:
        print("Error: pip install chromadb")
        sys.exit(1)

    settings.ensure_dirs()
    persist_dir = str(settings.chroma_persist_dir)
    collection_name = settings.chroma_collection_name

    print(f"\nInitialising ChromaDB at: {persist_dir}")
    client = chromadb.PersistentClient(path=persist_dir)

    if reset:
        try:
            client.delete_collection(collection_name)
            print(f"Deleted collection: {collection_name}")
        except Exception:
            pass

    ef = _make_embedding_fn()
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
        embedding_function=ef,
    )

    existing = collection.count()
    print(f"Existing documents: {existing}")
    print(f"Seeding {len(BUILTIN_DOCUMENTS)} built-in guidelines...")

    ids, docs, metas = [], [], []
    for d in BUILTIN_DOCUMENTS:
        ids.append(d["id"])
        docs.append(d["content"])
        metas.append({"title": d["title"], "category": d["category"], "source": "built-in"})
        print(f"  + [{d['category']:10s}] {d['title']}")

    collection.upsert(ids=ids, documents=docs, metadatas=metas)

    # Load PDFs from data/knowledge/ if present
    knowledge_dir = Path("data/knowledge")
    if knowledge_dir.exists():
        for pdf_path in knowledge_dir.glob("*.pdf"):
            try:
                from pypdf import PdfReader
                text = "\n".join(p.extract_text() or "" for p in PdfReader(str(pdf_path)).pages)
                chunks = [text[i:i+1000] for i in range(0, len(text), 800)]
                for i, chunk in enumerate(chunks):
                    collection.upsert(
                        ids=[f"pdf-{pdf_path.stem}-{i}"],
                        documents=[chunk],
                        metadatas=[{"title": pdf_path.stem, "category": "pdf", "source": str(pdf_path)}],
                    )
                print(f"  + PDF: {pdf_path.name} ({len(chunks)} chunks)")
            except Exception as e:
                print(f"  ! {pdf_path.name}: {e}")

    final = collection.count()
    print(f"\n{'─'*50}")
    print(f"  ✓ Collection : {collection_name}")
    print(f"  ✓ Documents  : {final} total ({final - existing} new)")
    print(f"  ✓ Location   : {persist_dir}")
    print(f"{'─'*50}")

    # Verification query
    print("\nVerification — searching 'chest pain emergency':")
    results = collection.query(query_texts=["chest pain emergency"], n_results=2)
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        print(f"  → [{meta['category']}] {meta['title']}: {doc[:90]}...")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the medical knowledge base")
    parser.add_argument("--reset", action="store_true", help="Delete and recreate collection")
    args = parser.parse_args()
    seed_knowledge_base(reset=args.reset)
