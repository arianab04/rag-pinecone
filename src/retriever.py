import os
from pathlib import Path

from dotenv import load_dotenv
from pinecone import Pinecone

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.retrievers import BM25Retriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun


# ============================================================
# CONFIGURACIÓN
# ============================================================

load_dotenv()

DOCUMENTS_DIR = Path("data/documents")

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("INDEX_NAME")


# ============================================================
# CARGAR DOCUMENTOS Y CHUNKS
# ============================================================

def load_chunks():

    documents = []

    for file_path in DOCUMENTS_DIR.glob("*.md"):

        text = file_path.read_text(
            encoding="utf-8"
        )

        document = Document(
            page_content=text,
            metadata={
                "source": file_path.name,
                "document": file_path.stem,
            }
        )

        documents.append(document)

    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=700,
        chunk_overlap=100
    )

    chunks = text_splitter.split_documents(documents)

    return chunks


# ============================================================
# RETRIEVER DE PINECONE
# ============================================================

class PineconeRetriever(BaseRetriever):

    index: object
    embeddings: object
    k: int = 5

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun
    ):

        # Convertir la pregunta en embedding
        query_vector = self.embeddings.embed_query(query)

        # Buscar en Pinecone
        results = self.index.query(
            vector=query_vector,
            top_k=self.k,
            include_metadata=True
        )

        documents = []

        for match in results["matches"]:

            metadata = match["metadata"]

            document = Document(
                page_content=metadata["text"],
                metadata={
                    "source": metadata["source"],
                    "document": metadata["document"],
                    "category": metadata["category"],
                    "chunk_id": metadata["chunk_id"],
                    "score": match["score"],
                }
            )

            documents.append(document)

        return documents


# ============================================================
# CONECTAR CON PINECONE
# ============================================================

pc = Pinecone(
    api_key=PINECONE_API_KEY
)

index = pc.Index(INDEX_NAME)

print("Conectado a Pinecone")


# ============================================================
# EMBEDDINGS
# ============================================================

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small"
)

print("Modelo de embeddings listo")


# ============================================================
# CARGAR CHUNKS
# ============================================================

chunks = load_chunks()

print(
    f"Chunks cargados para BM25: {len(chunks)}"
)


# ============================================================
# BM25
# ============================================================

bm25_retriever = BM25Retriever.from_documents(
    chunks
)

bm25_retriever.k = 5


# ============================================================
# PINECONE RETRIEVER
# ============================================================

pinecone_retriever = PineconeRetriever(
    index=index,
    embeddings=embeddings,
    k=5
)


# ============================================================
# ENSEMBLE RETRIEVER
# ============================================================

from langchain_classic.retrievers import EnsembleRetriever


ensemble_retriever = EnsembleRetriever(
    retrievers=[
        pinecone_retriever,
        bm25_retriever
    ],
    weights=[
        0.5,
        0.5
    ]
)


# ============================================================
# CONSULTA
# ============================================================

query = "¿Qué es un DataFrame en pandas?"

print("\n" + "=" * 80)
print(f"PREGUNTA: {query}")
print("=" * 80)


# ============================================================
# RESULTADOS ENSEMBLE
# ============================================================

results = ensemble_retriever.invoke(query)


print("\n" + "=" * 80)
print("RESULTADOS ENSEMBLE")
print("=" * 80)


for i, document in enumerate(
    results[:5],
    start=1
):

    print(
        f"\n{i}. Documento: "
        f"{document.metadata['document']}"
    )

    print(
        f"   Categoría: "
        f"{document.metadata.get('category', 'N/A')}"
    )

    print(
        f"   Chunk: "
        f"{document.metadata.get('chunk_id', 'N/A')}"
    )

    print(
        f"   Texto: "
        f"{document.page_content[:500]}"
    )

    print("-" * 80)