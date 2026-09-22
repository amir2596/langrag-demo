"""
A small FastAPI service that answers questions about the sample Nimbus
docs, grounded in retrieval — the same RAG pattern as ScopeSense, just
in the Python/LangChain stack most Upwork AI-agent job posts ask for.

Run:
    python ingest.py   # once, to build the vector store
    uvicorn app:app --reload

Then:
    curl -X POST http://localhost:8000/ask \
        -H "Content-Type: application/json" \
        -d '{"question": "How many automations can I have on the Team plan?"}'
"""

import pathlib

from fastapi import FastAPI
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama, OllamaEmbeddings
from pydantic import BaseModel

PERSIST_DIR = pathlib.Path(__file__).parent / "chroma_db"
EMBEDDING_MODEL = "bge-m3"
CHAT_MODEL = "qwen2.5:7b-instruct"
OLLAMA_BASE_URL = "http://localhost:11434"

SYSTEM_PROMPT = """You answer questions about Nimbus using ONLY the context below.
If the answer isn't in the context, say so plainly — never guess or use
outside knowledge. Be concise. When you use a fact from the context,
you don't need to cite it inline; sources are returned separately.

Context:
{context}"""

app = FastAPI(title="Nimbus Docs RAG Demo")

# Loaded once at startup, not per-request — same reasoning as
# ScopeSense's model warm-up: pay setup cost once, not per request.
_embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=OLLAMA_BASE_URL)
_vectorstore = Chroma(
    persist_directory=str(PERSIST_DIR),
    embedding_function=_embeddings,
    collection_name="nimbus_docs",
)
_retriever = _vectorstore.as_retriever(search_kwargs={"k": 3})

_llm = ChatOllama(model=CHAT_MODEL, base_url=OLLAMA_BASE_URL, temperature=0)
_prompt = ChatPromptTemplate.from_messages(
    [("system", SYSTEM_PROMPT), ("human", "{question}")]
)
_generation_chain = _prompt | _llm | StrOutputParser()


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str
    sources: list[str]


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    # Retrieval and generation are separate steps on purpose: this is
    # what lets the response include exactly which source files backed
    # the answer, rather than just trusting the model to have used
    # them faithfully.
    retrieved_docs = _retriever.invoke(req.question)
    context = "\n\n".join(
        f"[{doc.metadata.get('source', 'unknown')}]: {doc.page_content}"
        for doc in retrieved_docs
    )
    sources = sorted({doc.metadata.get("source", "unknown") for doc in retrieved_docs})

    answer = _generation_chain.invoke({"context": context, "question": req.question})

    return AskResponse(answer=answer, sources=sources)
