"""Base de datos simulada de un sistema interno de gestión de proyectos de localización.

No hay base de datos real: los datos viven en memoria, tipados con dataclasses.
Todos los valores son ficticios pero realistas.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

# "Hoy" fijo para que las demos y los tests sean reproducibles.
FECHA_REFERENCIA: date = date(2026, 10, 5)


@dataclass(frozen=True)
class ProblemaQA:
    id: str
    severidad: str  # "critico" | "mayor" | "menor"
    categoria: str
    descripcion: str
    resuelto: bool


@dataclass(frozen=True)
class IdiomaDestino:
    codigo: str
    nombre: str
    proveedor: str
    palabras_totales: int
    palabras_traducidas: int
    palabras_revisadas: int
    segmentos_totales: int
    segmentos_confirmados: int
    estado_traduccion: str
    estado_revision: str
    fecha_entrega: date
    capacidad_diaria_palabras: int  # ritmo sostenido estimado del proveedor
    qa_ejecutado: bool
    problemas_qa: tuple[ProblemaQA, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Proyecto:
    id: str
    nombre: str
    cliente: str
    idioma_fuente: str
    estado: str
    fecha_entrega_global: date
    archivos: tuple[str, ...]
    idiomas: dict[str, IdiomaDestino]


def _p(id_: str, sev: str, cat: str, desc: str, resuelto: bool) -> ProblemaQA:
    return ProblemaQA(id_, sev, cat, desc, resuelto)


PROYECTOS: dict[str, Proyecto] = {
    "129171": Proyecto(
        id="129171",
        nombre="Manual de usuario e interfaz del robot X500",
        cliente="Northwind Robotics",
        idioma_fuente="en-US",
        estado="En producción",
        fecha_entrega_global=date(2026, 10, 20),
        archivos=("X500_UserManual_v3.2.docx", "X500_GUI_strings.json", "X500_SafetyLabels.xliff"),
        idiomas={
            "es-LA": IdiomaDestino(
                codigo="es-LA", nombre="Español (Latinoamérica)", proveedor="Lingua Norte",
                palabras_totales=48500, palabras_traducidas=48500, palabras_revisadas=48500,
                segmentos_totales=3120, segmentos_confirmados=3120,
                estado_traduccion="Completado", estado_revision="Completado",
                fecha_entrega=date(2026, 10, 9), capacidad_diaria_palabras=6000,
                qa_ejecutado=True,
                problemas_qa=(
                    _p("ES-001", "menor", "Puntuación", "Falta coma antes de 'etc.' en la sección 4.2.", True),
                    _p("ES-002", "menor", "Formato", "Espaciado doble en tabla de especificaciones.", True),
                ),
            ),
            "fr-FR": IdiomaDestino(
                codigo="fr-FR", nombre="Francés (Francia)", proveedor="Atelier Traduction",
                palabras_totales=48500, palabras_traducidas=44300, palabras_revisadas=39800,
                segmentos_totales=3120, segmentos_confirmados=2850,
                estado_traduccion="En curso", estado_revision="En curso",
                fecha_entrega=date(2026, 10, 12), capacidad_diaria_palabras=2500,
                qa_ejecutado=True,
                problemas_qa=(
                    _p("FR-001", "critico", "Terminología", "Botón E-STOP traducido como 'parada final' en lugar de 'arrêt d'urgence' (seguridad).", False),
                    _p("FR-002", "mayor", "Precisión", "Valor de torque omitido en el paso 7 del procedimiento de calibración.", False),
                    _p("FR-003", "mayor", "Consistencia", "'Payload' traducido de tres formas distintas en el manual.", False),
                    _p("FR-004", "mayor", "Formato", "Variables {0} desordenadas en cadena de la GUI.", False),
                    _p("FR-005", "mayor", "Precisión", "Unidad en pulgadas sin convertir a métrico.", True),
                    _p("FR-006", "menor", "Puntuación", "Espacio fino faltante antes de los dos puntos.", False),
                    _p("FR-007", "menor", "Estilo", "Uso inconsistente de 'vous' y 'tu'.", False),
                    _p("FR-008", "menor", "Formato", "Negrita perdida en encabezado 3.1.", False),
                ),
            ),
            "de-DE": IdiomaDestino(
                codigo="de-DE", nombre="Alemán (Alemania)", proveedor="Sprachwerk GmbH",
                palabras_totales=48500, palabras_traducidas=31200, palabras_revisadas=18400,
                segmentos_totales=3120, segmentos_confirmados=2005,
                estado_traduccion="En curso", estado_revision="En curso",
                fecha_entrega=date(2026, 10, 12), capacidad_diaria_palabras=1900,
                qa_ejecutado=True,
                problemas_qa=(
                    _p("DE-001", "mayor", "Terminología", "Glosario del cliente no aplicado a 'end effector'.", False),
                    _p("DE-002", "menor", "Ortografía", "Compuesto escrito con guion en lugar de junto.", False),
                    _p("DE-003", "menor", "Formato", "Comillas rectas en lugar de „tipográficas“.", False),
                ),
            ),
            "ja-JP": IdiomaDestino(
                codigo="ja-JP", nombre="Japonés (Japón)", proveedor="Tokyo Lingo KK",
                palabras_totales=49800, palabras_traducidas=29700, palabras_revisadas=0,
                segmentos_totales=3260, segmentos_confirmados=1860,
                estado_traduccion="En curso", estado_revision="No iniciada",
                fecha_entrega=date(2026, 10, 20), capacidad_diaria_palabras=3000,
                qa_ejecutado=False,
            ),
        },
    ),
    "130045": Proyecto(
        id="130045",
        nombre="Campaña Q4 de la app móvil FitPulse",
        cliente="FitPulse Inc.",
        idioma_fuente="en-US",
        estado="En revisión",
        fecha_entrega_global=date(2026, 10, 14),
        archivos=("FitPulse_Q4_strings.json", "FitPulse_PushNotifications.xlsx"),
        idiomas={
            "es-LA": IdiomaDestino(
                codigo="es-LA", nombre="Español (Latinoamérica)", proveedor="Lingua Norte",
                palabras_totales=9200, palabras_traducidas=9200, palabras_revisadas=9200,
                segmentos_totales=860, segmentos_confirmados=860,
                estado_traduccion="Completado", estado_revision="Completado",
                fecha_entrega=date(2026, 10, 8), capacidad_diaria_palabras=5000,
                qa_ejecutado=True,
            ),
            "it-IT": IdiomaDestino(
                codigo="it-IT", nombre="Italiano (Italia)", proveedor="Parola Studio",
                palabras_totales=9200, palabras_traducidas=9200, palabras_revisadas=7400,
                segmentos_totales=860, segmentos_confirmados=860,
                estado_traduccion="Completado", estado_revision="En curso",
                fecha_entrega=date(2026, 10, 14), capacidad_diaria_palabras=3000,
                qa_ejecutado=True,
                problemas_qa=(_p("IT-001", "mayor", "Precisión", "Notificación push supera el límite de caracteres.", False),),
            ),
        },
    ),
}
