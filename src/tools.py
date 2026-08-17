from langchain_core.tools import tool

from src.retriever import RAGSystem


# ============================================================
# SISTEMA RAG
# ============================================================

rag_system = RAGSystem()


# ============================================================
# HERRAMIENTA DE BÚSQUEDA
# ============================================================

@tool
def buscar_documentacion_tecnica(query: str) -> str:
    """
    Busca información técnica relevante en la documentación
    del proyecto utilizando recuperación híbrida con Pinecone
    y BM25.

    Usar esta herramienta cuando la pregunta requiera
    información específica de la documentación técnica.
    """

    documents = rag_system.search(query)

    if not documents:
        return "No se encontró información relevante."

    results: list[str] = []

    for i, document in enumerate(documents[:5], start=1):

        source = document.metadata.get(
            "document",
            "desconocido",
        )

        category = document.metadata.get(
            "category",
            "N/A",
        )

        chunk_id = document.metadata.get(
            "chunk_id",
            "N/A",
        )

        results.append(
            f"""
Resultado {i}
Documento: {source}
Categoría: {category}
Chunk: {chunk_id}

Contenido:
{document.page_content}
"""
        )

    return "\n".join(results)