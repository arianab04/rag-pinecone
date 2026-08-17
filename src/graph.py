from langchain_openai import ChatOpenAI
from langgraph.graph import START, END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from src.tools import buscar_documentacion_tecnica


# ============================================================
# MODELO
# ============================================================

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
)


# ============================================================
# HERRAMIENTAS
# ============================================================

tools = [
    buscar_documentacion_tecnica,
]


# ============================================================
# MODELO CON HERRAMIENTAS
# ============================================================

llm_with_tools = llm.bind_tools(tools)


# ============================================================
# NODO DEL AGENTE
# ============================================================

def agent_node(state: MessagesState) -> dict:
    """
    Ejecuta el LLM sobre el historial actual de mensajes.
    """

    response = llm_with_tools.invoke(
        state["messages"]
    )

    return {
        "messages": [response]
    }


# ============================================================
# CONSTRUCCIÓN DEL GRAFO
# ============================================================

builder = StateGraph(MessagesState)

builder.add_node(
    "agent",
    agent_node,
)

builder.add_node(
    "tools",
    ToolNode(tools),
)


# ============================================================
# EDGES
# ============================================================

builder.add_edge(
    START,
    "agent",
)

builder.add_conditional_edges(
    "agent",
    tools_condition,
)

builder.add_edge(
    "tools",
    "agent",
)