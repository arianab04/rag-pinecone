import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from src.tools import buscar_documentacion_tecnica


# ============================================================
# CONFIGURACIÓN
# ============================================================

load_dotenv()


# ============================================================
# MODELO
# ============================================================

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
)


# ============================================================
# MODELO CON HERRAMIENTAS
# ============================================================

llm_with_tools = llm.bind_tools(
    [buscar_documentacion_tecnica]
)


# ============================================================
# PRUEBA
# ============================================================

if __name__ == "__main__":

    question = (
        "¿Qué es un DataFrame en pandas? "
        "Respondé utilizando la documentación técnica disponible."
    )

    response = llm_with_tools.invoke(
        question
    )

    print("\n" + "=" * 80)
    print("RESPUESTA DEL MODELO")
    print("=" * 80)

    print(response.content)

    print("\n" + "=" * 80)
    print("TOOL CALLS")
    print("=" * 80)

    print(response.tool_calls)