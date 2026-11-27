"""Operadores genéticos. Reciben un `random.Random` explícito y no modifican sus argumentos."""

from __future__ import annotations

import random
from collections.abc import Sequence

from .dominios import Dominio
from .evaluacion import Evaluacion, Gen
from .modelo import Instancia


# --- Inicialización -----------------------------------------------------------

def inicializar(dominios: Sequence[Dominio], rng: random.Random) -> list[Gen]:
    """Horario aleatorio uniforme dentro del dominio de cada evento."""
    return [(rng.choice(d.bloques), rng.choice(d.salones)) for d in dominios]


# --- Selección ----------------------------------------------------------------

def torneo(poblacion: Sequence[tuple[list[Gen], Evaluacion]], k: int,
           rng: random.Random) -> list[Gen]:
    """Elige k individuos al azar (con reemplazo) y devuelve el de menor clave (V, S)."""
    competidores = [poblacion[rng.randrange(len(poblacion))] for _ in range(k)]
    return min(competidores, key=lambda ind: ind[1].clave())[0]


# --- Cruce --------------------------------------------------------------------

def tramos_de_cruce(inst: Instancia) -> list[range]:
    """Un tramo por bloque curricular, o por sección si sólo hay un bloque curricular."""
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
    """Cruce uniforme por tramos: cada tramo completo viene de uno de los dos padres."""
    hijo = list(padre1)
    for tramo in tramos:
        if rng.random() < 0.5:
            hijo[tramo.start:tramo.stop] = padre2[tramo.start:tramo.stop]
    return hijo


# --- Mutación -----------------------------------------------------------------

def mutar(horario: Sequence[Gen], dominios: Sequence[Dominio], tramos: Sequence[range],
          p_mutacion: float, rng: random.Random) -> list[Gen]:
    """Por gen, con probabilidad p_mutacion: reasigna (bloque, salón) al azar o
    intercambia el bloque con otro evento del mismo tramo (cada uno conserva su salón).
    """
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


# --- Reparación ---------------------------------------------------------------

class ReparadorPrimerHueco:
    """Reparación "primer hueco compatible" (línea base, lamarckiana).

    Cada evento que choca con uno ya colocado se mueve al primer (bloque, salón)
    libre de su dominio, prefiriendo otro día de su sección. Si no hay, cuenta como fallo.
    """

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
            """Choques que no dependen del salón: profesor, grupo y día de la sección."""
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
                # Sólo puede pasar si "mismo día" es blando: se mueve si hay un hueco limpio.
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
        # Un bloque con choque se descarta sin revisar sus salones (mismo resultado, más rápido).
        d = self.dominios[i]
        for t in d.bloques:
            if choca_bloque(e, t, evitar_mismo_dia):
                continue
            for r in d.salones:
                if (r, t) not in salon_ocupado:
                    return (t, r)
        return None


class ReparadorGuiado:
    """Reparación guiada (lamarckiana).

    Recoloca los eventos con choque y los genes `marcados` por la mutación,
    primero el más restringido (DSatur), cada uno en el bloque libre que menos sube S.
    """

    def __init__(self, inst: Instancia, dominios: Sequence[Dominio], evaluador):
        self.inst = inst
        self.dominios = dominios
        self.fallos = 0
        self.movimientos = 0
        self.pesos = evaluador.pesos
        curriculares = inst.bloques_curriculares()
        self._k = [curriculares.index(e.seccion.bloque_curricular) for e in inst.eventos]
        self._tope = evaluador._tope_diario
        self._piso = evaluador._piso_diario
        self._primer_bloque = evaluador._primer_bloque
        self._pref = [inst.profesores[e.seccion.profesor].preferidos for e in inst.eventos]

    def _costo_dia(self, k: int, bloques: list[int]) -> float:
        """Costo blando de un día de un grupo con clases en `bloques` (posiciones del día)."""
        p = self.pesos
        n = len(bloques)
        if n == 0:
            return p["pocas_clases"] * self._piso[k]
        huecos = max(bloques) - min(bloques) + 1 - n
        exceso = max(0, n - self._tope[k])
        pocas = max(0, self._piso[k] - n)
        tarde = 1 if min(bloques) != self._primer_bloque[k] else 0
        return (p["huecos"] * huecos + p["carga_diaria"] * exceso + p["pocas_clases"] * pocas
                + p["inicio_tarde"] * tarde)

    def __call__(self, horario: Sequence[Gen], rng: random.Random,
                 marcados: frozenset[int] = frozenset()) -> list[Gen]:
        inst = self.inst
        B = inst.bloques_por_dia
        hijo = list(horario)
        salon_ocupado, prof_ocupado, curr_ocupado, dia_ocupado = set(), set(), set(), set()
        # Bloques (posición en el día) que ya ocupa cada grupo cada día.
        dia_grupo: dict[tuple[int, int], list[int]] = {}

        def colocar(i, t, r):
            s = inst.eventos[i].seccion
            salon_ocupado.add((r, t))
            prof_ocupado.add((s.profesor, t))
            curr_ocupado.add((s.bloque_curricular, t))
            dia_ocupado.add((s.id, inst.dia_de(t)))
            dia_grupo.setdefault((self._k[i], inst.dia_de(t)), []).append(t % B)

        def choca(i, t):
            s = inst.eventos[i].seccion
            return ((s.profesor, t) in prof_ocupado or (s.bloque_curricular, t) in curr_ocupado
                    or (inst.exige_dias_distintos(s) and (s.id, inst.dia_de(t)) in dia_ocupado))

        def libres(i):
            """Bloques sin choque duro con al menos un salón libre, con su salón."""
            d = self.dominios[i]
            res = []
            for t in d.bloques:
                if choca(i, t):
                    continue
                for r in d.salones:
                    if (r, t) not in salon_ocupado:
                        res.append((t, r))
                        break
            return res

        # 1. Se quedan los eventos sin choque que no mutaron; el resto queda pendiente.
        pendientes = []
        for i, (t, r) in enumerate(hijo):
            if i in marcados or (r, t) in salon_ocupado or choca(i, t):
                pendientes.append(i)
            else:
                colocar(i, t, r)

        # 2. Más restringido primero (orden fijo al empezar, desempate por índice).
        pendientes.sort(key=lambda i: (len(libres(i)), i))

        # 3. Cada pendiente va al bloque libre que menos sube S.
        p = self.pesos
        for i in pendientes:
            s = inst.eventos[i].seccion
            k = self._k[i]
            opciones = libres(i)
            if not opciones:
                t, r = hijo[i]
                self.fallos += 1
                colocar(i, t, r)
                continue
            mejor_costo, mejores = None, []
            for t, r in opciones:
                d = inst.dia_de(t)
                actuales = dia_grupo.get((k, d), [])
                costo = self._costo_dia(k, actuales + [t % B]) - self._costo_dia(k, actuales)
                pref = self._pref[i]
                if pref is not None and t not in pref:
                    costo += p["preferencias"]
                if (s.id, d) in dia_ocupado:
                    costo += p["mismo_dia"]
                if mejor_costo is None or costo < mejor_costo - 1e-12:
                    mejor_costo, mejores = costo, [(t, r)]
                elif abs(costo - mejor_costo) <= 1e-12:
                    mejores.append((t, r))
            t, r = mejores[0] if len(mejores) == 1 else rng.choice(mejores)
            if (t, r) != hijo[i]:
                self.movimientos += 1
            hijo[i] = (t, r)
            colocar(i, t, r)
        return hijo
