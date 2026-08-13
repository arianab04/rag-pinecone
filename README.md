# Sistema RAG escalable en la nube con Pinecone

Sistema de Recuperación Aumentada por Generación (RAG) implementado en Python utilizando Pinecone Serverless, embeddings de OpenAI y recuperación híbrida mediante búsqueda vectorial y BM25.

El proyecto implementa un pipeline completo de ingesta, recuperación y evaluación de documentos técnicos.

---

## 1. Objetivo

El objetivo del proyecto es construir un módulo de recuperación escalable en la nube capaz de:

- procesar documentos en formato Markdown;
- dividirlos en chunks;
- generar embeddings utilizando OpenAI;
- almacenar los vectores en Pinecone Serverless;
- realizar búsquedas semánticas mediante similitud vectorial;
- realizar búsquedas léxicas mediante BM25;
- combinar ambos métodos mediante un recuperador híbrido;
- evaluar la calidad de recuperación mediante Precision@5 y Recall@5.

---

## 2. Arquitectura

El flujo general del sistema es:

```text
Documentos Markdown
        |
        v
Carga de documentos
        |
        v
RecursiveCharacterTextSplitter
        |
        v
Chunks
        |
        v
OpenAI Embeddings
text-embedding-3-small
        |
        v
Vectores de 1536 dimensiones
        |
        v
Pinecone Serverless
        |
        +----------------------+
        |                      |
        v                      v
Búsqueda vectorial          BM25
        |                      |
        +----------+-----------+
                   |
                   v
           EnsembleRetriever
                   |
                   v
              Top-5
                   |
                   v
             Evaluación
        Precision@5 / Recall@5