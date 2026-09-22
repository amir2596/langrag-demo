"""
Reads every .md file in data/, splits it into overlapping chunks, embeds
each chunk with a local Ollama embedding model, and persists the result
to a local Chroma vector store on disk.

Run this once before starting app.py:
    python ingest.py
"""

import pathlib

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

DATA_DIR = pathlib.Path(__file__).parent / "data"
PERSIST_DIR = pathlib.Path(__file__).parent / "chroma_db"
EMBEDDING_MODEL = "bge-m3"
OLLAMA_BASE_URL = "http://localhost:11434"


def load_documents() -> list[dict]:
    """Loads each markdown file as one raw document, tagged with its
    filename as a source — this is what lets the API's answer cite
    which file backed it, which matters more for a real client demo
    than it might seem: "trust me" answers are worth less than
    "here's exactly where this came from" answers."""
    docs = []
    for path in sorted(DATA_DIR.glob("*.md")):
        docs.append({"text": path.read_text(encoding="utf-8"), "source": path.name})
    return docs


def main() -> None:
    raw_docs = load_documents()
    print(f"Loaded {len(raw_docs)} source documents from {DATA_DIR}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=80,
        separators=["\n## ", "\n\n", "\n", " ", ""],
    )

    texts: list[str] = []
    metadatas: list[dict] = []
    for doc in raw_docs:
        chunks = splitter.split_text(doc["text"])
        texts.extend(chunks)
        metadatas.extend({"source": doc["source"]} for _ in chunks)

    print(f"Split into {len(texts)} chunks")

    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=OLLAMA_BASE_URL)

    # from_texts embeds every chunk and persists the resulting vector
    # store to PERSIST_DIR automatically (Chroma's newer client
    # persists on write — no separate .persist() call needed).
    Chroma.from_texts(
        texts=texts,
        embedding=embeddings,
        metadatas=metadatas,
        persist_directory=str(PERSIST_DIR),
        collection_name="nimbus_docs",
    )

    print(f"Embedded and persisted to {PERSIST_DIR}")


if __name__ == "__main__":
    main()
