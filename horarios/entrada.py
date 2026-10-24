"""Carga y valida instancias JSON (ver instancias/ejemplo_minimo.json).

Los bloques se escriben "Día-n" con n desde 1 ("Lun-1").
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .modelo import NOMBRES_DIAS, Instancia, Profesor, Salon, Seccion


class ErrorInstancia(ValueError):
    """Instancia mal formada; contiene todos los errores."""

    def __init__(self, errores: list[str]):
        self.errores = errores
        super().__init__("Instancia inválida:\n- " + "\n- ".join(errores))


def cargar_instancia(ruta: str | Path) -> Instancia:
    with open(ruta, encoding="utf-8") as f:
        datos = json.load(f)
    return instancia_desde_dict(datos)


def instancia_desde_dict(datos: dict[str, Any]) -> Instancia:
    errores: list[str] = []

    dias = _entero(datos, "dias", errores, minimo=1, maximo=len(NOMBRES_DIAS))
    bloques_por_dia = _entero(datos, "bloques_por_dia", errores, minimo=1)
    etiquetas = tuple(datos.get("etiquetas_bloques", ()))
    if etiquetas and bloques_por_dia and len(etiquetas) != bloques_por_dia:
        errores.append(
            f"etiquetas_bloques tiene {len(etiquetas)} elementos, "
            f"pero bloques_por_dia es {bloques_por_dia}"
        )

    turnos: dict[str, frozenset[int]] = {}
    for nombre, bloques in (datos.get("turnos") or {}).items():
        if (not isinstance(bloques, list) or not bloques
                or not all(isinstance(b, int) and bloques_por_dia and 1 <= b <= bloques_por_dia
                           for b in bloques)):
            errores.append(f"turno {nombre!r}: debe ser una lista de bloques del día entre 1 y {bloques_por_dia}")
            continue
        turnos[nombre] = frozenset(b - 1 for b in bloques)
    dias_distintos = datos.get("sesiones_en_dias_distintos", True)
    if not isinstance(dias_distintos, bool):
        errores.append("sesiones_en_dias_distintos debe ser true o false")

    salones = []
    for i, s in enumerate(datos.get("salones", [])):
        cap = _entero(s, "capacidad", errores, minimo=1, contexto=f"salón #{i + 1}")
        salones.append(Salon(id=str(s.get("id", "")), capacidad=cap or 0))
    if not salones:
        errores.append("no hay salones")
    _sin_duplicados([s.id for s in salones], "salón", errores)

    profesores: dict[str, Profesor] = {}
    for p in datos.get("profesores", []):
        pid = str(p.get("id", ""))
        if pid in profesores:
            errores.append(f"profesor duplicado: {pid!r}")
        profesores[pid] = Profesor(
            id=pid,
            disponibles=_bloques(p.get("disponibles"), dias, bloques_por_dia, errores, pid),
            preferidos=_bloques(p.get("preferidos"), dias, bloques_por_dia, errores, pid),
        )

    secciones = []
    for i, s in enumerate(datos.get("secciones", [])):
        ctx = f"sección {s.get('id', f'#{i + 1}')!r}"
        for campo in ("id", "materia", "profesor", "bloque_curricular"):
            if not s.get(campo):
                errores.append(f"{ctx}: falta el campo {campo!r}")
        if s.get("turno") is not None and s["turno"] not in turnos:
            errores.append(f"{ctx}: el turno {s['turno']!r} no está definido en 'turnos'")
        if not isinstance(s.get("permitir_mismo_dia", False), bool):
            errores.append(f"{ctx}: permitir_mismo_dia debe ser true o false")
        if s.get("profesor") and s["profesor"] not in profesores:
            errores.append(f"{ctx}: el profesor {s['profesor']!r} no está en la lista de profesores")
        secciones.append(
            Seccion(
                id=str(s.get("id", "")),
                materia=str(s.get("materia", "")),
                profesor=str(s.get("profesor", "")),
                inscritos=_entero(s, "inscritos", errores, minimo=1, contexto=ctx) or 0,
                sesiones=_entero(s, "sesiones", errores, minimo=1, contexto=ctx) or 0,
                bloque_curricular=str(s.get("bloque_curricular", "")),
                turno=s.get("turno"),
                permitir_mismo_dia=s.get("permitir_mismo_dia", False) is True,
                carrera=str(s.get("carrera") or ""),
            )
        )
    if not secciones:
        errores.append("no hay secciones")
    _sin_duplicados([s.id for s in secciones], "sección", errores)

    if errores:
        raise ErrorInstancia(errores)

    return Instancia(
        nombre=str(datos.get("nombre", "sin nombre")),
        dias=dias,
        bloques_por_dia=bloques_por_dia,
        salones=tuple(salones),
        profesores=profesores,
        secciones=tuple(secciones),
        etiquetas_bloques=etiquetas,
        turnos=turnos,
        sesiones_en_dias_distintos=dias_distintos is not False,
    )


def _entero(d, campo, errores, minimo=None, maximo=None, contexto="instancia"):
    valor = d.get(campo)
    if not isinstance(valor, int) or isinstance(valor, bool):
        errores.append(f"{contexto}: {campo!r} debe ser un entero (se recibió {valor!r})")
        return None
    if minimo is not None and valor < minimo:
        errores.append(f"{contexto}: {campo!r} debe ser ≥ {minimo} (se recibió {valor})")
        return None
    if maximo is not None and valor > maximo:
        errores.append(f"{contexto}: {campo!r} debe ser ≤ {maximo} (se recibió {valor})")
        return None
    return valor


def _bloques(lista, dias, bloques_por_dia, errores, pid) -> frozenset[int] | None:
    if lista is None:
        return None
    if not dias or not bloques_por_dia:
        return None
    resultado = set()
    for texto in lista:
        try:
            nombre_dia, n = str(texto).split("-")
            d = NOMBRES_DIAS.index(nombre_dia)
            b = int(n) - 1
            if not (0 <= d < dias and 0 <= b < bloques_por_dia):
                raise ValueError
        except ValueError:
            errores.append(f"profesor {pid!r}: bloque inválido {texto!r} (formato 'Lun-1')")
            continue
        resultado.add(d * bloques_por_dia + b)
    return frozenset(resultado)


def _sin_duplicados(ids, tipo, errores) -> None:
    vistos = set()
    for i in ids:
        if i in vistos:
            errores.append(f"{tipo} duplicado: {i!r}")
        vistos.add(i)
