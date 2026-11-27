"""Pruebas de la fase 1: modelo, carga de instancias, dominios e inviabilidad."""

import copy
import json
from pathlib import Path

import pytest

from horarios.dominios import calcular_dominios, diagnosticar_inviabilidad
from horarios.entrada import ErrorInstancia, cargar_instancia, instancia_desde_dict

INSTANCIAS = Path(__file__).resolve().parent.parent / "instancias"


@pytest.fixture
def datos_minimos():
    with open(INSTANCIAS / "ejemplo_minimo.json", encoding="utf-8") as f:
        return json.load(f)


# --- Carga -----------------------------------------------------------------

def test_carga_ejemplo_minimo():
    inst = cargar_instancia(INSTANCIAS / "ejemplo_minimo.json")
    assert inst.num_bloques == 8
    assert len(inst.eventos) == 5
    # P1 prefiere los bloques 1-2 de cada día: t = 0, 1 (Lun) y 4, 5 (Mar).
    assert inst.profesores["P1"].preferidos == frozenset({0, 1, 4, 5})
    assert inst.nombre_bloque(5) == "Mar B2"


def test_carga_instancia_ficticia_genera_dos_eventos_por_seccion():
    inst = cargar_instancia(INSTANCIAS / "icc7_ficticio.json")
    assert len(inst.secciones) == 12
    assert len(inst.eventos) == 24
    assert inst.nombre_bloque(0) == "Lun 07:00-08:40"


def test_eventos_ordenados_por_bloque_curricular():
    inst = cargar_instancia(INSTANCIAS / "icc7_ficticio.json")
    bloques = [e.seccion.bloque_curricular for e in inst.eventos]
    assert bloques == sorted(bloques)  # tramos contiguos por bloque curricular
    assert [e.indice for e in inst.eventos] == list(range(24))


def test_rechaza_y_reporta_todos_los_errores(datos_minimos):
    d = copy.deepcopy(datos_minimos)
    d["salones"][0]["capacidad"] = 0                 # capacidad inválida
    d["secciones"][0]["profesor"] = "NO-EXISTE"      # profesor inexistente
    d["secciones"][1]["id"] = d["secciones"][2]["id"]  # id duplicado
    d["profesores"][0]["preferidos"] = ["Dom-9"]     # bloque fuera de rango
    with pytest.raises(ErrorInstancia) as exc:
        instancia_desde_dict(d)
    assert len(exc.value.errores) == 4


def test_rechaza_etiquetas_con_longitud_distinta(datos_minimos):
    d = copy.deepcopy(datos_minimos)
    d["etiquetas_bloques"] = ["7:00"]
    with pytest.raises(ErrorInstancia):
        instancia_desde_dict(d)


# --- Dominios --------------------------------------------------------------

def test_dominio_por_capacidad(datos_minimos):
    inst = instancia_desde_dict(datos_minimos)
    dominios = calcular_dominios(inst)
    por_seccion = {e.seccion.id: d for e, d in zip(inst.eventos, dominios)}
    # G1 (25) cabe en R1 (30) y R2 (45); G2 (40) sólo en R2.
    assert por_seccion["e1"].salones == (0, 1)
    assert por_seccion["e4"].salones == (1,)
    assert len(por_seccion["e1"].bloques) == 8


def test_dominio_por_disponibilidad(datos_minimos):
    d = copy.deepcopy(datos_minimos)
    d["profesores"][1]["disponibles"] = ["Mar-3", "Mar-4"]
    inst = instancia_desde_dict(d)
    dominios = calcular_dominios(inst)
    por_seccion = {e.seccion.id: dom for e, dom in zip(inst.eventos, dominios)}
    assert por_seccion["e2"].bloques == (6, 7)


# --- Inviabilidad ----------------------------------------------------------

def test_instancias_de_ejemplo_no_son_inviables_trivialmente():
    for nombre in ("ejemplo_minimo.json", "icc7_ficticio.json"):
        inst = cargar_instancia(INSTANCIAS / nombre)
        assert diagnosticar_inviabilidad(inst, calcular_dominios(inst)) == []


def _diagnostico(d):
    inst = instancia_desde_dict(d)
    return diagnosticar_inviabilidad(inst, calcular_dominios(inst))


def test_detecta_grupo_que_no_cabe_en_ningun_salon(datos_minimos):
    d = copy.deepcopy(datos_minimos)
    d["secciones"][3]["inscritos"] = 50
    assert any("ningún salón" in p for p in _diagnostico(d))


def test_detecta_profesor_con_mas_sesiones_que_bloques(datos_minimos):
    d = copy.deepcopy(datos_minimos)
    d["profesores"][0]["disponibles"] = ["Lun-1", "Lun-2"]  # P1 tiene 3 sesiones
    assert any("P1 tiene 3 sesiones" in p for p in _diagnostico(d))


def test_detecta_mas_sesiones_que_dias(datos_minimos):
    d = copy.deepcopy(datos_minimos)
    d["secciones"][0]["sesiones"] = 3  # sólo hay 2 días
    assert any("e1 tiene 3 sesiones" in p for p in _diagnostico(d))


def test_detecta_falta_de_salones_grandes(datos_minimos):
    d = copy.deepcopy(datos_minimos)
    # 9 sesiones de G2 (40 inscritos) y sólo R2 × 8 bloques = 8 plazas.
    # Repartidas en varias secciones para no disparar la regla de días.
    d["dias"], d["bloques_por_dia"] = 2, 4
    d["profesores"].append({"id": "P3"})
    for i in range(7):
        d["secciones"].append({"id": f"x{i}", "materia": "X", "profesor": "P3",
                               "inscritos": 40, "sesiones": 1, "bloque_curricular": f"Z{i}"})
    assert any("≥40 inscritos" in p for p in _diagnostico(d))
