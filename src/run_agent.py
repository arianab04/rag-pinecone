import asyncio
import json
from pathlib import Path

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from src.graph import builder


# ============================================================
# CONFIGURACIÓN
# ============================================================

THREAD_ID = "trace-demo-001"
RECURSION_LIMIT = 10

TRACE_DIR = Path("traces")
TRACE_FILE = TRACE_DIR / "execution_trace.json"


# ============================================================
# EJECUCIÓN
# ============================================================

async def main() -> None:
    """
    Ejecuta una consulta multi-step, muestra la secuencia
    de ejecución y guarda una traza JSON.
    """

    TRACE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    async with AsyncSqliteSaver.from_conn_string(
        "checkpoints.db"
    ) as checkpointer:

        graph = builder.compile(
            checkpointer=checkpointer
        )

        config = {
            "configurable": {
                "thread_id": THREAD_ID
            },
            "recursion_limit": RECURSION_LIMIT,
        }

        question = (
            "Necesito resolver una duda técnica en dos partes. "
            "Primero explicame cómo funcionan las sesiones y "
            "transacciones en SQLAlchemy, incluyendo la diferencia "
            "entre flush y commit. Después explicame qué problema "
            "puede aparecer cuando trabajo con código bloqueante "
            "dentro de asyncio y cómo debería manejarlo. "
            "Utilizá la documentación técnica disponible y "
            "analizá cada tema por separado antes de darme "
            "una conclusión integrada."
        )

        # ====================================================
        # EJECUCIÓN DEL GRAFO
        # ====================================================

        result = await graph.ainvoke(
            {
                "messages": [
                    HumanMessage(
                        content=question
                    )
                ]
            },
            config=config,
        )

        messages = result["messages"]

        # ====================================================
        # CONSTRUIR TRAZA
        # ====================================================

        trace_messages: list[dict] = []

        tool_calls: list[dict] = []
        tool_results: list[dict] = []

        for message in messages:

            if isinstance(message, HumanMessage):

                trace_messages.append(
                    {
                        "type": "human",
                        "content": message.content,
                    }
                )

            elif isinstance(message, AIMessage):

                if message.tool_calls:

                    calls = []

                    for tool_call in message.tool_calls:

                        call_data = {
                            "name": tool_call["name"],
                            "args": tool_call["args"],
                            "id": tool_call["id"],
                        }

                        calls.append(call_data)
                        tool_calls.append(call_data)

                    trace_messages.append(
                        {
                            "type": "ai",
                            "tool_calls": calls,
                        }
                    )

                else:

                    trace_messages.append(
                        {
                            "type": "ai",
                            "content": message.content,
                        }
                    )

            elif isinstance(message, ToolMessage):

                result_data = {
                    "tool_name": message.name,
                    "tool_call_id": message.tool_call_id,
                    "content": message.content,
                }

                tool_results.append(result_data)

                trace_messages.append(
                    {
                        "type": "tool",
                        **result_data,
                    }
                )

        final_answer = messages[-1].content

        trace = {
            "thread_id": THREAD_ID,
            "recursion_limit": RECURSION_LIMIT,
            "tool_call_count": len(tool_calls),
            "tool_result_count": len(tool_results),
            "question": question,
            "messages": trace_messages,
            "final_answer": final_answer,
        }

        # ====================================================
        # GUARDAR JSON
        # ====================================================

        TRACE_FILE.write_text(
            json.dumps(
                trace,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        # ====================================================
        # MOSTRAR RESULTADO
        # ====================================================

        print("\n" + "=" * 80)
        print("TRAZA GENERADA")
        print("=" * 80)

        print(
            f"Archivo: {TRACE_FILE}"
        )

        print(
            f"Llamadas a herramientas: "
            f"{len(tool_calls)}"
        )

        print(
            f"Resultados de herramientas: "
            f"{len(tool_results)}"
        )

        print(
            f"Thread ID: {THREAD_ID}"
        )

        print(
            f"Recursion limit: {RECURSION_LIMIT}"
        )

        print("\n" + "=" * 80)
        print("RESPUESTA FINAL")
        print("=" * 80)

        print(final_answer)


if __name__ == "__main__":
    asyncio.run(main())