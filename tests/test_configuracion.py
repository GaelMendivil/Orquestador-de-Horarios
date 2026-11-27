"""Pruebas de la configuración en tablas (configuracion.py)."""

import json
from pathlib import Path

import pytest

from horarios.configuracion import (carreras, cargar_configuracion, configuracion_desde_instancia,
                                    construir_instancia, interpretar_franjas, franjas_a_texto)
from horarios.dominios import calcular_dominios, diagnosticar_inviabilidad
from horarios.entrada import ErrorInstancia, instancia_desde_dict

RAIZ = Path(__file__).resolve().parent.parent
HORAS = [(480, 580), (600, 700), (720, 820), (960, 1060), (1080, 1180), (1200, 1300)]
TURNOS = {"matutino": {0, 1, 2}, "vespertino": {3, 4, 5}}


def config_base(**cambios):
    c = cargar_configuracion(RAIZ / "configuraciones" / "icc7_ejemplo.json")
    c.update(cambios)
    return c


def franjas(texto, dias=5):
    return interpretar_franjas(texto, dias, HORAS, TURNOS)


def test_ejemplo_icc_equivale_a_la_instancia_real():
    datos, avisos = construir_instancia(config_base())
    assert avisos == []
    nueva = instancia_desde_dict(datos)
    real = instancia_desde_dict(json.loads((RAIZ / "instancias" / "icc7_real.json").read_text(encoding="utf-8")))
    resumen = lambda i: sorted((s.materia, s.profesor, s.inscritos, s.sesiones, s.turno) for s in i.secciones)
    assert resumen(nueva) == resumen(real)
    assert nueva.bloques_curriculares() == ("ICC 7 G1", "ICC 7 G2")
    assert (nueva.turnos, nueva.etiquetas_bloques) == (real.turnos, real.etiquetas_bloques)
    # "Mismo día" es sólo blando.
    assert not nueva.sesiones_en_dias_distintos
    assert not any(s.permitir_mismo_dia for s in nueva.secciones)


def test_cada_materia_se_abre_para_cada_grupo_y_reparte_profesores():
    c = config_base()
    c["grupos"].append({"Carrera": "ICC", "Semestre": 7, "Grupo": "G3", "Alumnos": 10, "Turno": "vespertino"})
    c["materias"][0]["Profesor"] = "Ana, Luis"
    datos, avisos = construir_instancia(c)
    assert len(datos["secciones"]) == 18
    materia = c["materias"][0]["Materia"]
    profes = [s["profesor"] for s in datos["secciones"] if s["materia"] == materia]
    assert profes == ["Ana", "Luis", "Ana"]
    assert any("no están en Profesores" in a for a in avisos)


def test_filtrar_por_carrera():
    c = cargar_configuracion(RAIZ / "configuraciones" / "cetys_tijuana_aprox.json")
    assert len(carreras(c)) == 22
    datos, _ = construir_instancia(c, ["ICC", "ISW"])
    assert {s["carrera"] for s in datos["secciones"]} == {"ICC", "ISW"}
    # ISW 1.er semestre tiene 35 alumnos: se divide en 2 grupos (18 y 17).
    assert sorted({s["inscritos"] for s in datos["secciones"] if s["carrera"] == "ISW"}) == [17, 18]


def test_cetys_completo_es_viable():
    c = cargar_configuracion(RAIZ / "configuraciones" / "cetys_tijuana_aprox.json")
    inst = instancia_desde_dict(construir_instancia(c)[0])
    assert len(inst.eventos) == 1800
    assert diagnosticar_inviabilidad(inst, calcular_dominios(inst)) == []


def test_errores_con_tabla_y_fila():
    c = config_base()
    c["grupos"][1]["Turno"] = "nocturno"
    c["materias"][2]["Sesiones"] = None
    c["salones"].append({"Salón": "Salón ICC-1", "Edificio": None, "Capacidad": 20})
    with pytest.raises(ErrorInstancia) as exc:
        construir_instancia(c)
    texto = "\n".join(exc.value.errores)
    assert "Grupos, fila 2 (ICC 7 G2): el turno 'nocturno' no existe" in texto
    assert "Materias, fila 3" in texto
    assert "'Salón ICC-1' está repetido" in texto


@pytest.mark.parametrize("texto, esperado", [
    ("", None),
    ("todo", set(range(30))),
    ("vespertino", {d * 6 + b for d in range(5) for b in (3, 4, 5)}),
    ("Lun-Mié 4-6", {d * 6 + b for d in range(3) for b in (3, 4, 5)}),
    ("lun,MIE 1", {0, 12}),
    ("Vie", set(range(24, 30))),
    ("Lun 16:00-20:00; Mar matutino", {3, 4, 6, 7, 8}),
    ("Lunes - Martes 2 , 3", {1, 2, 7, 8}),
])
def test_interpretar_franjas(texto, esperado):
    resultado = franjas(texto)
    assert (resultado if resultado is None else set(resultado)) == esperado


@pytest.mark.parametrize("texto, mensaje", [
    ("tarde", "no entiendo"),
    ("Sáb 1", "no es día de clase"),
    ("Lun 7", "no existe"),
    ("16-22", "16:00-22:00"),
    ("Vie-Lun 1", "al revés"),
    ("15:00-16:30", "ningún bloque"),
])
def test_franjas_invalidas(texto, mensaje):
    with pytest.raises(ValueError, match=mensaje):
        franjas(texto)


def test_franjas_a_texto_ida_y_vuelta():
    for texto in ("Lun 1-3; Mié 2,5", "4-6", "todo"):
        bloques = franjas(texto)
        assert franjas(franjas_a_texto(bloques, 5, 6)) == bloques


def test_instancias_antiguas_se_convierten_a_tablas():
    for nombre in ("icc7_real.json", "sint_30.json"):
        datos = json.loads((RAIZ / "instancias" / nombre).read_text(encoding="utf-8"))
        original = instancia_desde_dict(datos)
        convertida = instancia_desde_dict(construir_instancia(configuracion_desde_instancia(datos))[0])
        clave = lambda i: sorted((s.bloque_curricular, s.materia, s.profesor, s.inscritos, s.sesiones, s.turno)
                                 for s in i.secciones)
        assert clave(convertida) == clave(original)
        assert {p: (v.disponibles, v.preferidos) for p, v in convertida.profesores.items()} == \
               {p: (v.disponibles, v.preferidos) for p, v in original.profesores.items()
                if p in convertida.profesores}


def test_reparacion_evita_mismo_dia_aunque_sea_blando():
    from horarios.dominios import calcular_dominios
    from horarios.evaluacion import Evaluador
    from horarios.operadores import ReparadorPrimerHueco
    inst = instancia_desde_dict(construir_instancia(config_base())[0])
    # Las dos sesiones de cada materia en el mismo día (lunes), en el turno vespertino.
    horario = [(3 + (e.numero_sesion % 3), 0) for e in inst.eventos]
    reparado = ReparadorPrimerHueco(inst, calcular_dominios(inst))(horario)
    ev = Evaluador(inst).evaluar(reparado)
    assert ev.v == 0 and ev.mismo_dia == 0
