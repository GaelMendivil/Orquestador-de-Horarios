"""Modelo de datos inmutable del problema de horarios.

Un bloque t = dia * bloques_por_dia + bloque (día 0 = lunes). Salones y eventos
se identifican por su posición en `Instancia.salones` e `Instancia.eventos`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

NOMBRES_DIAS = ("Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom")


@dataclass(frozen=True)
class Salon:
    id: str
    capacidad: int


@dataclass(frozen=True)
class Profesor:
    id: str
    disponibles: frozenset[int] | None = None  # H5; None = siempre
    preferidos: frozenset[int] | None = None   # S2; None = sin preferencias


@dataclass(frozen=True)
class Seccion:
    """Una materia abierta con un profesor fijo y un número de inscritos."""

    id: str
    materia: str
    profesor: str
    inscritos: int
    sesiones: int
    bloque_curricular: str               # secciones que no se empalman (H3)
    turno: str | None = None             # None = cualquier bloque del día
    permitir_mismo_dia: bool = False     # excepción a H6
    carrera: str = ""                    # sólo informativo


@dataclass(frozen=True)
class Evento:
    """Una sesión concreta de una sección: la unidad que asigna el GA."""

    indice: int
    seccion: Seccion
    numero_sesion: int  # 0, 1, ... hasta seccion.sesiones - 1


@dataclass(frozen=True)
class Instancia:
    nombre: str
    dias: int
    bloques_por_dia: int
    salones: tuple[Salon, ...]
    profesores: dict[str, Profesor]
    secciones: tuple[Seccion, ...]
    etiquetas_bloques: tuple[str, ...] = ()  # p. ej. "07:00-08:40"
    turnos: dict[str, frozenset[int]] = field(default_factory=dict)  # bloques del día, base 0
    sesiones_en_dias_distintos: bool = True  # regla H6
    eventos: tuple[Evento, ...] = field(init=False)

    def __post_init__(self) -> None:
        # Ordenados por bloque curricular para que el cruce opere sobre tramos contiguos.
        ordenadas = sorted(self.secciones, key=lambda s: (s.bloque_curricular, s.id))
        eventos = []
        for seccion in ordenadas:
            for k in range(seccion.sesiones):
                eventos.append(Evento(len(eventos), seccion, k))
        object.__setattr__(self, "eventos", tuple(eventos))

    @property
    def num_bloques(self) -> int:
        return self.dias * self.bloques_por_dia

    def dia_de(self, t: int) -> int:
        return t // self.bloques_por_dia

    def bloque_de(self, t: int) -> int:
        return t % self.bloques_por_dia

    def nombre_bloque(self, t: int) -> str:
        dia = NOMBRES_DIAS[self.dia_de(t)]
        b = self.bloque_de(t)
        etiqueta = self.etiquetas_bloques[b] if self.etiquetas_bloques else f"B{b + 1}"
        return f"{dia} {etiqueta}"

    def exige_dias_distintos(self, seccion: Seccion) -> bool:
        return self.sesiones_en_dias_distintos and not seccion.permitir_mismo_dia

    def bloques_curriculares(self) -> tuple[str, ...]:
        return tuple(sorted({s.bloque_curricular for s in self.secciones}))
