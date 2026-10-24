"""Modelo de datos inmutable.

t = dia * bloques_por_dia + bloque; el día 0 es lunes.
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
    disponibles: frozenset[int] | None = None
    preferidos: frozenset[int] | None = None


@dataclass(frozen=True)
class Seccion:

    id: str
    materia: str
    profesor: str
    inscritos: int
    sesiones: int
    bloque_curricular: str
    turno: str | None = None
    permitir_mismo_dia: bool = False
    carrera: str = ""


@dataclass(frozen=True)
class Evento:

    indice: int
    seccion: Seccion
    numero_sesion: int


@dataclass(frozen=True)
class Instancia:
    nombre: str
    dias: int
    bloques_por_dia: int
    salones: tuple[Salon, ...]
    profesores: dict[str, Profesor]
    secciones: tuple[Seccion, ...]
    etiquetas_bloques: tuple[str, ...] = ()
    turnos: dict[str, frozenset[int]] = field(default_factory=dict)
    sesiones_en_dias_distintos: bool = True
    eventos: tuple[Evento, ...] = field(init=False)

    def __post_init__(self) -> None:
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
