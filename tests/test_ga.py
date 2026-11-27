"""Pruebas de la fase 4: operadores y motor del GA base."""

import json
import random
from pathlib import Path

import pytest

from horarios.dominios import calcular_dominios
from horarios.entrada import cargar_instancia, instancia_desde_dict
from horarios.evaluacion import Evaluador
from horarios.ga import ConfiguracionGA, InstanciaInviable, ejecutar
from horarios.operadores import (ReparadorPrimerHueco, cruce_por_tramos, inicializar, mutar,
                                 torneo, tramos_de_cruce)
from horarios.validador import validar

INSTANCIAS = Path(__file__).resolve().parent.parent / "instancias"


@pytest.fixture(scope="module")
def icc7():
    return cargar_instancia(INSTANCIAS / "icc7_ficticio.json")


def en_dominio(horario, dominios):
    return all(t in d.bloques and r in d.salones for (t, r), d in zip(horario, dominios))


# --- Operadores ------------------------------------------------------------

def test_tramos_por_bloque_curricular(icc7):
    tramos = tramos_de_cruce(icc7)
    assert [len(t) for t in tramos] == [12, 12]  # 2 grupos × 6 materias × 2 sesiones


def test_tramos_por_seccion_si_hay_un_solo_bloque():
    with open(INSTANCIAS / "icc7_ficticio.json", encoding="utf-8") as f:
        d = json.load(f)
    for s in d["secciones"]:
        s["bloque_curricular"] = "UNICO"
    inst = instancia_desde_dict(d)
    assert [len(t) for t in tramos_de_cruce(inst)] == [2] * 12


def test_cruce_hereda_tramos_completos(icc7):
    tramos = tramos_de_cruce(icc7)
    p1 = [(0, 0)] * 24
    p2 = [(1, 1)] * 24
    rng = random.Random(3)
    for _ in range(20):
        hijo = cruce_por_tramos(p1, p2, tramos, rng)
        for tramo in tramos:
            assert len({hijo[i] for i in tramo}) == 1  # todo el tramo de un mismo padre
    assert p1 == [(0, 0)] * 24  # no modifica a los padres


def test_mutacion_e_inicializacion_respetan_el_dominio(icc7):
    dominios = calcular_dominios(icc7)
    tramos = tramos_de_cruce(icc7)
    rng = random.Random(0)
    h = inicializar(dominios, rng)
    assert en_dominio(h, dominios)
    for _ in range(200):
        h = mutar(h, dominios, tramos, 0.3, rng)
        assert en_dominio(h, dominios)


def test_torneo_elige_menor_clave(icc7):
    ev = Evaluador(icc7)
    dominios = calcular_dominios(icc7)
    rng = random.Random(0)
    pob = [(h, ev.evaluar(h)) for h in (inicializar(dominios, rng) for _ in range(10))]
    mejor = min(pob, key=lambda i: i[1].clave())[0]
    # Con k igual a toda la población es casi seguro que el mejor participe.
    elegidos = [torneo(pob, 60, rng) for _ in range(20)]
    assert all(e == mejor for e in elegidos)


def test_reparacion_reduce_violaciones_y_respeta_dominio(icc7):
    dominios = calcular_dominios(icc7)
    ev = Evaluador(icc7)
    reparar = ReparadorPrimerHueco(icc7, dominios)
    rng = random.Random(0)
    for _ in range(30):
        h = [(rng.choice(d.bloques[:3]), rng.choice(d.salones)) for d in dominios]  # muchos choques
        reparado = reparar(h)
        assert en_dominio(reparado, dominios)
        assert ev.evaluar(reparado).v <= ev.evaluar(h).v
        assert ev.evaluar(reparado).v == validar(icc7, reparado).total
    assert reparar.fallos == 0  # instancia holgada: siempre encuentra hueco


def test_reparacion_primer_hueco_sesga_hacia_el_inicio(icc7):
    """Documenta el sesgo A8 del análisis: lo reparado cae en los primeros bloques."""
    dominios = calcular_dominios(icc7)
    todos_en_lun1 = [(0, d.salones[0]) for d in dominios]
    reparado = ReparadorPrimerHueco(icc7, dominios)(todos_en_lun1)
    assert max(t for t, _ in reparado) < 12  # todo queda en lunes y martes


