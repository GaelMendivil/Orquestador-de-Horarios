"""Operadores genéticos. No modifican sus argumentos."""

from __future__ import annotations

import random
from collections.abc import Sequence

from .dominios import Dominio
from .evaluacion import Evaluacion, Gen
from .modelo import Instancia


def inicializar(dominios: Sequence[Dominio], rng: random.Random) -> list[Gen]:
    return [(rng.choice(d.bloques), rng.choice(d.salones)) for d in dominios]


def torneo(poblacion: Sequence[tuple[list[Gen], Evaluacion]], k: int,
           rng: random.Random) -> list[Gen]:
    competidores = [poblacion[rng.randrange(len(poblacion))] for _ in range(k)]
    return min(competidores, key=lambda ind: ind[1].clave())[0]


def tramos_de_cruce(inst: Instancia) -> list[range]:
    """Un tramo por bloque curricular, o por sección si sólo hay uno."""
    def agrupar(clave):
        tramos, inicio = [], 0
        for i in range(1, len(inst.eventos) + 1):
            if i == len(inst.eventos) or clave(inst.eventos[i]) != clave(inst.eventos[inicio]):
                tramos.append(range(inicio, i))
                inicio = i
        return tramos

    por_bloque = agrupar(lambda e: e.seccion.bloque_curricular)
    return por_bloque if len(por_bloque) > 1 else agrupar(lambda e: e.seccion.id)


def cruce_por_tramos(padre1: Sequence[Gen], padre2: Sequence[Gen], tramos: Sequence[range],
                     rng: random.Random) -> list[Gen]:
    hijo = list(padre1)
    for tramo in tramos:
        if rng.random() < 0.5:
            hijo[tramo.start:tramo.stop] = padre2[tramo.start:tramo.stop]
    return hijo


def mutar(horario: Sequence[Gen], dominios: Sequence[Dominio], tramos: Sequence[range],
          p_mutacion: float, rng: random.Random) -> list[Gen]:
    hijo = list(horario)
    tramo_de = {}
    for tramo in tramos:
        for i in tramo:
            tramo_de[i] = tramo
    for i in range(len(hijo)):
        if rng.random() >= p_mutacion:
            continue
        tramo = tramo_de[i]
        if rng.random() < 0.5 or len(tramo) < 2:
            d = dominios[i]
            hijo[i] = (rng.choice(d.bloques), rng.choice(d.salones))
        else:
            j = rng.choice([j for j in tramo if j != i])
            (ti, ri), (tj, rj) = hijo[i], hijo[j]
            if tj in dominios[i].bloques and ti in dominios[j].bloques:
                hijo[i], hijo[j] = (tj, ri), (ti, rj)
    return hijo


class ReparadorPrimerHueco:
    def __init__(self, inst: Instancia, dominios: Sequence[Dominio]):
        self.inst = inst
        self.dominios = dominios
        self.fallos = 0
        self.movimientos = 0

    def __call__(self, horario: Sequence[Gen], rng: random.Random | None = None) -> list[Gen]:
        inst = self.inst
        hijo = list(horario)
        salon_ocupado, prof_ocupado, curr_ocupado, dia_ocupado = set(), set(), set(), set()

        def choca_bloque(e, t, evitar_mismo_dia):
            """Choques que no dependen del salón: profesor, grupo y día."""
            s = e.seccion
            return ((s.profesor, t) in prof_ocupado or (s.bloque_curricular, t) in curr_ocupado
                    or ((evitar_mismo_dia or inst.exige_dias_distintos(s))
                        and (s.id, inst.dia_de(t)) in dia_ocupado))

        for i, e in enumerate(inst.eventos):
            t, r = hijo[i]
            s = e.seccion
            if (r, t) in salon_ocupado or choca_bloque(e, t, False):
                nuevo = (self._buscar_hueco(i, e, choca_bloque, salon_ocupado, True)
                         or self._buscar_hueco(i, e, choca_bloque, salon_ocupado, False))
                if nuevo is None:
                    self.fallos += 1
                else:
                    self.movimientos += 1
                    t, r = hijo[i] = nuevo
            elif (s.id, inst.dia_de(t)) in dia_ocupado:
                nuevo = self._buscar_hueco(i, e, choca_bloque, salon_ocupado, True)
                if nuevo is not None:
                    self.movimientos += 1
                    t, r = hijo[i] = nuevo
            salon_ocupado.add((r, t))
            prof_ocupado.add((s.profesor, t))
            curr_ocupado.add((s.bloque_curricular, t))
            dia_ocupado.add((s.id, inst.dia_de(t)))
        return hijo

    def _buscar_hueco(self, i, e, choca_bloque, salon_ocupado, evitar_mismo_dia):
        d = self.dominios[i]
        for t in d.bloques:
            if choca_bloque(e, t, evitar_mismo_dia):
                continue
            for r in d.salones:
                if (r, t) not in salon_ocupado:
                    return (t, r)
        return None
