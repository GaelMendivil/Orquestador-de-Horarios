"""Validador independiente y distinto a propósito de evaluacion.py.

k eventos en el mismo recurso y bloque cuentan k - 1.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .modelo import Instancia


@dataclass
class Reporte:
    salon: int = 0
    profesor: int = 0
    curricular: int = 0
    dias: int = 0
    capacidad: int = 0
    disponibilidad: int = 0
    turno: int = 0
    fuera_de_rango: int = 0
    mensajes: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return (self.salon + self.profesor + self.curricular + self.dias
                + self.capacidad + self.disponibilidad + self.turno + self.fuera_de_rango)

    @property
    def factible(self) -> bool:
        return self.total == 0


def validar(inst: Instancia, horario) -> Reporte:
    rep = Reporte()
    eventos = inst.eventos
    if len(horario) != len(eventos):
        rep.fuera_de_rango += 1
        rep.mensajes.append(f"El horario tiene {len(horario)} genes y hay {len(eventos)} eventos")
        return rep

    def nombre(i):
        e = eventos[i]
        return f"{e.seccion.id} (sesión {e.numero_sesion + 1})"

    for i, (t, r) in enumerate(horario):
        e = eventos[i]
        if not (0 <= t < inst.num_bloques and 0 <= r < len(inst.salones)):
            rep.fuera_de_rango += 1
            rep.mensajes.append(f"{nombre(i)}: bloque {t} o salón {r} fuera de rango")
            continue
        salon = inst.salones[r]
        if salon.capacidad < e.seccion.inscritos:
            rep.capacidad += 1
            rep.mensajes.append(
                f"{nombre(i)}: {e.seccion.inscritos} inscritos en {salon.id} (capacidad {salon.capacidad})"
            )
        if e.seccion.turno is not None and inst.bloque_de(t) not in inst.turnos[e.seccion.turno]:
            rep.turno += 1
            rep.mensajes.append(f"{nombre(i)}: {inst.nombre_bloque(t)} está fuera del turno {e.seccion.turno}")
        disp = inst.profesores[e.seccion.profesor].disponibles
        if disp is not None and t not in disp:
            rep.disponibilidad += 1
            rep.mensajes.append(f"{nombre(i)}: {e.seccion.profesor} no está disponible en {inst.nombre_bloque(t)}")

        choque = {"salon": None, "profesor": None, "curricular": None, "dias": None}
        for j in range(i):
            tj, rj = horario[j]
            ej = eventos[j]
            if tj == t and rj == r and choque["salon"] is None:
                choque["salon"] = j
            if tj == t and ej.seccion.profesor == e.seccion.profesor and choque["profesor"] is None:
                choque["profesor"] = j
            if (tj == t and ej.seccion.bloque_curricular == e.seccion.bloque_curricular
                    and choque["curricular"] is None):
                choque["curricular"] = j
            if (ej.seccion.id == e.seccion.id and inst.exige_dias_distintos(e.seccion)
                    and inst.dia_de(tj) == inst.dia_de(t) and choque["dias"] is None):
                choque["dias"] = j

        cuando = inst.nombre_bloque(t)
        if choque["salon"] is not None:
            rep.salon += 1
            rep.mensajes.append(f"{nombre(i)} y {nombre(choque['salon'])} en {salon.id} el {cuando}")
        if choque["profesor"] is not None:
            rep.profesor += 1
            rep.mensajes.append(
                f"{e.seccion.profesor} tiene {nombre(i)} y {nombre(choque['profesor'])} el {cuando}"
            )
        if choque["curricular"] is not None:
            rep.curricular += 1
            rep.mensajes.append(
                f"{e.seccion.bloque_curricular} tiene {nombre(i)} y {nombre(choque['curricular'])} el {cuando}"
            )
        if choque["dias"] is not None:
            rep.dias += 1
            rep.mensajes.append(f"{e.seccion.id} tiene dos sesiones el mismo día ({cuando.split()[0]})")
    return rep
