"""Tests de la mecánica del grafo con un LLM simulado (sin red ni API key)."""
import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from agente import crear_grafo, ejecutar_consulta
from tests.modelo_falso import ModeloFalso, llamar, tool_results, turno_actual


def politica_listo(msgs):
    t = turno_actual(msgs)
    n = sum(isinstance(m, ToolMessage) for m in t)
    if n == 0:
        return llamar(("consultar_proyecto_localizacion", {"proyecto_id": "129171"}))
    if n == 1:
        return llamar(*[(h, {"proyecto_id": "129171", "idioma": i})
                        for i in ("es-LA", "fr-FR") for h in ("consultar_estado_idioma", "consultar_resultados_qa")])
    return AIMessage(content="es-LA listo; fr-FR no: faltan 4200 palabras y hay 1 error crítico abierto.")


async def test_ciclo_multipaso():
    grafo = crear_grafo(ModeloFalso(politica=politica_listo))
    r = await ejecutar_consulta(grafo, "¿Listo 129171 en es y fr?", "t1", verbose=False)
    assert len(r.llamadas) == 5 and r.llamadas[0][0] == "consultar_proyecto_localizacion"
    assert "fr-FR no" in r.respuesta


def politica_contexto(msgs):
    """Solo sabe de qué proyecto se habla si lo ve en el historial (como haría un LLM real)."""
    historial = [m for m in msgs if isinstance(m, ToolMessage)]
    proyecto = next((r["proyecto_id"] for r in tool_results(historial) if "proyecto_id" in r), None)
    if proyecto is None:
        return AIMessage(content="¿De qué proyecto hablás? Necesito el ID.")
    actual = turno_actual(msgs)
    if not any(isinstance(m, ToolMessage) for m in actual):
        return llamar(("consultar_estado_idioma", {"proyecto_id": proyecto, "idioma": "ja-JP"}))
    return AIMessage(content=f"Proyecto {proyecto}: ja-JP tiene más pendientes.")


async def test_persistencia_y_aislamiento_de_threads(tmp_path):
    db = str(tmp_path / "mem.sqlite")
    def politica(msgs):
        pregunta = turno_actual(msgs)[0].content
        if "idiomas tiene" in pregunta:
            if not any(isinstance(m, ToolMessage) for m in turno_actual(msgs)):
                return llamar(("consultar_proyecto_localizacion", {"proyecto_id": "129171"}))
            return AIMessage(content="es-LA, fr-FR, de-DE y ja-JP.")
        return politica_contexto(msgs)

    modelo = ModeloFalso(politica=politica)
    async with AsyncSqliteSaver.from_conn_string(db) as mem:
        g = crear_grafo(modelo, mem)
        await ejecutar_consulta(g, "¿Qué idiomas tiene 129171?", "A", verbose=False)
        r2 = await ejecutar_consulta(g, "¿Y cuál de ellos tiene más pendientes?", "A", verbose=False)
        assert "129171" in r2.respuesta
        rb = await ejecutar_consulta(g, "¿Y cuál de ellos tiene más pendientes?", "B", verbose=False)
        assert "ID" in rb.respuesta and not rb.llamadas
    # Reabrir la base (simula reiniciar el proceso): el hilo A sigue ahí, el B no mezcló nada.
    async with AsyncSqliteSaver.from_conn_string(db) as mem:
        g = crear_grafo(modelo, mem)
        a = await g.aget_state({"configurable": {"thread_id": "A"}})
        b = await g.aget_state({"configurable": {"thread_id": "B"}})
        assert len(a.values["messages"]) > len(b.values["messages"]) == 2
        assert sum(isinstance(m, HumanMessage) for m in a.values["messages"]) == 2


async def test_recursion_limit_corta_ciclo_infinito():
    siempre = ModeloFalso(politica=lambda m: llamar(("consultar_proyecto_localizacion", {"proyecto_id": "129171"})))
    grafo = crear_grafo(siempre)
    r = await ejecutar_consulta(grafo, "loop", "t", recursion_limit=6, verbose=False)
    assert r.truncado_por_limite and len(r.llamadas) == 3
