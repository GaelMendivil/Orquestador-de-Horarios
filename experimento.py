"""Corre el experimento del Avance 3 sobre CETYS: una variante de reparación × varias semillas.

Uso (desde la carpeta horarios/):
    python experimento.py primer_hueco                 # semillas 1..30, en paralelo
    python experimento.py ninguna --semillas 1-5 --procesos 2
    python experimento.py primer_hueco --salida resultados/mi_corrida

Todas las variantes usan la configuración de linea_base.json salvo la reparación.
Escribe <salida>/<variante>_<semilla>.json y un resumen <salida>/<variante>.csv.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

from horarios.configuracion import cargar_configuracion, construir_instancia  # noqa: E402
from horarios.entrada import instancia_desde_dict  # noqa: E402
from horarios.ga import ConfiguracionGA, ejecutar  # noqa: E402

LINEA_BASE = AQUI / "linea_base.json"
CAMPOS = ["variante", "semilla", "v", "s", "huecos", "fuera_preferencia", "exceso_diario",
          "faltante_diario", "inicio_tarde", "mismo_dia", "evaluaciones",
          "evaluaciones_hasta_factible", "segundos", "motivo_fin", "certificado"]


def huella(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()[:16]


def leer_linea_base() -> dict:
    return json.loads(LINEA_BASE.read_text(encoding="utf-8"))


def correr_una(variante: str, semilla: int, salida: str) -> dict:
    base = leer_linea_base()
    config = cargar_configuracion(AQUI / base["configuracion"])
    datos, _ = construir_instancia(config)
    inst = instancia_desde_dict(datos)
    cfg = ConfiguracionGA(**{**base["ga"], "reparacion": variante, "semilla": semilla})
    r = ejecutar(inst, cfg)
    e = r.evaluacion
    fila = {"variante": variante, "semilla": semilla, "v": e.v, "s": e.s, "huecos": e.huecos,
            "fuera_preferencia": e.fuera_preferencia, "exceso_diario": e.exceso_diario,
            "faltante_diario": e.faltante_diario, "inicio_tarde": e.inicio_tarde,
            "mismo_dia": e.mismo_dia, "evaluaciones": r.evaluaciones,
            "evaluaciones_hasta_factible": r.evaluaciones_hasta_factible,
            "segundos": round(r.segundos, 1), "motivo_fin": r.motivo_fin,
            "certificado": r.reporte.factible}
    detalle = {**fila, "ga": asdict(cfg), "historial": [asdict(h) for h in r.historial]}
    Path(salida, f"{variante}_{semilla}.json").write_text(json.dumps(detalle), encoding="utf-8")
    print(f"{variante} semilla {semilla}: V = {e.v}, S = {e.s:.4f}, {r.segundos:.0f} s", flush=True)
    return fila


def semillas(texto: str) -> list[int]:
    a, _, b = texto.partition("-")
    return list(range(int(a), int(b or a) + 1))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("variante")
    p.add_argument("--semillas", default="1-30")
    p.add_argument("--procesos", type=int, default=4)
    p.add_argument("--salida", default="resultados")
    a = p.parse_args()
    Path(a.salida).mkdir(parents=True, exist_ok=True)
    lista = semillas(a.semillas)
    with ProcessPoolExecutor(a.procesos) as ex:
        filas = list(ex.map(correr_una, [a.variante] * len(lista), lista, [a.salida] * len(lista)))
    with open(Path(a.salida, f"{a.variante}.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        w.writeheader()
        w.writerows(filas)


if __name__ == "__main__":
    main()
