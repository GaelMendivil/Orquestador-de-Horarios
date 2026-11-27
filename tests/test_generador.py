"""Pruebas de la fase 2: generador de instancias."""

import pytest

from horarios.dominios import calcular_dominios, diagnosticar_inviabilidad
from horarios.entrada import instancia_desde_dict
from horarios.generador import ParametrosGenerador, generar, ocupacion


def test_misma_semilla_misma_instancia():
    p = ParametrosGenerador(semilla=7, fraccion_disponible=0.6)
    assert generar(p) == generar(p)


def test_semillas_distintas_dan_instancias_distintas():
    a = generar(ParametrosGenerador(semilla=1))
    b = generar(ParametrosGenerador(semilla=2))
    assert a["secciones"] != b["secciones"]


def test_tamanos_y_conteos():
    p = ParametrosGenerador(bloques_curriculares=3, materias_por_bloque=5,
                            sesiones_por_materia=2, secciones_por_profesor=3)
    inst = instancia_desde_dict(generar(p))
    assert len(inst.secciones) == 15
    assert len(inst.eventos) == 30
    assert len(inst.profesores) == 5  # ceil(15 / 3)


@pytest.mark.parametrize("semilla", range(30))
def test_instancias_generadas_cargan_y_no_son_inviables_trivialmente(semilla):
    p = ParametrosGenerador(semilla=semilla, bloques_curriculares=4, salones=3,
                            fraccion_disponible=0.5, secciones_por_profesor=3)
    inst = instancia_desde_dict(generar(p))
    assert diagnosticar_inviabilidad(inst, calcular_dominios(inst)) == []


def test_disponibilidad_respeta_margen_minimo():
    p = ParametrosGenerador(fraccion_disponible=0.05, secciones_por_profesor=3)
    datos = generar(p)
    for prof in datos["profesores"]:
        carga = sum(s["sesiones"] for s in datos["secciones"] if s["profesor"] == prof["id"])
        assert len(prof["disponibles"]) >= carga + 2


def test_ocupacion():
    datos = generar(ParametrosGenerador(bloques_curriculares=2, materias_por_bloque=6,
                                        sesiones_por_materia=2, salones=2))
    assert ocupacion(datos) == pytest.approx(24 / 60)


def test_parametros_invalidos():
    with pytest.raises(ValueError):
        generar(ParametrosGenerador(inscritos_min=50, inscritos_max=10))


def test_agranda_salones_cuando_no_caben_por_capacidad():
    # Semilla 2 producía 36 sesiones con ≥28 inscritos y un solo salón de ese tamaño.
    p = ParametrosGenerador(semilla=2, bloques_curriculares=4, salones=3,
                            fraccion_disponible=0.5, secciones_por_profesor=3)
    inst = instancia_desde_dict(generar(p))
    assert diagnosticar_inviabilidad(inst, calcular_dominios(inst)) == []


def test_error_claro_si_faltan_salones():
    with pytest.raises(ValueError, match="aumenta el número de salones"):
        generar(ParametrosGenerador(bloques_curriculares=10, materias_por_bloque=10, salones=1))
