"""Herramientas (tools) que el LLM puede invocar mediante tool calling.

Cada una simula una operación contra el sistema interno de gestión de proyectos
de localización. Devuelven JSON (str) y nunca lanzan excepciones por datos
inexistentes: devuelven un objeto con "error" para que el LLM pueda reaccionar.
"""
from __future__ import annotations

import json
import math
import unicodedata
from typing import Any

from langchain_core.tools import tool

from datos_simulados import FECHA_REFERENCIA, PROYECTOS, IdiomaDestino, Proyecto

_ALIAS_IDIOMAS: dict[str, str] = {
    "espanol": "es", "spanish": "es", "castellano": "es",
    "frances": "fr", "french": "fr",
    "aleman": "de", "german": "de",
    "japones": "ja", "japanese": "ja",
    "italiano": "it", "italian": "it",
}


def _sin_acentos(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


def _json(datos: dict[str, Any]) -> str:
    return json.dumps(datos, ensure_ascii=False, indent=2)


def _buscar_proyecto(proyecto_id: str) -> Proyecto | None:
    return PROYECTOS.get(str(proyecto_id).strip())


def _resolver_idioma(proyecto: Proyecto, texto: str) -> IdiomaDestino | None:
    """Acepta 'fr-FR', 'fr', 'francés', 'French', etc."""
    clave = _sin_acentos(texto)
    for codigo, idioma in proyecto.idiomas.items():
        if clave == codigo.lower():
            return idioma
    prefijo = _ALIAS_IDIOMAS.get(clave, clave.split("-")[0])
    for codigo, idioma in proyecto.idiomas.items():
        if codigo.lower().startswith(prefijo):
            return idioma
    return None


def _error_proyecto(proyecto_id: str) -> str:
    return _json({"error": f"Proyecto '{proyecto_id}' no encontrado.",
                  "proyectos_disponibles": sorted(PROYECTOS)})


def _error_idioma(proyecto: Proyecto, idioma: str) -> str:
    return _json({"error": f"El idioma '{idioma}' no está incluido en el proyecto {proyecto.id}.",
                  "idiomas_del_proyecto": list(proyecto.idiomas)})


@tool
async def consultar_proyecto_localizacion(proyecto_id: str) -> str:
    """Consulta la información GENERAL de un proyecto de localización: nombre, cliente,
    idioma fuente, estado, fecha de entrega global, archivos, avance global y la lista
    de idiomas destino con su estado resumido. NO incluye palabras pendientes por idioma
    ni errores de QA: para eso usar consultar_estado_idioma y consultar_resultados_qa.

    Args:
        proyecto_id: ID numérico del proyecto, por ejemplo "129171".
    """
    p = _buscar_proyecto(proyecto_id)
    if p is None:
        return _error_proyecto(proyecto_id)
    total = sum(i.palabras_totales for i in p.idiomas.values())
    traducidas = sum(i.palabras_traducidas for i in p.idiomas.values())
    return _json({
        "proyecto_id": p.id,
        "nombre": p.nombre,
        "cliente": p.cliente,
        "idioma_fuente": p.idioma_fuente,
        "estado": p.estado,
        "fecha_entrega_global": p.fecha_entrega_global.isoformat(),
        "archivos": list(p.archivos),
        "avance_global_traduccion_pct": round(100 * traducidas / total, 1),
        "idiomas_destino": [
            {"codigo": i.codigo, "nombre": i.nombre, "proveedor": i.proveedor,
             "estado_traduccion": i.estado_traduccion, "estado_revision": i.estado_revision,
             "fecha_entrega": i.fecha_entrega.isoformat()}
            for i in p.idiomas.values()
        ],
    })


@tool
async def consultar_estado_idioma(proyecto_id: str, idioma: str) -> str:
    """Consulta el estado DETALLADO de UN idioma destino de un proyecto: palabras totales,
    traducidas, revisadas y pendientes, segmentos, porcentajes de avance, proveedor,
    fecha de entrega, días restantes y estimación de atraso según el ritmo del proveedor.
    Hay que llamarla una vez por cada idioma que se necesite analizar.

    Args:
        proyecto_id: ID del proyecto, por ejemplo "129171".
        idioma: código o nombre del idioma, por ejemplo "fr-FR", "fr" o "francés".
    """
    p = _buscar_proyecto(proyecto_id)
    if p is None:
        return _error_proyecto(proyecto_id)
    i = _resolver_idioma(p, idioma)
    if i is None:
        return _error_idioma(p, idioma)
    pendientes = i.palabras_totales - i.palabras_traducidas
    dias_restantes = (i.fecha_entrega - FECHA_REFERENCIA).days
    dias_necesarios = math.ceil(pendientes / i.capacidad_diaria_palabras) if pendientes else 0
    atraso = max(0, dias_necesarios - dias_restantes)
    return _json({
        "proyecto_id": p.id,
        "idioma": i.codigo,
        "nombre_idioma": i.nombre,
        "proveedor": i.proveedor,
        "palabras_totales": i.palabras_totales,
        "palabras_traducidas": i.palabras_traducidas,
        "palabras_pendientes_traduccion": pendientes,
        "palabras_revisadas": i.palabras_revisadas,
        "palabras_pendientes_revision": i.palabras_totales - i.palabras_revisadas,
        "avance_traduccion_pct": round(100 * i.palabras_traducidas / i.palabras_totales, 1),
        "avance_revision_pct": round(100 * i.palabras_revisadas / i.palabras_totales, 1),
        "segmentos_confirmados": f"{i.segmentos_confirmados}/{i.segmentos_totales}",
        "estado_traduccion": i.estado_traduccion,
        "estado_revision": i.estado_revision,
        "fecha_entrega": i.fecha_entrega.isoformat(),
        "fecha_consulta": FECHA_REFERENCIA.isoformat(),
        "dias_restantes": dias_restantes,
        "capacidad_diaria_proveedor_palabras": i.capacidad_diaria_palabras,
        "dias_necesarios_para_terminar_traduccion": dias_necesarios,
        "atraso_estimado_dias": atraso,
        "en_riesgo_de_atraso": atraso > 0,
    })


@tool
async def consultar_resultados_qa(proyecto_id: str, idioma: str) -> str:
    """Consulta los resultados de QA lingüístico de UN idioma destino: cantidad de errores
    por severidad (crítico / mayor / menor), cuántos siguen abiertos y el detalle de los
    errores abiertos. Si el QA todavía no se ejecutó para ese idioma, lo indica.

    Args:
        proyecto_id: ID del proyecto, por ejemplo "129171".
        idioma: código o nombre del idioma, por ejemplo "es-LA", "es" o "español".
    """
    p = _buscar_proyecto(proyecto_id)
    if p is None:
        return _error_proyecto(proyecto_id)
    i = _resolver_idioma(p, idioma)
    if i is None:
        return _error_idioma(p, idioma)
    if not i.qa_ejecutado:
        return _json({"proyecto_id": p.id, "idioma": i.codigo, "qa_ejecutado": False,
                      "mensaje": "El QA todavía no se ejecutó para este idioma."})
    resumen: dict[str, dict[str, int]] = {}
    for sev in ("critico", "mayor", "menor"):
        de_sev = [x for x in i.problemas_qa if x.severidad == sev]
        resumen[sev] = {"total": len(de_sev), "abiertos": sum(1 for x in de_sev if not x.resuelto)}
    return _json({
        "proyecto_id": p.id,
        "idioma": i.codigo,
        "qa_ejecutado": True,
        "errores_por_severidad": resumen,
        "errores_abiertos_detalle": [
            {"id": x.id, "severidad": x.severidad, "categoria": x.categoria, "descripcion": x.descripcion}
            for x in i.problemas_qa if not x.resuelto
        ],
    })


HERRAMIENTAS = [consultar_proyecto_localizacion, consultar_estado_idioma, consultar_resultados_qa]
