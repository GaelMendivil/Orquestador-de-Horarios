import json
from pathlib import Path

from horarios.generador import ParametrosGenerador, generar, ocupacion

REFERENCIA = {
    "sint_10.json": ParametrosGenerador(bloques_curriculares=2, materias_por_bloque=5, salones=2, semilla=10),
    "sint_30.json": ParametrosGenerador(bloques_curriculares=5, materias_por_bloque=6, salones=4,
                                        fraccion_disponible=0.7, semilla=30),
    "sint_100.json": ParametrosGenerador(bloques_curriculares=10, materias_por_bloque=10, salones=10,
                                         secciones_por_profesor=3, fraccion_disponible=0.7, semilla=100),
}

if __name__ == "__main__":
    carpeta = Path(__file__).parent / "instancias"
    for nombre, p in REFERENCIA.items():
        datos = generar(p)
        (carpeta / nombre).write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
        eventos = sum(s["sesiones"] for s in datos["secciones"])
        print(f"{nombre}: {len(datos['secciones'])} secciones, {eventos} eventos, "
              f"{len(datos['profesores'])} profesores, ocupación {ocupacion(datos):.2f}")
