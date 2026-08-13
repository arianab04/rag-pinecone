import json
import sys
from pathlib import Path


# ============================================================
# CONFIGURACIÓN DE RUTAS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(
    0,
    str(PROJECT_ROOT)
)


# ============================================================
# IMPORTAR RETRIEVERS
# ============================================================

from src.retriever import (
    pinecone_retriever,
    bm25_retriever,
    ensemble_retriever
)


# ============================================================
# GOLDEN SET
# ============================================================

GOLDEN_SET_PATH = (
    PROJECT_ROOT
    / "evaluation"
    / "golden_set.json"
)


with open(
    GOLDEN_SET_PATH,
    "r",
    encoding="utf-8"
) as file:

    golden_set = json.load(file)


print(
    f"Preguntas cargadas: {len(golden_set)}"
)


# ============================================================
# ELIMINAR DOCUMENTOS DUPLICADOS
# ============================================================

def unique_documents(documents):

    seen = set()
    unique = []

    for document in documents:

        if document not in seen:

            seen.add(document)
            unique.append(document)

    return unique


# ============================================================
# PRECISION@5
# ============================================================

def precision_at_5(
    retrieved_documents,
    relevant_documents
):

    retrieved = retrieved_documents[:5]

    relevant_retrieved = sum(
        1
        for document in retrieved
        if document in relevant_documents
    )

    return relevant_retrieved / 5


# ============================================================
# RECALL@5
# ============================================================

def recall_at_5(
    retrieved_documents,
    relevant_documents
):

    retrieved = retrieved_documents[:5]

    relevant_retrieved = sum(
        1
        for document in retrieved
        if document in relevant_documents
    )

    return (
        relevant_retrieved
        / len(relevant_documents)
    )


# ============================================================
# EVALUAR UN RETRIEVER
# ============================================================

def evaluate_retriever(
    retriever,
    retriever_name
):

    total_precision = 0
    total_recall = 0

    print("\n")
    print("=" * 80)
    print(f"EVALUANDO: {retriever_name}")
    print("=" * 80)

    for item in golden_set:

        question_id = item["id"]
        question = item["pregunta"]

        relevant_documents = set(
            item["documentos_relevantes"]
        )

        # Ejecutar retriever
        retrieved_docs = retriever.invoke(
            question
        )

        # Obtener documentos
        retrieved_documents = [
            doc.metadata.get("document")
            for doc in retrieved_docs
        ]

        # Eliminar chunks duplicados
        retrieved_documents = unique_documents(
            retrieved_documents
        )

        # Calcular métricas
        precision = precision_at_5(
            retrieved_documents,
            relevant_documents
        )

        recall = recall_at_5(
            retrieved_documents,
            relevant_documents
        )

        total_precision += precision
        total_recall += recall

        print(
            f"\n{question_id} | "
            f"Precision@5: {precision:.2f} | "
            f"Recall@5: {recall:.2f}"
        )

        print(
            f"  Esperados: "
            f"{sorted(relevant_documents)}"
        )

        print(
            f"  Recuperados: "
            f"{retrieved_documents[:5]}"
        )

    # Promedios
    mean_precision = (
        total_precision
        / len(golden_set)
    )

    mean_recall = (
        total_recall
        / len(golden_set)
    )

    print("\n" + "-" * 80)

    print(
        f"Precision@5 promedio: "
        f"{mean_precision:.3f}"
    )

    print(
        f"Recall@5 promedio: "
        f"{mean_recall:.3f}"
    )

    return (
        mean_precision,
        mean_recall
    )


# ============================================================
# EVALUAR LOS TRES MÉTODOS
# ============================================================

vector_precision, vector_recall = evaluate_retriever(
    pinecone_retriever,
    "VECTOR SEARCH - PINECONE"
)


bm25_precision, bm25_recall = evaluate_retriever(
    bm25_retriever,
    "BM25"
)


ensemble_precision, ensemble_recall = evaluate_retriever(
    ensemble_retriever,
    "ENSEMBLE"
)


# ============================================================
# TABLA FINAL
# ============================================================

print("\n\n")
print("=" * 80)
print("COMPARACIÓN FINAL")
print("=" * 80)

print(
    f"\n{'Retriever':<25}"
    f"{'Precision@5':>15}"
    f"{'Recall@5':>15}"
)

print("-" * 55)

print(
    f"{'Vector Search':<25}"
    f"{vector_precision:>15.3f}"
    f"{vector_recall:>15.3f}"
)

print(
    f"{'BM25':<25}"
    f"{bm25_precision:>15.3f}"
    f"{bm25_recall:>15.3f}"
)

print(
    f"{'Ensemble':<25}"
    f"{ensemble_precision:>15.3f}"
    f"{ensemble_recall:>15.3f}"
)