# --- Motor -----------------------------------------------------------------

@pytest.mark.parametrize("reparacion", ["ninguna", "primer_hueco"])
@pytest.mark.parametrize("archivo", ["ejemplo_minimo.json", "icc7_ficticio.json", "sint_10.json"])
def test_llega_a_horario_factible_certificado(archivo, reparacion):
    inst = cargar_instancia(INSTANCIAS / archivo)
    r = ejecutar(inst, ConfiguracionGA(reparacion=reparacion, semilla=1, max_evaluaciones=20_000))
    assert r.evaluacion.factible
    assert r.reporte.factible  # certificado por el validador independiente


def test_misma_semilla_mismo_resultado(icc7):
    cfg = ConfiguracionGA(semilla=5, max_evaluaciones=2_000, reparacion="ninguna")
    a, b = ejecutar(icc7, cfg), ejecutar(icc7, cfg)
    assert a.mejor == b.mejor
    assert [h.mejor_s for h in a.historial] == [h.mejor_s for h in b.historial]


def test_respeta_presupuesto():
    inst = cargar_instancia(INSTANCIAS / "sint_30.json")
    r = ejecutar(inst, ConfiguracionGA(semilla=0, max_evaluaciones=1_000))
    assert r.evaluaciones <= 1_000
    assert r.motivo_fin == "presupuesto de evaluaciones agotado"


def test_historial_y_callback(icc7):
    vistos = []
    r = ejecutar(icc7, ConfiguracionGA(semilla=2, max_evaluaciones=3_000, reparacion="ninguna"),
                 al_terminar_generacion=vistos.append)
    assert len(vistos) == len(r.historial) - 1  # la generación 0 no llama al callback
    mejores = [(h.mejor_v, h.mejor_s) for h in r.historial]
    assert mejores == sorted(mejores, reverse=True)  # con elitismo, nunca empeora


def test_instancia_inviable_se_rechaza_con_motivo():
    with open(INSTANCIAS / "ejemplo_minimo.json", encoding="utf-8") as f:
        d = json.load(f)
    d["secciones"][3]["inscritos"] = 99
    with pytest.raises(InstanciaInviable, match="ningún salón"):
        ejecutar(instancia_desde_dict(d))


def test_configuracion_invalida():
    with pytest.raises(ValueError):
        ConfiguracionGA(reparacion="magica")
    with pytest.raises(ValueError):
        ConfiguracionGA(elitismo=100, tam_poblacion=100)


# --- Salida ----------------------------------------------------------------

def test_tabla_semanal_y_csv():
    from horarios.salida import horario_csv, opciones_de_vista, tabla_semanal
    inst = cargar_instancia(INSTANCIAS / "ejemplo_minimo.json")
    horario = [(0, 0), (1, 0), (6, 0), (2, 1), (3, 1)]  # horario B del análisis
    t = tabla_semanal(inst, horario, "profesor", "P1")
    assert t["columnas"] == ["Lun", "Mar"] and len(t["filas"]) == 4
    assert t["celdas"][0][0].startswith("Matemáticas (G1)")  # e1 en Lun B1
    assert t["celdas"][2][1].startswith("Programación")      # e3 en Mar B3
    assert opciones_de_vista(inst, "salon") == ["R1", "R2"]
    lineas = horario_csv(inst, horario).strip().splitlines()
    assert len(lineas) == 6 and lineas[0].startswith("carrera,grupo,seccion")


def test_tabla_muestra_empalmes():
    from horarios.salida import tabla_semanal
    inst = cargar_instancia(INSTANCIAS / "ejemplo_minimo.json")
    horario_a = [(0, 0), (3, 0), (4, 0), (0, 1), (1, 1)]  # P1 en dos clases el Lun B1
    t = tabla_semanal(inst, horario_a, "profesor", "P1")
    assert " / " in t["celdas"][0][0]
