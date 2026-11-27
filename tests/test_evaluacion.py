"""Pruebas de la fase 3: evaluador y validador independiente."""

import random
from pathlib import Path

import pytest

from horarios.dominios import calcular_dominios
from horarios.entrada import cargar_instancia
from horarios.evaluacion import Evaluador
from horarios.validador import validar

INSTANCIAS = Path(__file__).resolve().parent.parent / "instancias"

# Ejemplo A/B del análisis inicial.
# t: Lun-1=0, Lun-2=1, Lun-3=2, Lun-4=3, Mar-1=4, Mar-3=6. Salones: R1=0, R2=1.
# Orden de eventos: e1, e2, e3 (G1), e4, e5 (G2).
HORARIO_A = [(0, 0), (3, 0), (4, 0), (0, 1), (1, 1)]
HORARIO_B = [(0, 0), (1, 0), (6, 0), (2, 1), (3, 1)]


# Pesos del ejemplo del análisis (antes de existir la carga diaria).
PESOS_ANALISIS = {"huecos": 0.5, "preferencias": 0.5, "carga_diaria": 0.0, "pocas_clases": 0.0, "mismo_dia": 0.0,
                  "inicio_tarde": 0.0}


@pytest.fixture(scope="module")
def minimo():
    return cargar_instancia(INSTANCIAS / "ejemplo_minimo.json")


def test_horario_a_calculado_a_mano(minimo):
    ev = Evaluador(minimo, PESOS_ANALISIS).evaluar(HORARIO_A)
    assert (ev.v_salon, ev.v_profesor, ev.v_curricular, ev.v_dias) == (0, 1, 0, 0)
    assert ev.huecos == 2            # G1 el lunes ocupa los bloques 1 y 4
    assert ev.fuera_preferencia == 0
    # Z = 0.5·U1 + 0.5·U2 = 0.5·8 + 0.5·3 = 5.5
    assert ev.s == pytest.approx(0.5 * 2 / 5.5)


def test_horario_b_calculado_a_mano(minimo):
    ev = Evaluador(minimo, PESOS_ANALISIS).evaluar(HORARIO_B)
    assert ev.v == 0 and ev.factible
    assert ev.huecos == 0
    assert ev.fuera_preferencia == 2  # e3 (Mar-3) y e4 (Lun-3)
    # U2 = 3: sólo cuentan las sesiones de profesores con preferencias (P1).
    assert ev.s == pytest.approx(0.5 * 2 / 5.5)


def test_lexicografico_prefiere_el_factible(minimo):
    evaluador = Evaluador(minimo, PESOS_ANALISIS)
    a, b = evaluador.evaluar(HORARIO_A), evaluador.evaluar(HORARIO_B)
    assert a.s <= b.s                # A es al menos igual de cómodo...
    assert b.clave() < a.clave()     # ...pero B gana porque A tiene un empalme


def test_exceso_cuenta_movimientos_minimos(minimo):
    # Tres sesiones en R2 el Lun-1: 2 sobran (no 3 pares).
    h = [(0, 1), (0, 1), (0, 1), (1, 1), (2, 1)]
    ev = Evaluador(minimo).evaluar(h)
    assert ev.v_salon == 2


def test_dos_sesiones_mismo_dia():
    inst = cargar_instancia(INSTANCIAS / "icc7_ficticio.json")
    h = [(4 * e.indice % 30, 0) for e in inst.eventos]
    h[1] = (h[0][0] + 1, 0)  # 2.ª sesión de la primera sección, mismo día
    ev = Evaluador(inst).evaluar(h)
    assert ev.v_dias >= 1
    assert validar(inst, h).dias == ev.v_dias


def test_pesos_se_normalizan_y_se_validan(minimo):
    pesos = Evaluador(minimo, {"huecos": 3, "preferencias": 1, "carga_diaria": 0, "pocas_clases": 0, "mismo_dia": 0,
                               "inicio_tarde": 0}).pesos
    assert pesos == {"huecos": 0.75, "preferencias": 0.25, "carga_diaria": 0.0, "pocas_clases": 0.0, "mismo_dia": 0.0,
                     "inicio_tarde": 0.0}
    with pytest.raises(ValueError):
        Evaluador(minimo, {"huecos": 1})
    with pytest.raises(ValueError):
        Evaluador(minimo, {"huecos": 0, "preferencias": 0, "carga_diaria": 0, "pocas_clases": 0, "mismo_dia": 0,
                           "inicio_tarde": 0})


def test_contador_de_evaluaciones(minimo):
    evaluador = Evaluador(minimo)
    evaluador.evaluar(HORARIO_A)
    evaluador.evaluar(HORARIO_B)
    assert evaluador.evaluaciones == 2


def test_validador_mensajes(minimo):
    rep = validar(minimo, HORARIO_A)
    assert not rep.factible and rep.profesor == 1
    assert any("P1 tiene" in m for m in rep.mensajes)
    assert validar(minimo, HORARIO_B).factible


def test_validador_detecta_capacidad_y_longitud(minimo):
    h = list(HORARIO_B)
    h[3] = (2, 0)  # G2 (40) en R1 (30)
    assert validar(minimo, h).capacidad == 1
    assert not validar(minimo, h[:-1]).factible


@pytest.mark.parametrize("archivo", ["icc7_ficticio.json", "sint_30.json", "sint_100.json"])
def test_evaluador_y_validador_coinciden_en_horarios_aleatorios(archivo):
    inst = cargar_instancia(INSTANCIAS / archivo)
    dominios = calcular_dominios(inst)
    evaluador = Evaluador(inst)
    rng = random.Random(0)
    for _ in range(50):
        # Aleatorio dentro del dominio, concentrado en pocos bloques para
        # provocar muchos choques de todos los tipos.
        h = [(rng.choice(d.bloques[:8]), rng.choice(d.salones)) for d in dominios]
        ev, rep = evaluador.evaluar(h), validar(inst, h)
        assert (ev.v_salon, ev.v_profesor, ev.v_curricular, ev.v_dias) == \
               (rep.salon, rep.profesor, rep.curricular, rep.dias)
        assert rep.capacidad == rep.disponibilidad == 0  # dentro del dominio
        assert ev.factible == rep.factible


def test_carga_diaria():
    inst = cargar_instancia(INSTANCIAS / "icc7_ficticio.json")
    ev = Evaluador(inst)
    # 12 sesiones por grupo y 5 días: techo 3 y piso 2 por día.
    # Peor caso por grupo: 12 el mismo día = 9 de exceso y 4 días × 2 faltantes.
    assert ev.u_carga == 18 and ev.u_pocas == 16
    # Grupo A: 6 sesiones el lunes y 6 el martes (exceso 3 + 3).
    a = [(t, 0) for t in range(12)]
    # Grupo B: 3 sesiones por día de martes a viernes (exceso 0).
    b = [(6 * d + k, 1) for d in (1, 2, 3, 4) for k in (3, 4, 5)]
    r = ev.evaluar(a + b)
    assert r.exceso_diario == 6
    # A: miércoles, jueves y viernes vacíos (2 + 2 + 2); B: lunes vacío (2).
    assert r.faltante_diario == 8
