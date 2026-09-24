import os
from pathlib import Path
import streamlit as st

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


# Page configuration
st.set_page_config(page_title="Nimbus Docs AI Assistant", page_icon="🤖")
st.title("🤖 Nimbus Docs Q&A Assistant")
st.caption("A grounded RAG demo powered by Google Gemini & LangChain")

# Sidebar for API Key configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input(
        "Enter Google Gemini API Key:",
        type="password",
        value=os.getenv("GEMINI_API_KEY", ""),
        help="Get a free key from Google AI Studio",
    )
    st.markdown(
        "[Get a free Gemini API key](https://aistudio.google.com/)"
    )


@st.cache_resource(show_spinner="Indexing documentation into vector store...")
def get_vectorstore(api_key: str):
    
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-2", google_api_key=api_key
    )

    # Load markdown documents directly from the data directory
    docs = []
    data_path = Path(__file__).parent / "data"
    for file_path in sorted(data_path.glob("*.md")):
        text = file_path.read_text(encoding="utf-8")
        docs.append(Document(page_content=text, metadata={"source": file_path.name}))

    # Split documents into overlapping semantic chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=80,
        separators=["\n## ", "\n\n", "\n", " ", ""],
    )
    splits = text_splitter.split_documents(docs)

    # Create an in-memory Chroma vector store
    vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings)
    return vectorstore


# Halt execution until the user provides an API key
if not api_key:
    st.info("👈 Please enter your Gemini API key in the sidebar to get started.", icon="🔑")
    st.stop()

# Initialize retriever and generation chain
vectorstore = get_vectorstore(api_key)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

llm = ChatGoogleGenerativeAI(
    model="models/gemini-3.6-flash", google_api_key=api_key, temperature=0
)

system_prompt = """You answer questions about Nimbus using ONLY the context below.
If the answer isn't in the context, say so plainly — never guess or use outside knowledge.
Be concise and factual.

Context:
{context}"""

prompt = ChatPromptTemplate.from_messages(
    [("system", system_prompt), ("human", "{question}")]
)

rag_chain = prompt | llm | StrOutputParser()

# Initialize session state for conversation history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Render chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sources" in msg and msg["sources"]:
            st.caption(f"📚 Sources: {', '.join(msg['sources'])}")

# Handle new user input
if user_question := st.chat_input("Ask a question about Nimbus..."):
    # Display user query
    st.session_state.messages.append({"role": "user", "content": user_question})
    with st.chat_message("user"):
        st.markdown(user_question)

    # Retrieve context and generate answer
    with st.chat_message("assistant"):
        with st.spinner("Searching docs and generating answer..."):
            retrieved_docs = retriever.invoke(user_question)
            context = "\n\n".join(
                f"[{doc.metadata.get('source', 'unknown')}]: {doc.page_content}"
                for doc in retrieved_docs
            )
            sources = sorted(
                {doc.metadata.get("source", "unknown") for doc in retrieved_docs}
            )

            response = rag_chain.invoke(
                {"context": context, "question": user_question}
            )

            st.markdown(response)
            if sources:
                st.caption(f"📚 Sources: {', '.join(sources)}")

            # Persist response in session history
            st.session_state.messages.append(
                {"role": "assistant", "content": response, "sources": sources}
            )