"""Generador de instancias sintéticas reproducibles (misma semilla, misma instancia)."""

from __future__ import annotations

import math
import random
from dataclasses import asdict, dataclass

from .modelo import NOMBRES_DIAS


@dataclass(frozen=True)
class ParametrosGenerador:
    dias: int = 5
    bloques_por_dia: int = 6
    bloques_curriculares: int = 2
    materias_por_bloque: int = 6
    sesiones_por_materia: int = 2
    secciones_por_profesor: float = 2.0
    fraccion_disponible: float = 1.0
    fraccion_preferida: float = 0.5
    inscritos_min: int = 20
    inscritos_max: int = 40
    salones: int = 2
    capacidad_min: int = 25
    capacidad_max: int = 45
    semilla: int = 0


def generar(p: ParametrosGenerador) -> dict:
    _validar(p)
    rng = random.Random(p.semilla)
    num_bloques = p.dias * p.bloques_por_dia

    capacidades = [rng.randint(p.capacidad_min, p.capacidad_max) for _ in range(p.salones)]
    capacidades[capacidades.index(max(capacidades))] = max(max(capacidades), p.inscritos_max)
    salones = [{"id": f"S{i + 1}", "capacidad": c} for i, c in enumerate(capacidades)]

    secciones = []
    for g in range(p.bloques_curriculares):
        bc = f"G{g + 1}"
        for m in range(p.materias_por_bloque):
            secciones.append({
                "id": f"{bc}-M{m + 1}",
                "materia": f"Materia {m + 1}",
                "profesor": None,
                "inscritos": rng.randint(p.inscritos_min, p.inscritos_max),
                "sesiones": p.sesiones_por_materia,
                "bloque_curricular": bc,
            })

    _asegurar_capacidad(salones, secciones, num_bloques)

    num_profesores = max(1, math.ceil(len(secciones) / p.secciones_por_profesor))
    orden = list(range(len(secciones)))
    rng.shuffle(orden)
    carga = [0] * num_profesores
    for turno, i in enumerate(orden):
        k = turno % num_profesores
        secciones[i]["profesor"] = f"P{k + 1}"
        carga[k] += p.sesiones_por_materia

    profesores = []
    for k in range(num_profesores):
        prof = {"id": f"P{k + 1}"}
        disponibles = list(range(num_bloques))
        if p.fraccion_disponible < 1.0:
            n = max(round(p.fraccion_disponible * num_bloques), carga[k] + 2)
            disponibles = sorted(rng.sample(disponibles, min(n, num_bloques)))
            prof["disponibles"] = [_texto_bloque(t, p.bloques_por_dia) for t in disponibles]
        if p.fraccion_preferida > 0:
            n = max(1, round(p.fraccion_preferida * len(disponibles)))
            preferidos = sorted(rng.sample(disponibles, n))
            prof["preferidos"] = [_texto_bloque(t, p.bloques_por_dia) for t in preferidos]
        profesores.append(prof)

    return {
        "nombre": f"sintética g{p.bloques_curriculares}x{p.materias_por_bloque} "
                  f"s{p.salones} semilla {p.semilla}",
        "parametros_generador": asdict(p),
        "dias": p.dias,
        "bloques_por_dia": p.bloques_por_dia,
        "salones": salones,
        "profesores": profesores,
        "secciones": secciones,
    }


def _asegurar_capacidad(salones: list[dict], secciones: list[dict], num_bloques: int) -> None:
    """Agranda salones hasta cumplir la regla de capacidad de diagnosticar_inviabilidad."""
    for c in sorted({s["inscritos"] for s in secciones}, reverse=True):
        necesarias = sum(s["sesiones"] for s in secciones if s["inscritos"] >= c)
        while necesarias > num_bloques * sum(1 for r in salones if r["capacidad"] >= c):
            cortos = [r for r in salones if r["capacidad"] < c]
            if not cortos:
                raise ValueError(
                    f"{necesarias} sesiones no caben en {len(salones)} salones × {num_bloques} "
                    f"bloques: aumenta el número de salones"
                )
            max(cortos, key=lambda r: r["capacidad"])["capacidad"] = c


def ocupacion(datos: dict) -> float:
    """Sesiones / (salones × bloques)."""
    sesiones = sum(s["sesiones"] for s in datos["secciones"])
    plazas = len(datos["salones"]) * datos["dias"] * datos["bloques_por_dia"]
    return sesiones / plazas


def _texto_bloque(t: int, bloques_por_dia: int) -> str:
    return f"{NOMBRES_DIAS[t // bloques_por_dia]}-{t % bloques_por_dia + 1}"


def _validar(p: ParametrosGenerador) -> None:
    errores = []
    if not 1 <= p.dias <= len(NOMBRES_DIAS):
        errores.append("dias fuera de rango")
    for campo in ("bloques_por_dia", "bloques_curriculares", "materias_por_bloque",
                  "sesiones_por_materia", "salones", "inscritos_min", "capacidad_min"):
        if getattr(p, campo) < 1:
            errores.append(f"{campo} debe ser ≥ 1")
    if p.inscritos_min > p.inscritos_max:
        errores.append("inscritos_min > inscritos_max")
    if p.capacidad_min > p.capacidad_max:
        errores.append("capacidad_min > capacidad_max")
    if p.secciones_por_profesor < 1:
        errores.append("secciones_por_profesor debe ser ≥ 1")
    if not 0 < p.fraccion_disponible <= 1 or not 0 <= p.fraccion_preferida <= 1:
        errores.append("las fracciones deben estar en (0, 1]")
    if errores:
        raise ValueError("; ".join(errores))
