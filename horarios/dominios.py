"""Dominios de los genes (imponen H4 y H5) y detección temprana de inviabilidad.

Las comprobaciones de inviabilidad son condiciones necesarias, no suficientes.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .modelo import Instancia


@dataclass(frozen=True)
class Dominio:
    """Valores permitidos para el gen (t, r) de un evento: bloques × salones."""

    bloques: tuple[int, ...]
    salones: tuple[int, ...]  # índices en Instancia.salones

    def vacio(self) -> bool:
        return not self.bloques or not self.salones


def calcular_dominios(inst: Instancia) -> tuple[Dominio, ...]:
    todos_los_bloques = range(inst.num_bloques)
    dominios = []
    for e in inst.eventos:
        s = e.seccion
        profesor = inst.profesores[s.profesor]
        turno = inst.turnos.get(s.turno) if s.turno is not None else None
        bloques = tuple(
            t for t in todos_los_bloques
            if (profesor.disponibles is None or t in profesor.disponibles)
            and (turno is None or inst.bloque_de(t) in turno)
        )
        salones = tuple(
            i for i, salon in enumerate(inst.salones) if salon.capacidad >= s.inscritos
        )
        dominios.append(Dominio(bloques, salones))
    return tuple(dominios)


def diagnosticar_inviabilidad(inst: Instancia, dominios: tuple[Dominio, ...]) -> list[str]:
    """Devuelve los motivos por los que la instancia es seguro inviable (vacío = no se detectó ninguno)."""
    problemas: list[str] = []

    # 1. Algún evento sin valores posibles.
    vistas = set()
    for e, dom in zip(inst.eventos, dominios):
        s = e.seccion
        if s.id in vistas:
            continue
        vistas.add(s.id)
        if not dom.salones:
            problemas.append(
                f"La sección {s.id} tiene {s.inscritos} inscritos y ningún salón tiene esa capacidad"
            )
        if not dom.bloques:
            problemas.append(f"El profesor {s.profesor} de la sección {s.id} no tiene bloques disponibles")

    # 2. Un profesor con más sesiones que bloques disponibles (H2 + H5).
    sesiones_por_profesor = Counter(e.seccion.profesor for e in inst.eventos)
    for pid, n in sesiones_por_profesor.items():
        disp = inst.profesores[pid].disponibles
        capacidad = inst.num_bloques if disp is None else len(disp)
        if n > capacidad:
            problemas.append(f"El profesor {pid} tiene {n} sesiones y sólo {capacidad} bloques disponibles")

    # 3. Un bloque curricular con más sesiones que bloques utilizables (H3).
    por_bloque: dict[str, list[int]] = {}
    for e, dom in zip(inst.eventos, dominios):
        por_bloque.setdefault(e.seccion.bloque_curricular, []).append(e.indice)
    for bc, indices in por_bloque.items():
        utilizables = set().union(*(dominios[i].bloques for i in indices))
        if len(indices) > len(utilizables):
            problemas.append(
                f"El bloque curricular {bc} tiene {len(indices)} sesiones y sólo {len(utilizables)} "
                f"bloques utilizables en la semana"
            )

    # 4. Una sección con más sesiones que días (H6: sesiones en días distintos).
    for s in inst.secciones:
        if inst.exige_dias_distintos(s) and s.sesiones > inst.dias:
            problemas.append(f"La sección {s.id} tiene {s.sesiones} sesiones y sólo hay {inst.dias} días")

    # 5. Más sesiones que pares (salón, bloque) utilizables (H1), por umbral de capacidad.
    for c in sorted({s.inscritos for s in inst.secciones}):
        n_sesiones = sum(1 for e in inst.eventos if e.seccion.inscritos >= c)
        n_salones = sum(1 for r in inst.salones if r.capacidad >= c)
        plazas = n_salones * inst.num_bloques
        if n_sesiones > plazas:
            problemas.append(
                f"Hay {n_sesiones} sesiones con ≥{c} inscritos y sólo {plazas} pares (salón, bloque) "
                f"con esa capacidad"
            )

    return problemas
