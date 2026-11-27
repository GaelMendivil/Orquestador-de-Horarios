"""Evaluación de horarios: violaciones duras V(x) y penalizaciones blandas S(x).

Un horario tiene un gen (t, r) por evento: t es el bloque de la semana y r el
índice del salón. S(x) = Σ w_k P_k / Z con Z = Σ w_k U_k (peor caso), así que
S ∈ [0, 1] y cada peso es el costo de una ocurrencia. Se compara (V, S)
lexicográficamente. H4 y H5 se garantizan con los dominios, no se miden aquí.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from .modelo import Instancia

Gen = tuple[int, int]  # (bloque t, índice de salón r)
Horario = Sequence[Gen]

PESOS_POR_DEFECTO = {"huecos": 1.0, "preferencias": 1.0, "carga_diaria": 1.0, "pocas_clases": 3.0,
                     "mismo_dia": 0.1, "inicio_tarde": 3.0}


@dataclass(frozen=True)
class Evaluacion:
    v_salon: int
    v_profesor: int
    v_curricular: int
    v_dias: int
    huecos: int            # P1: horas muertas (en bloques)
    fuera_preferencia: int  # P2: sesiones fuera de los bloques preferidos
    exceso_diario: int     # P3a: sesiones por encima de techo(n/días) por grupo y día
    faltante_diario: int   # P3b: sesiones que faltan para piso(n/días) por grupo y día
    mismo_dia: int         # P4: sesiones repetidas el mismo día en secciones exentas de H6
    inicio_tarde: int      # P5: días con clase que no empiezan en el primer bloque del turno
    s: float               # S(x) normalizada y ponderada, en [0, 1]

    @property
    def v(self) -> int:
        return self.v_salon + self.v_profesor + self.v_curricular + self.v_dias

    @property
    def factible(self) -> bool:
        return self.v == 0

    def clave(self) -> tuple[int, float]:
        """Clave de orden lexicográfico: menor es mejor."""
        return (self.v, self.s)


class Evaluador:
    def __init__(self, inst: Instancia, pesos: dict[str, float] | None = None):
        pesos = dict(PESOS_POR_DEFECTO if pesos is None else pesos)
        if set(pesos) != set(PESOS_POR_DEFECTO) or any(w < 0 for w in pesos.values()):
            raise ValueError(f"pesos debe tener las claves {sorted(PESOS_POR_DEFECTO)} con valores ≥ 0")
        total = sum(pesos.values())
        if total == 0:
            raise ValueError("al menos un peso debe ser positivo")
        self.pesos = {k: w / total for k, w in pesos.items()}
        self.inst = inst

        # Índices enteros precalculados para que evaluar() sólo haga aritmética.
        profesores = sorted(inst.profesores)
        curriculares = inst.bloques_curriculares()
        secciones = [s.id for s in inst.secciones]
        self._prof = [profesores.index(e.seccion.profesor) for e in inst.eventos]
        self._curr = [curriculares.index(e.seccion.bloque_curricular) for e in inst.eventos]
        self._secc = [secciones.index(e.seccion.id) for e in inst.eventos]
        # Secciones sujetas a H6 (dura); las demás van a P4 (blanda).
        self._h6 = [inst.exige_dias_distintos(s) for s in inst.secciones]
        self._preferidos = [inst.profesores[e.seccion.profesor].preferidos for e in inst.eventos]
        self._num_prof = len(profesores)
        self._num_curr = len(curriculares)
        self._num_secc = len(secciones)

        # Cotas de peor caso para normalizar. Huecos por grupo y día ≤ bloques usables - 2.
        self.u_huecos = 0
        for bc in curriculares:
            turnos = {e.seccion.turno for e in inst.eventos if e.seccion.bloque_curricular == bc}
            if None in turnos or not inst.turnos:
                largo = inst.bloques_por_dia
            else:
                largo = len(set().union(*(inst.turnos[t] for t in turnos)))
            self.u_huecos += inst.dias * max(0, largo - 2)
        self.u_preferencias = sum(1 for p in self._preferidos if p is not None)
        # P3: entre piso(n/días) y techo(n/días) sesiones por día; peor caso, todas el mismo día.
        sesiones_por_curr = [self._curr.count(k) for k in range(self._num_curr)]
        self._tope_diario = [-(-n // inst.dias) for n in sesiones_por_curr]
        self._piso_diario = [n // inst.dias for n in sesiones_por_curr]
        self.u_carga = sum(n - c for n, c in zip(sesiones_por_curr, self._tope_diario))
        self.u_pocas = sum((inst.dias - 1) * f for f in self._piso_diario)
        # P5: primer bloque del turno de cada grupo (o del día, si no tiene turno).
        self._primer_bloque = []
        for bc in curriculares:
            turnos = {e.seccion.turno for e in inst.eventos if e.seccion.bloque_curricular == bc}
            if None in turnos or not inst.turnos:
                permitidos = list(range(inst.bloques_por_dia))
            else:
                permitidos = sorted(set().union(*(inst.turnos[t] for t in turnos)))
            self._primer_bloque.append(permitidos[0])
        self.u_inicio = self._num_curr * inst.dias
        self.u_mismo_dia = sum(max(0, s.sesiones - 1) for s, h6 in zip(inst.secciones, self._h6) if not h6)
        self.z = (self.pesos["huecos"] * self.u_huecos + self.pesos["preferencias"] * self.u_preferencias
                  + self.pesos["carga_diaria"] * self.u_carga + self.pesos["pocas_clases"] * self.u_pocas
                  + self.pesos["mismo_dia"] * self.u_mismo_dia
                  + self.pesos["inicio_tarde"] * self.u_inicio)
        self.evaluaciones = 0  # contador para el presupuesto del GA

    def evaluar(self, horario: Horario) -> Evaluacion:
        self.evaluaciones += 1
        inst = self.inst
        T = inst.num_bloques
        B = inst.bloques_por_dia

        ocup_salon = [0] * (len(inst.salones) * T)
        ocup_prof = [0] * (self._num_prof * T)
        ocup_curr = [0] * (self._num_curr * T)
        ocup_dia = [0] * (self._num_secc * inst.dias)
        fuera_pref = 0

        for i, (t, r) in enumerate(horario):
            ocup_salon[r * T + t] += 1
            ocup_prof[self._prof[i] * T + t] += 1
            ocup_curr[self._curr[i] * T + t] += 1
            ocup_dia[self._secc[i] * inst.dias + t // B] += 1
            pref = self._preferidos[i]
            if pref is not None and t not in pref:
                fuera_pref += 1

        huecos = 0
        exceso_diario = faltante_diario = inicio_tarde = 0
        for k in range(self._num_curr):
            tope, piso, primero = self._tope_diario[k], self._piso_diario[k], self._primer_bloque[k]
            for d in range(inst.dias):
                base = k * T + d * B
                ocupados = [b for b in range(B) if ocup_curr[base + b] > 0]
                if ocupados:
                    huecos += ocupados[-1] - ocupados[0] + 1 - len(ocupados)
                sesiones_dia = sum(ocup_curr[base:base + B])
                exceso_diario += max(0, sesiones_dia - tope)
                faltante_diario += max(0, piso - sesiones_dia)
                if ocupados and ocupados[0] != primero:
                    inicio_tarde += 1

        v_dias = mismo_dia = 0
        for k in range(self._num_secc):
            exceso = _exceso(ocup_dia[k * inst.dias:(k + 1) * inst.dias])
            if self._h6[k]:
                v_dias += exceso
            else:
                mismo_dia += exceso

        p = self.pesos
        s = (p["huecos"] * huecos + p["preferencias"] * fuera_pref
             + p["carga_diaria"] * exceso_diario + p["pocas_clases"] * faltante_diario
             + p["mismo_dia"] * mismo_dia
             + p["inicio_tarde"] * inicio_tarde)
        s = s / self.z if self.z else 0.0

        return Evaluacion(
            v_salon=_exceso(ocup_salon),
            v_profesor=_exceso(ocup_prof),
            v_curricular=_exceso(ocup_curr),
            v_dias=v_dias,
            huecos=huecos,
            fuera_preferencia=fuera_pref,
            exceso_diario=exceso_diario,
            faltante_diario=faltante_diario,
            mismo_dia=mismo_dia,
            inicio_tarde=inicio_tarde,
            s=s,
        )


def _exceso(ocupaciones: list[int]) -> int:
    """Suma de max(0, k - 1): cuántos eventos sobran en total."""
    return sum(k - 1 for k in ocupaciones if k > 1)
