"""Pruebas de turnos, excepción a H6 y el caso real de ICC 7.º semestre."""

import copy
import json
from pathlib import Path

import pytest

from horarios.dominios import calcular_dominios, diagnosticar_inviabilidad
from horarios.entrada import ErrorInstancia, cargar_instancia, instancia_desde_dict
from horarios.evaluacion import Evaluador
from horarios.ga import ConfiguracionGA, ejecutar
from horarios.modelo import NOMBRES_DIAS
from horarios.validador import validar

INSTANCIAS = Path(__file__).resolve().parent.parent / "instancias"


@pytest.fixture
def datos_real():
    return json.loads((INSTANCIAS / "icc7_real.json").read_text(encoding="utf-8"))


def horario_actual_grupo1(inst):
    act = json.loads((INSTANCIAS / "icc7_real_grupo1_horario_actual.json").read_text(encoding="utf-8"))
    h = []
    for e in inst.eventos:
        dia, bloque = act["sesiones"][e.seccion.id][e.numero_sesion].split("-")
        h.append((NOMBRES_DIAS.index(dia) * inst.bloques_por_dia + int(bloque) - 1, 0))
    return h


def test_turno_restringe_el_dominio(datos_real):
    inst = instancia_desde_dict(datos_real)
    for dom in calcular_dominios(inst):
        assert {inst.bloque_de(t) for t in dom.bloques} == {3, 4, 5}  # 16:00, 18:00, 20:00


def test_turno_inexistente_es_error(datos_real):
    d = copy.deepcopy(datos_real)
    d["secciones"][0]["turno"] = "nocturno"
    with pytest.raises(ErrorInstancia, match="nocturno"):
        instancia_desde_dict(d)


def test_turno_demasiado_corto_es_inviable(datos_real):
    d = copy.deepcopy(datos_real)
    d["turnos"]["vespertino"] = [4, 5]  # 10 bloques en la semana para 12 sesiones por grupo
    inst = instancia_desde_dict(d)
    assert any("bloques utilizables" in p for p in diagnosticar_inviabilidad(inst, calcular_dominios(inst)))


def _sin_excepcion(nombre):
    d = json.loads((INSTANCIAS / nombre).read_text(encoding="utf-8"))
    for s in d["secciones"]:
        s.pop("permitir_mismo_dia", None)
    return d


def test_sin_la_excepcion_el_horario_actual_viola_dias_distintos():
    inst = instancia_desde_dict(_sin_excepcion("icc7_real_grupo1.json"))
    h = horario_actual_grupo1(inst)
    ev, rep = Evaluador(inst).evaluar(h), validar(inst, h)
    assert (ev.v_salon, ev.v_profesor, ev.v_curricular, ev.v_dias) == (0, 0, 0, 1)
    assert ev.huecos == 0 and ev.exceso_diario == 0 and ev.mismo_dia == 0
    assert rep.dias == 1 and "G1-PIV" in rep.mensajes[0]


def test_con_la_excepcion_es_valido_con_penalizacion_blanda():
    inst = cargar_instancia(INSTANCIAS / "icc7_real_grupo1.json")
    h = horario_actual_grupo1(inst)
    ev = Evaluador(inst).evaluar(h)
    assert ev.v == 0 and validar(inst, h).factible
    assert ev.mismo_dia == 1
    assert ev.faltante_diario == 0 and ev.inicio_tarde == 0  # reparto 3, 2, 3, 2, 2
    # Costo = w_dia · 1; Z = 1·U1 + 1·U3a + 3·U3b + 0.1·U4 + 3·U5 = 5 + 9 + 3·8 + 0.1 + 3·5
    # (pesos sin normalizar; la normalización se cancela). U1 = 5 días × (3 bloques del
    # turno − 2); U3a = 9 de exceso; U3b = 4 días × 2 faltantes; U5 = 5 días.
    assert ev.s == pytest.approx(0.1 / 53.1)

def test_mismo_dia_cuesta_una_decima_de_hora_muerta():
    """Los pesos son costo por ocurrencia: juntar el viernes cuesta 0.1 horas muertas."""
    inst = cargar_instancia(INSTANCIAS / "icc7_real_grupo1.json")
    ev = Evaluador(inst)
    assert ev.pesos["mismo_dia"] / ev.pesos["huecos"] == pytest.approx(0.1)
    assert ev.u_huecos == 5  # cota ajustada al turno vespertino

def test_regla_global_desactivada_pasa_todo_a_blanda():
    d = _sin_excepcion("icc7_real_grupo1.json")
    d["sesiones_en_dias_distintos"] = False
    inst = instancia_desde_dict(d)
    h = horario_actual_grupo1(inst)
    assert validar(inst, h).factible
    assert Evaluador(inst).evaluar(h).mismo_dia == 1


@pytest.mark.parametrize("reparacion", ["ninguna", "primer_hueco"])
def test_ga_resuelve_el_caso_real(reparacion):
    inst = cargar_instancia(INSTANCIAS / "icc7_real.json")
    r = ejecutar(inst, ConfiguracionGA(semilla=1, reparacion=reparacion))
    assert r.reporte.factible
    assert all(inst.bloque_de(t) >= 3 for t, _ in r.mejor)  # todo en turno vespertino


