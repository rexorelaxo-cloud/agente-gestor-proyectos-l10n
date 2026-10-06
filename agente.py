"""Agente de gestión de proyectos de localización con LangGraph.

Ciclo:  START → modelo ──(¿tool_calls?)──► herramientas ──► modelo → ... → END
La decisión de qué herramienta llamar (y cuándo parar) la toma el LLM vía tool calling;
el grafo solo enruta según si el último AIMessage trae tool_calls.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.errors import GraphRecursionError
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from dotenv import load_dotenv

from herramientas import HERRAMIENTAS

load_dotenv()  # lee claves desde .env (si existe); nunca van en el código

RECURSION_LIMIT_POR_DEFECTO: int = 15  # ≈ 7 vueltas modelo→herramienta→modelo

PROMPT_SISTEMA: str = """Sos un asistente interno de una empresa de localización. Ayudás a project managers \
a consultar el estado de proyectos de localización usando las herramientas disponibles.

Reglas:
- Respondé siempre con datos obtenidos de las herramientas; nunca inventes cifras.
- Si la pregunta involucra varios idiomas, consultá cada idioma por separado.
- Para comparar o rankear idiomas de un proyecto (más pendientes, más atrasado, etc.), primero consultá el proyecto \
para obtener la lista de idiomas destino y después consultá el estado de TODOS ellos, sin saltearte ninguno. \
El idioma fuente nunca es un idioma destino.
- Si una herramienta devuelve un error, corregí los argumentos (usá la lista de idiomas que devuelve el error) y reintentá.
- Si falta el ID del proyecto y no se puede deducir de la conversación, pedilo.
- Un idioma está LISTO PARA ENTREGAR solo si: traducción al 100 %, revisión al 100 % y \
QA ejecutado sin errores críticos ni mayores abiertos (los menores abiertos no bloquean, pero mencionalos).
- "Más atrasado" se mide por los días de atraso estimado, no por el volumen de palabras pendientes.
- Si algo no está listo, indicá concretamente qué falta.
- Respondé en español rioplatense, de forma breve y clara."""


def crear_modelo(nombre: str | None = None) -> BaseChatModel:
    """Crea el LLM real.

    Orden: argumento > variable MODELO_LLM (formato 'proveedor:modelo') > según la API key
    disponible (OPENAI_API_KEY → gpt-4o, si no Anthropic).
    """
    from langchain.chat_models import init_chat_model

    if nombre is None:
        nombre = os.getenv("MODELO_LLM")
    if nombre is None:
        nombre = "openai:gpt-4o" if os.getenv("OPENAI_API_KEY") else "anthropic:claude-sonnet-5-5"
    return init_chat_model(nombre)


def crear_grafo(llm: BaseChatModel, checkpointer: BaseCheckpointSaver | None = None) -> CompiledStateGraph:
    """Construye y compila el StateGraph (estado = MessagesState)."""
    llm_con_herramientas = llm.bind_tools(HERRAMIENTAS)

    async def nodo_modelo(state: MessagesState) -> dict[str, list[BaseMessage]]:
        respuesta = await llm_con_herramientas.ainvoke([SystemMessage(PROMPT_SISTEMA), *state["messages"]])
        return {"messages": [respuesta]}

    constructor = StateGraph(MessagesState)
    constructor.add_node("modelo", nodo_modelo)
    constructor.add_node("herramientas", ToolNode(HERRAMIENTAS))
    constructor.add_edge(START, "modelo")
    constructor.add_conditional_edges("modelo", tools_condition, {"tools": "herramientas", END: END})
    constructor.add_edge("herramientas", "modelo")  # el ciclo
    return constructor.compile(checkpointer=checkpointer)


@dataclass
class ResultadoConsulta:
    respuesta: str
    llamadas: list[tuple[str, dict[str, Any]]] = field(default_factory=list)
    truncado_por_limite: bool = False


def _resumir(texto: str, maximo: int = 110) -> str:
    plano = " ".join(texto.split())
    return plano if len(plano) <= maximo else plano[:maximo] + "…"


async def ejecutar_consulta(
    grafo: CompiledStateGraph,
    pregunta: str,
    thread_id: str,
    recursion_limit: int = RECURSION_LIMIT_POR_DEFECTO,
    verbose: bool = True,
) -> ResultadoConsulta:
    """Ejecuta una consulta en un thread, imprimiendo la traza paso a paso."""
    config: dict[str, Any] = {"configurable": {"thread_id": thread_id}, "recursion_limit": recursion_limit}
    resultado = ResultadoConsulta(respuesta="")
    salida = print if verbose else (lambda *_a, **_k: None)
    salida(f"\n[thread={thread_id}] Usuario: {pregunta}")
    paso = 0
    try:
        async for actualizacion in grafo.astream(
            {"messages": [HumanMessage(pregunta)]}, config, stream_mode="updates"
        ):
            for nodo, cambios in actualizacion.items():
                for msg in cambios["messages"]:
                    paso += 1
                    if isinstance(msg, AIMessage) and msg.tool_calls:
                        for tc in msg.tool_calls:
                            resultado.llamadas.append((tc["name"], tc["args"]))
                            salida(f"  {paso:>2}. [modelo]       → pide {tc['name']}({tc['args']})")
                    elif isinstance(msg, ToolMessage):
                        salida(f"  {paso:>2}. [herramientas] ← {msg.name}: {_resumir(str(msg.content))}")
                    elif isinstance(msg, AIMessage):
                        texto = msg.text if hasattr(msg, "text") else str(msg.content)
                        resultado.respuesta = str(texto)
                        salida(f"  {paso:>2}. [modelo]       final")
    except GraphRecursionError:
        resultado.truncado_por_limite = True
        resultado.respuesta = (f"Se alcanzó el límite de {recursion_limit} pasos sin llegar a una respuesta final.")
        salida(f"  !! recursion_limit={recursion_limit} alcanzado; se corta el ciclo.")
    salida(f"[thread={thread_id}] Agente: {resultado.respuesta}")
    return resultado
