"""Pruebas de la plantilla de Excel (refleja las tablas de la app)."""

from pathlib import Path

import pytest
from openpyxl import load_workbook

from horarios.configuracion import cargar_configuracion, construir_instancia
from horarios.entrada import ErrorInstancia
from horarios.entrada_excel import crear_plantilla, leer_excel

CONFIGS = Path(__file__).resolve().parent.parent / "configuraciones"


@pytest.fixture
def plantilla(tmp_path):
    config = cargar_configuracion(CONFIGS / "icc7_ejemplo.json")
    ruta = tmp_path / "plantilla.xlsx"
    crear_plantilla(config, ruta)
    return config, ruta


def test_hojas_y_columnas_iguales_a_la_app(plantilla):
    _, ruta = plantilla
    wb = load_workbook(ruta)
    assert wb.sheetnames == ["Cómo llenar", "General", "Bloques", "Salones", "Profesores", "Grupos", "Materias"]
    assert [c.value for c in wb["Grupos"][1]] == ["Carrera", "Semestre", "Grupo", "Alumnos", "Turno"]


def test_ida_y_vuelta_conserva_la_configuracion(plantilla):
    config, ruta = plantilla
    leido = leer_excel(ruta)
    for tabla in ("bloques", "salones", "profesores", "grupos", "materias"):
        assert leido[tabla] == config[tabla], tabla
    assert construir_instancia(leido)[0] == construir_instancia(config)[0]


def test_cetys_ida_y_vuelta(tmp_path):
    config = cargar_configuracion(CONFIGS / "cetys_tijuana_aprox.json")
    crear_plantilla(config, tmp_path / "c.xlsx")
    assert construir_instancia(leer_excel(tmp_path / "c.xlsx"))[0] == construir_instancia(config)[0]


def test_disponibilidad_escrita_a_mano(plantilla):
    _, ruta = plantilla
    wb = load_workbook(ruta)
    wb["Profesores"]["B2"] = "Lun-Mié vespertino; Vie 18:00-22:00"
    wb.save(ruta)
    datos, _ = construir_instancia(leer_excel(ruta))
    prof = next(p for p in datos["profesores"] if p["id"] == "Dra. Elena Ruiz")
    assert prof["disponibles"] == ["Lun-4", "Lun-5", "Lun-6", "Mar-4", "Mar-5", "Mar-6",
                                   "Mié-4", "Mié-5", "Mié-6", "Vie-5", "Vie-6"]


def test_errores_de_captura_se_reportan_juntos(plantilla):
    _, ruta = plantilla
    wb = load_workbook(ruta)
    wb["Profesores"]["B2"] = "tarde"
    wb["Salones"]["C2"] = 0
    wb["Grupos"]["D3"] = -4
    wb.save(ruta)
    with pytest.raises(ErrorInstancia) as exc:
        construir_instancia(leer_excel(ruta))
    assert len(exc.value.errores) == 3


def test_falta_una_hoja(plantilla):
    _, ruta = plantilla
    wb = load_workbook(ruta)
    del wb["Grupos"]
    wb.save(ruta)
    with pytest.raises(ErrorInstancia, match="Falta la hoja Grupos"):
        leer_excel(ruta)