def test_tabla_oculta_bloques_fuera_del_turno():
    from horarios.salida import tabla_semanal
    inst = cargar_instancia(INSTANCIAS / "icc7_real_grupo1.json")
    t = tabla_semanal(inst, horario_actual_grupo1(inst), "bloque_curricular", "ICC7-G1")
    assert t["filas"] == ["16:00-17:40", "18:00-19:40", "20:00-21:40"]
    assert t["celdas"][0][0].startswith("Cómputo Evolutivo")  # lunes 16:00


def test_tabla_de_un_grupo_muestra_solo_su_turno():
    from horarios.configuracion import cargar_configuracion, construir_instancia
    from horarios.salida import tabla_semanal
    c = cargar_configuracion(Path(__file__).resolve().parent.parent / "configuraciones" / "cetys_tijuana_aprox.json")
    inst = instancia_desde_dict(construir_instancia(c, ["ICC"])[0])
    horario = [(0, 0)] * len(inst.eventos)
    assert tabla_semanal(inst, horario, "bloque_curricular", "ICC 1 A")["filas"][0] == "08:00-09:40"
    assert tabla_semanal(inst, horario, "bloque_curricular", "ICC 7 G1")["filas"][0] == "16:00-17:40"


# Horario de la foto: reparto 3, 3, 2, 3, 1 y el
# viernes una sola clase (Química) a las 20:00. "Movido": la 2.ª sesión de Procesamiento
# de Imágenes pasa del jueves 20:00 al viernes 16:00 y Química a las 18:00 (reparto 3, 3, 2, 2, 2).
FOTO = {"G1-CE": ["Lun-4", "Mié-4"], "G1-ADM": ["Lun-5", "Jue-4"], "G1-ETI": ["Lun-6", "Jue-5"],
        "G1-NUB": ["Mar-4", "Mié-5"], "G1-PIV": ["Mar-5", "Jue-6"], "G1-QUI": ["Mar-6", "Vie-6"]}


def horario_desde(inst, sesiones):
    h = []
    for e in inst.eventos:
        dia, bloque = sesiones[e.seccion.id][e.numero_sesion].split("-")
        h.append((NOMBRES_DIAS.index(dia) * inst.bloques_por_dia + int(bloque) - 1, 0))
    return h


def test_foto_inicio_tarde_y_dia_vacio():
    inst = cargar_instancia(INSTANCIAS / "icc7_real_grupo1.json")
    ev = Evaluador(inst).evaluar(horario_desde(inst, FOTO))
    assert ev.v == 0 and ev.huecos == 0 and ev.exceso_diario == 0
    assert ev.inicio_tarde == 1   # viernes, sólo Química a las 20:00
    assert ev.faltante_diario == 1    # viernes con 1 clase y piso(12/5) = 2


def test_foto_con_la_clase_movida_queda_en_cero():
    inst = cargar_instancia(INSTANCIAS / "icc7_real_grupo1.json")
    # El viernes debe empezar a las 16:00, así que Química pasa a las 18:00.
    movido = dict(FOTO, **{"G1-PIV": ["Mar-5", "Vie-4"], "G1-QUI": ["Mar-6", "Vie-5"]})
    ev = Evaluador(inst).evaluar(horario_desde(inst, movido))
    assert ev.v == 0 and ev.huecos == 0 and ev.exceso_diario == 0
    assert ev.inicio_tarde == 0 and ev.faltante_diario == 0 and ev.s == 0


@pytest.mark.parametrize("dia_bloque, castigo", [("Vie-4", 0), ("Vie-5", 1), ("Vie-6", 1)])
def test_clase_sola_solo_en_el_primer_bloque_no_se_castiga(dia_bloque, castigo):
    inst = cargar_instancia(INSTANCIAS / "icc7_real_grupo1.json")
    sesiones = dict(FOTO, **{"G1-QUI": ["Mar-6", dia_bloque]})
    assert Evaluador(inst).evaluar(horario_desde(inst, sesiones)).inicio_tarde == castigo


def test_clase_sola_y_reparto_contra_conteo_directo():
    """P3 y P5 recontados de otra forma (por evento, sin las tablas del evaluador)."""
    import random
    inst = cargar_instancia(INSTANCIAS / "icc7_real.json")
    ev = Evaluador(inst)
    dominios = calcular_dominios(inst)
    rng = random.Random(7)
    for _ in range(200):
        h = [(rng.choice(d.bloques), rng.choice(d.salones)) for d in dominios]
        exceso = faltante = sola = 0
        for g in inst.bloques_curriculares():
            mios = [t for (t, _), e in zip(h, inst.eventos) if e.seccion.bloque_curricular == g]
            techo, piso = -(-len(mios) // inst.dias), len(mios) // inst.dias
            for d in range(inst.dias):
                del_dia = sorted({inst.bloque_de(t) for t in mios if inst.dia_de(t) == d})
                n = sum(1 for t in mios if inst.dia_de(t) == d)
                exceso += max(0, n - techo)
                faltante += max(0, piso - n)
                # Turno vespertino = bloques 3, 4, 5: todo día con clase debe empezar en el 3.
                sola += n >= 1 and del_dia[0] != 3
        r = ev.evaluar(h)
        assert (r.exceso_diario, r.faltante_diario, r.inicio_tarde) == (exceso, faltante, sola)
