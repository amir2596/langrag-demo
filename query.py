"""
Quick terminal testing without needing curl or the API running.
Run: python query.py
Then type questions, one per line. Ctrl+C to quit.
"""

from app import _generation_chain, _retriever


def answer(question: str) -> tuple[str, list[str]]:
    docs = _retriever.invoke(question)
    context = "\n\n".join(
        f"[{d.metadata.get('source', 'unknown')}]: {d.page_content}" for d in docs
    )
    sources = sorted({d.metadata.get("source", "unknown") for d in docs})
    return _generation_chain.invoke({"context": context, "question": question}), sources


def main() -> None:
    print("Nimbus docs Q&A — ask anything, Ctrl+C to quit.\n")
    try:
        while True:
            question = input("> ").strip()
            if not question:
                continue
            reply, sources = answer(question)
            print(f"\n{reply}\n(sources: {', '.join(sources)})\n")
    except KeyboardInterrupt:
        print("\nbye")


if __name__ == "__main__":
    main()
