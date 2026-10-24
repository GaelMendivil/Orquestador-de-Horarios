"""Presentación de horarios como tablas, independiente de la interfaz."""

from __future__ import annotations

import csv
import io

from .evaluacion import Horario
from .modelo import NOMBRES_DIAS, Instancia

VISTAS = ("bloque_curricular", "profesor", "salon")


def opciones_de_vista(inst: Instancia, vista: str) -> list[str]:
    if vista == "bloque_curricular":
        return list(inst.bloques_curriculares())
    if vista == "profesor":
        return sorted(inst.profesores)
    if vista == "salon":
        return [s.id for s in inst.salones]
    raise ValueError(f"vista desconocida: {vista!r}")


def tabla_semanal(inst: Instancia, horario: Horario, vista: str, clave: str) -> dict:
    """Cuadrícula bloques × días; los empalmes se separan con " / "."""
    filas = [inst.etiquetas_bloques[b] if inst.etiquetas_bloques else f"B{b + 1}"
             for b in range(inst.bloques_por_dia)]
    columnas = list(NOMBRES_DIAS[:inst.dias])
    celdas = [["" for _ in columnas] for _ in filas]
    for e, (t, r) in zip(inst.eventos, horario):
        s = e.seccion
        salon = inst.salones[r].id
        if vista == "bloque_curricular" and s.bloque_curricular == clave:
            texto = f"{s.materia} · {s.profesor} · {salon}"
        elif vista == "profesor" and s.profesor == clave:
            texto = f"{s.materia} ({s.bloque_curricular}) · {salon}"
        elif vista == "salon" and salon == clave:
            texto = f"{s.materia} ({s.bloque_curricular}) · {s.profesor}"
        else:
            continue
        celda = celdas[inst.bloque_de(t)][inst.dia_de(t)]
        celdas[inst.bloque_de(t)][inst.dia_de(t)] = f"{celda} / {texto}" if celda else texto
    relevantes = [e.seccion for e in inst.eventos if _pertenece(inst, e, horario, vista, clave)] or inst.secciones
    if inst.turnos and all(s.turno for s in relevantes):
        visibles = sorted(set().union(*(inst.turnos[s.turno] for s in relevantes)))
        filas = [filas[b] for b in visibles]
        celdas = [celdas[b] for b in visibles]
    return {"filas": filas, "columnas": columnas, "celdas": celdas}


def _pertenece(inst, e, horario, vista, clave) -> bool:
    s = e.seccion
    if vista == "bloque_curricular":
        return s.bloque_curricular == clave
    if vista == "profesor":
        return s.profesor == clave
    return inst.salones[horario[e.indice][1]].id == clave


def horario_csv(inst: Instancia, horario: Horario) -> str:
    filas = []
    for e, (t, r) in zip(inst.eventos, horario):
        s = e.seccion
        filas.append((s.bloque_curricular, inst.dia_de(t), inst.bloque_de(t), {
            "carrera": s.carrera, "grupo": s.bloque_curricular, "seccion": s.id, "materia": s.materia,
            "sesion": e.numero_sesion + 1, "profesor": s.profesor,
            "dia": NOMBRES_DIAS[inst.dia_de(t)], "bloque": inst.nombre_bloque(t).split(" ", 1)[1],
            "salon": inst.salones[r].id, "inscritos": s.inscritos,
            "capacidad": inst.salones[r].capacidad,
        }))
    filas.sort(key=lambda f: f[:3])
    salida = io.StringIO()
    escritor = csv.DictWriter(salida, fieldnames=list(filas[0][3]))
    escritor.writeheader()
    escritor.writerows(f[3] for f in filas)
    return salida.getvalue()
