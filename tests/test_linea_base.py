"""Vigila que la línea base congelada (linea_base.json) no cambie.

Si alguna de estas pruebas falla después de tocar el código, la línea base ya
no es la misma que se midió y la comparación del Avance 3 deja de ser justa:
hay que revertir el cambio (o volver a medir la línea base completa).
Valores obtenidos el 16-nov-2026 con el código congelado.
"""

import hashlib
import json
from pathlib import Path

import pytest

from horarios.configuracion import cargar_configuracion, construir_instancia
from horarios.entrada import cargar_instancia, instancia_desde_dict
from horarios.ga import ConfiguracionGA, ejecutar

RAIZ = Path(__file__).resolve().parent.parent
BASE = json.loads((RAIZ / "linea_base.json").read_text(encoding="utf-8"))


def huella(horario) -> str:
    return hashlib.sha256(json.dumps([list(g) for g in horario]).encode()).hexdigest()[:16]


def correr(inst, reparacion, evaluaciones):
    cfg = ConfiguracionGA(**{**BASE["ga"], "reparacion": reparacion, "semilla": 1,
                             "max_evaluaciones": evaluaciones})
    return ejecutar(inst, cfg)


@pytest.mark.parametrize("reparacion, v, s, h", [
    ("primer_hueco", 0, 0.19749999999999998, "cf60091296db3937"),
    ("ninguna", 4, 0.2675, "60b7de681a5d219f"),
])
def test_linea_base_sint30(reparacion, v, s, h):
    r = correr(cargar_instancia(RAIZ / "instancias" / "sint_30.json"), reparacion, 3000)
    assert (r.evaluacion.v, r.evaluacion.s, huella(r.mejor)) == (v, s, h)


@pytest.mark.parametrize("reparacion, v, s, h", [
    ("primer_hueco", 0, 0.10763175906913074, "68e058d4008231b1"),
    ("ninguna", 1116, 0.23861510381017564, "3becebb8fd7fcdb2"),
])
def test_linea_base_cetys(reparacion, v, s, h):
    datos, _ = construir_instancia(cargar_configuracion(RAIZ / BASE["configuracion"]))
    r = correr(instancia_desde_dict(datos), reparacion, 500)
    assert (r.evaluacion.v, r.evaluacion.s, huella(r.mejor)) == (v, s, h)
