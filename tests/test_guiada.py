"""Pruebas de la reparación guiada (contribución C1)."""

import random
from pathlib import Path

import pytest

from horarios.dominios import calcular_dominios
from horarios.entrada import cargar_instancia
from horarios.evaluacion import Evaluador
from horarios.ga import ConfiguracionGA, ejecutar
from horarios.operadores import ReparadorGuiado, ReparadorPrimerHueco, inicializar
from horarios.validador import validar
from tests.test_caso_real import FOTO, horario_desde

INSTANCIAS = Path(__file__).resolve().parent.parent / "instancias"


@pytest.mark.parametrize("archivo", ["icc7_real.json", "sint_30.json", "sint_100.json"])
def test_quita_los_empalmes_de_horarios_aleatorios(archivo):
    inst = cargar_instancia(INSTANCIAS / archivo)
    dominios = calcular_dominios(inst)
    guiada = ReparadorGuiado(inst, dominios, Evaluador(inst))
    rng = random.Random(3)
    for _ in range(20):
        h = guiada(inicializar(dominios, rng), rng)
        rep = validar(inst, h)
        assert rep.factible or guiada.fallos > 0


def test_no_es_peor_que_primer_hueco_en_lo_blando():
    """Misma población aleatoria reparada de las dos formas: la guiada debe dar menor S en promedio."""
    inst = cargar_instancia(INSTANCIAS / "sint_30.json")
    dominios = calcular_dominios(inst)
    ev = Evaluador(inst)
    guiada, primer = ReparadorGuiado(inst, dominios, ev), ReparadorPrimerHueco(inst, dominios)
    rng = random.Random(5)
    s_g = s_p = 0.0
    for _ in range(30):
        h = inicializar(dominios, rng)
        s_g += ev.evaluar(guiada(h, random.Random(0))).s
        s_p += ev.evaluar(primer(h)).s
    assert s_g < s_p


def test_recoloca_la_clase_sola_de_la_foto():
    """Si se marca Química del viernes 20:00, la guiada la manda a un lugar que no cuesta más."""
    inst = cargar_instancia(INSTANCIAS / "icc7_real_grupo1.json")
    dominios = calcular_dominios(inst)
    ev = Evaluador(inst)
    h = horario_desde(inst, FOTO)
    i = next(e.indice for e in inst.eventos if e.seccion.id == "G1-QUI" and e.numero_sesion == 1)
    nuevo = ReparadorGuiado(inst, dominios, ev)(h, random.Random(0), frozenset({i}))
    antes, despues = ev.evaluar(h), ev.evaluar(nuevo)
    assert despues.v == 0 and despues.s < antes.s
    assert despues.inicio_tarde == 0


def test_ga_guiada_es_reproducible_y_certificada():
    inst = cargar_instancia(INSTANCIAS / "sint_30.json")
    cfg = ConfiguracionGA(reparacion="guiada", semilla=2, max_evaluaciones=1500)
    a, b = ejecutar(inst, cfg), ejecutar(inst, cfg)
    assert a.mejor == b.mejor and a.evaluacion == b.evaluacion
    assert a.reporte.factible == a.evaluacion.factible
