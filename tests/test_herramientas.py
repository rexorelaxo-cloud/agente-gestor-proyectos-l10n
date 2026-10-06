import json

from herramientas import consultar_estado_idioma, consultar_proyecto_localizacion, consultar_resultados_qa


async def test_proyecto_general():
    d = json.loads(await consultar_proyecto_localizacion.ainvoke({"proyecto_id": "129171"}))
    assert d["cliente"] == "Northwind Robotics"
    assert [i["codigo"] for i in d["idiomas_destino"]] == ["es-LA", "fr-FR", "de-DE", "ja-JP"]


async def test_proyecto_inexistente():
    d = json.loads(await consultar_proyecto_localizacion.ainvoke({"proyecto_id": "999999"}))
    assert "error" in d and "129171" in d["proyectos_disponibles"]


async def test_estado_idioma_alias_y_calculos():
    d = json.loads(await consultar_estado_idioma.ainvoke({"proyecto_id": "129171", "idioma": "alemán"}))
    assert d["idioma"] == "de-DE"
    assert d["palabras_pendientes_traduccion"] == 17300
    assert d["dias_restantes"] == 7 and d["dias_necesarios_para_terminar_traduccion"] == 10
    assert d["atraso_estimado_dias"] == 3 and d["en_riesgo_de_atraso"]


async def test_mas_pendientes_no_es_mas_atrasado():
    ja = json.loads(await consultar_estado_idioma.ainvoke({"proyecto_id": "129171", "idioma": "ja"}))
    assert ja["palabras_pendientes_traduccion"] == 20100 and ja["atraso_estimado_dias"] == 0 and not ja["en_riesgo_de_atraso"]


async def test_idioma_fuera_del_proyecto():
    d = json.loads(await consultar_estado_idioma.ainvoke({"proyecto_id": "129171", "idioma": "it"}))
    assert "error" in d


async def test_qa():
    fr = json.loads(await consultar_resultados_qa.ainvoke({"proyecto_id": "129171", "idioma": "fr"}))
    assert fr["errores_por_severidad"]["critico"]["abiertos"] == 1
    assert fr["errores_por_severidad"]["mayor"] == {"total": 4, "abiertos": 3}
    ja = json.loads(await consultar_resultados_qa.ainvoke({"proyecto_id": "129171", "idioma": "ja"}))
    assert ja["qa_ejecutado"] is False
