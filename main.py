"""Demo del agente de localización: multi-paso, persistencia SQLite y thread_id."""
from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from agente import crear_grafo, crear_modelo, ejecutar_consulta

RUTA_DB = Path("memoria_localizacion.sqlite")


def titulo(texto: str) -> None:
    print(f"\n{'=' * 78}\n{texto}\n{'=' * 78}")


async def main(conservar_db: bool) -> None:
    if not conservar_db and RUTA_DB.exists():
        RUTA_DB.unlink()
    llm = crear_modelo()

    async with AsyncSqliteSaver.from_conn_string(str(RUTA_DB)) as memoria:
        grafo = crear_grafo(llm, memoria)

        titulo("1) Razonamiento multi-paso: ¿listo para entregar en español y francés?")
        await ejecutar_consulta(grafo, "¿Está listo el proyecto 129171 para entregar en español y francés? "
                                       "Si no, indicame qué falta.", thread_id="multipaso-1")

        titulo("2) Multi-paso: más pendientes vs. más atrasado")
        await ejecutar_consulta(grafo, "¿Cuál de los idiomas del proyecto 129171 tiene más palabras pendientes "
                                       "y cuál está más atrasado?", thread_id="multipaso-2")

        titulo("3) Persistencia: mismo thread_id, 'ellos' se refiere al proyecto anterior")
        await ejecutar_consulta(grafo, "¿Qué idiomas están incluidos en el proyecto 129171?", thread_id="sesion-A")
        await ejecutar_consulta(grafo, "¿Y cuál de ellos tiene más palabras pendientes?", thread_id="sesion-A")

        titulo("4) Aislamiento: otro thread_id NO conoce el contexto de sesion-A")
        await ejecutar_consulta(grafo, "¿Y cuál de ellos tiene más palabras pendientes?", thread_id="sesion-B")

        titulo("5) Manejo de error: proyecto inexistente")
        await ejecutar_consulta(grafo, "¿Cómo va el proyecto 999999?", thread_id="sesion-C")

    titulo("6) Persistencia en disco: se reabre SQLite y se recupera sesion-A")
    async with AsyncSqliteSaver.from_conn_string(str(RUTA_DB)) as memoria:
        grafo = crear_grafo(llm, memoria)
        estado = await grafo.aget_state({"configurable": {"thread_id": "sesion-A"}})
        print(f"Mensajes guardados en sesion-A: {len(estado.values['messages'])}")
        await ejecutar_consulta(grafo, "Recordame de qué proyecto veníamos hablando.", thread_id="sesion-A")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--conservar-db", action="store_true", help="No borrar la base SQLite al iniciar.")
    asyncio.run(main(parser.parse_args().conservar_db))
