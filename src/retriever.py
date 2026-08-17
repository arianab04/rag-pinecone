import os
from pathlib import Path

from dotenv import load_dotenv
from pinecone import Pinecone

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever


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

def load_chunks() -> list[Document]:
    """Carga los documentos Markdown y los divide en chunks."""

    documents: list[Document] = []

    for file_path in DOCUMENTS_DIR.glob("*.md"):
        text = file_path.read_text(encoding="utf-8")

        document = Document(
            page_content=text,
            metadata={
                "source": file_path.name,
                "document": file_path.stem,
            },
        )

        documents.append(document)

    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=700,
        chunk_overlap=100,
    )

    chunks = text_splitter.split_documents(documents)

    return chunks


# ============================================================
# RETRIEVER DE PINECONE
# ============================================================

class PineconeRetriever(BaseRetriever):
    """Retriever que realiza búsquedas vectoriales en Pinecone."""

    index: object
    embeddings: object
    k: int = 5

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
    ) -> list[Document]:

        query_vector = self.embeddings.embed_query(query)

        results = self.index.query(
            vector=query_vector,
            top_k=self.k,
            include_metadata=True,
        )

        documents: list[Document] = []

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
                },
            )

            documents.append(document)

        return documents


# ============================================================
# SISTEMA RAG
# ============================================================

class RAGSystem:
    """
    Sistema de recuperación híbrida que combina Pinecone y BM25.

    La lógica de recuperación queda encapsulada dentro de esta clase
    para evitar exponer los retrievers a nivel de módulo.
    """

    def __init__(
        self,
        documents_dir: Path = DOCUMENTS_DIR,
        k: int = 5,
    ) -> None:

        self.documents_dir = documents_dir
        self.k = k

        # ----------------------------------------------------
        # Validación de configuración
        # ----------------------------------------------------

        if not PINECONE_API_KEY:
            raise ValueError(
                "No se encontró PINECONE_API_KEY en las variables de entorno."
            )

        if not INDEX_NAME:
            raise ValueError(
                "No se encontró INDEX_NAME en las variables de entorno."
            )

        # ----------------------------------------------------
        # Pinecone
        # ----------------------------------------------------

        self.pc = Pinecone(
            api_key=PINECONE_API_KEY
        )

        self.index = self.pc.Index(INDEX_NAME)

        print("Conectado a Pinecone")

        # ----------------------------------------------------
        # Embeddings
        # ----------------------------------------------------

        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small"
        )

        print("Modelo de embeddings listo")

        # ----------------------------------------------------
        # Chunks para BM25
        # ----------------------------------------------------

        self.chunks = load_chunks()

        print(
            f"Chunks cargados para BM25: {len(self.chunks)}"
        )

        # ----------------------------------------------------
        # BM25
        # ----------------------------------------------------

        self.bm25_retriever = BM25Retriever.from_documents(
            self.chunks
        )

        self.bm25_retriever.k = self.k

        # ----------------------------------------------------
        # Pinecone Retriever
        # ----------------------------------------------------

        self.pinecone_retriever = PineconeRetriever(
            index=self.index,
            embeddings=self.embeddings,
            k=self.k,
        )

        # ----------------------------------------------------
        # Ensemble Retriever
        # ----------------------------------------------------

        self.ensemble_retriever = EnsembleRetriever(
            retrievers=[
                self.pinecone_retriever,
                self.bm25_retriever,
            ],
            weights=[
                0.5,
                0.5,
            ],
        )

    # ========================================================
    # BÚSQUEDA HÍBRIDA
    # ========================================================

    def search(self, query: str) -> list[Document]:
        """
        Ejecuta una búsqueda híbrida utilizando Pinecone y BM25.

        Args:
            query: Pregunta o consulta técnica.

        Returns:
            Lista de documentos relevantes.
        """

        if not query.strip():
            raise ValueError(
                "La consulta no puede estar vacía."
            )

        return self.ensemble_retriever.invoke(query)


# ============================================================
# PRUEBA MANUAL
# ============================================================

if __name__ == "__main__":

    rag_system = RAGSystem()

    query = "¿Qué es un DataFrame en pandas?"

    print("\n" + "=" * 80)
    print(f"PREGUNTA: {query}")
    print("=" * 80)

    results = rag_system.search(query)

    print("\n" + "=" * 80)
    print("RESULTADOS ENSEMBLE")
    print("=" * 80)

    for i, document in enumerate(
        results[:5],
        start=1,
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