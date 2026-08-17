# Agente de razonamiento cíclico con memoria persistente

Agente desarrollado con Python 3.12, LangGraph y LangChain que utiliza
herramientas de búsqueda sobre documentación técnica, razonamiento
multi-paso y persistencia de estado mediante SQLite.

## Objetivo

El proyecto implementa un agente capaz de:

- decidir autónomamente cuándo utilizar una herramienta;
- ejecutar búsquedas sobre documentación técnica;
- realizar razonamiento multi-paso mediante un ciclo ReAct;
- mantener el estado de una conversación mediante `thread_id`;
- persistir el estado utilizando SQLite;
- ejecutar el flujo de forma asíncrona;
- limitar la cantidad máxima de pasos mediante `recursion_limit`.

## Tecnologías utilizadas

- Python 3.12
- LangGraph
- LangChain
- OpenAI
- Pinecone
- BM25
- SQLite
- aiosqlite
- asyncio

## Arquitectura

El flujo principal del agente se construye utilizando `StateGraph` y
`MessagesState`.

El modelo se encuentra conectado a una herramienta personalizada mediante
`llm.bind_tools()`.

La arquitectura permite que el modelo decida si necesita utilizar una
herramienta:

```text
Usuario
   │
   ▼
Nodo del modelo
   │
   ├── ¿Necesita una herramienta?
   │          │
   │          ├── Sí
   │          ▼
   │     Nodo de herramientas
   │          │
   │          ▼
   │     Resultado de herramienta
   │          │
   │          ▼
   │     Nodo del modelo
   │
   └── No
       │
       ▼
   Respuesta final