"""Chat interactivo con el agente de localización (para preguntar en vivo).

Uso:
    python chat.py                      # sesión nueva con thread_id "demo"
    python chat.py --thread otra        # otra conversación (otra memoria)
Comandos: /thread <nombre> cambia de conversación, /salir termina.
La memoria se guarda en memoria_localizacion.sqlite, así que podés cerrar y volver.
"""
from __future__ import annotations

import argparse
import asyncio

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from agente import crear_grafo, crear_modelo, ejecutar_consulta
from main import RUTA_DB


async def chat(thread_id: str) -> None:
    grafo_llm = crear_modelo()
    async with AsyncSqliteSaver.from_conn_string(str(RUTA_DB)) as memoria:
        grafo = crear_grafo(grafo_llm, memoria)
        print(f"Chat de localización (thread: {thread_id}). Proyectos de ejemplo: 129171 y 130045.")
        print("Escribí tu pregunta, /thread <nombre> para cambiar de conversación, /salir para terminar.")
        while True:
            texto = (await asyncio.to_thread(input, "\nVos> ")).strip()
            if not texto:
                continue
            if texto.lower() in ("/salir", "/exit", "salir"):
                break
            if texto.lower().startswith("/thread "):
                thread_id = texto.split(maxsplit=1)[1]
                print(f"→ Ahora estás en el thread '{thread_id}'.")
                continue
            await ejecutar_consulta(grafo, texto, thread_id=thread_id)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--thread", default="demo", help="thread_id de la conversación")
    asyncio.run(chat(parser.parse_args().thread))
