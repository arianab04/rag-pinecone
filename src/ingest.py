import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from pinecone import Pinecone


# Cargar variables del archivo .env
load_dotenv()


# Configuración
DOCUMENTS_DIR = Path("data/documents")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("INDEX_NAME")


# Categorías de nuestros documentos
CATEGORIES = {
    "asyncio_concurrencia": "concurrency",
    "fastapi_dependencias": "web",
    "pandas_dataframes": "data_analysis",
    "pydantic_validacion": "validation",
    "pytest_fixtures": "testing",
    "sqlalchemy_sesiones": "database",
}


def load_documents():
    documents = []

    for file_path in DOCUMENTS_DIR.glob("*.md"):

        text = file_path.read_text(encoding="utf-8")

        document = Document(
            page_content=text,
            metadata={
                "source": file_path.name,
                "document": file_path.stem,
                "category": CATEGORIES.get(
                    file_path.stem,
                    "other"
                ),
            }
        )

        documents.append(document)

    return documents


if __name__ == "__main__":

    # --------------------------------------------------
    # 1. CARGAR DOCUMENTOS
    # --------------------------------------------------

    documents = load_documents()

    print(f"Documentos encontrados: {len(documents)}")


    # --------------------------------------------------
    # 2. CREAR CHUNKS
    # --------------------------------------------------

    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=700,
        chunk_overlap=100
    )

    chunks = text_splitter.split_documents(documents)

    print(f"Chunks generados: {len(chunks)}")


    # --------------------------------------------------
    # 3. CREAR EMBEDDINGS
    # --------------------------------------------------

    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small"
    )

    texts = [
        chunk.page_content
        for chunk in chunks
    ]

    vectors = embeddings.embed_documents(texts)

    print(f"Embeddings generados: {len(vectors)}")
    print(
        f"Dimensión de cada vector: {len(vectors[0])}"
    )


    # --------------------------------------------------
    # 4. CONECTAR CON PINECONE
    # --------------------------------------------------

    pc = Pinecone(
        api_key=PINECONE_API_KEY
    )

    index = pc.Index(INDEX_NAME)


    # --------------------------------------------------
    # 5. PREPARAR REGISTROS
    # --------------------------------------------------

    records = []

    for i, (chunk, vector) in enumerate(
        zip(chunks, vectors)
    ):

        record = {
            "id": f"chunk-{i + 1:03d}",
            "values": vector,
            "metadata": {
                **chunk.metadata,
                "chunk_id": f"chunk-{i + 1:03d}",
                "text": chunk.page_content,
            },
        }

        records.append(record)


    # --------------------------------------------------
    # 6. SUBIR A PINECONE
    # --------------------------------------------------

    index.upsert(
        vectors=records
    )

    print(
        f"\nVectores subidos a Pinecone: {len(records)}"
    )