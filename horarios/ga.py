"""GA generacional con elitismo.

Termina al agotar evaluaciones, al llegar a V = S = 0, o si el mejor es
factible y no mejora en `paciencia` generaciones.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field

from .dominios import calcular_dominios, diagnosticar_inviabilidad
from .evaluacion import Evaluacion, Evaluador, Gen
from .modelo import Instancia
from .operadores import (ReparadorPrimerHueco, cruce_por_tramos, inicializar, mutar,
                         torneo, tramos_de_cruce)
from .validador import Reporte, validar

REPARACIONES = ("ninguna", "primer_hueco")


@dataclass(frozen=True)
class ConfiguracionGA:
    tam_poblacion: int = 100
    k_torneo: int = 2
    p_cruce: float = 0.9
    p_mutacion: float | None = None
    elitismo: int = 2
    max_evaluaciones: int = 20_000
    paciencia: int = 100
    reparacion: str = "primer_hueco"
    pesos: dict[str, float] | None = None
    semilla: int = 0

    def __post_init__(self):
        errores = []
        if self.tam_poblacion < 2:
            errores.append("tam_poblacion debe ser ≥ 2")
        if not 1 <= self.k_torneo <= self.tam_poblacion:
            errores.append("k_torneo debe estar entre 1 y tam_poblacion")
        if not 0 <= self.elitismo < self.tam_poblacion:
            errores.append("elitismo debe estar entre 0 y tam_poblacion - 1")
        if not 0 <= self.p_cruce <= 1:
            errores.append("p_cruce debe estar en [0, 1]")
        if self.p_mutacion is not None and not 0 <= self.p_mutacion <= 1:
            errores.append("p_mutacion debe estar en [0, 1]")
        if self.reparacion not in REPARACIONES:
            errores.append(f"reparacion debe ser una de {REPARACIONES}")
        if self.max_evaluaciones < self.tam_poblacion:
            errores.append("max_evaluaciones debe ser ≥ tam_poblacion")
        if errores:
            raise ValueError("; ".join(errores))


@dataclass
class RegistroGeneracion:
    generacion: int
    evaluaciones: int
    mejor_v: int
    mejor_s: float
    media_v: float
    factibles: float
    diversidad: float
    segundos: float


@dataclass
class Resultado:
    mejor: list[Gen]
    evaluacion: Evaluacion
    reporte: Reporte
    historial: list[RegistroGeneracion]
    evaluaciones: int
    evaluaciones_hasta_factible: int | None
    segundos: float
    motivo_fin: str
    fallos_reparacion: int = 0
    configuracion: ConfiguracionGA = field(default_factory=ConfiguracionGA)


class InstanciaInviable(Exception):
    def __init__(self, motivos: list[str]):
        self.motivos = motivos
        super().__init__("La instancia es inviable:\n- " + "\n- ".join(motivos))


def ejecutar(inst: Instancia, cfg: ConfiguracionGA = ConfiguracionGA(),
             al_terminar_generacion=None) -> Resultado:
    """`al_terminar_generacion(registro)` permite mostrar el progreso."""
    inicio = time.perf_counter()
    dominios = calcular_dominios(inst)
    motivos = diagnosticar_inviabilidad(inst, dominios)
    if motivos:
        raise InstanciaInviable(motivos)

    rng = random.Random(cfg.semilla)
    evaluador = Evaluador(inst, cfg.pesos)
    tramos = tramos_de_cruce(inst)
    p_mut = cfg.p_mutacion if cfg.p_mutacion is not None else 1 / len(inst.eventos)
    reparar = ReparadorPrimerHueco(inst, dominios) if cfg.reparacion == "primer_hueco" else None

    def nuevo_individuo(horario):
        if reparar is not None:
            horario = reparar(horario)
        return (horario, evaluador.evaluar(horario))

    poblacion = [nuevo_individuo(inicializar(dominios, rng)) for _ in range(cfg.tam_poblacion)]
    mejor = min(poblacion, key=lambda ind: ind[1].clave())
    evals_factible = evaluador.evaluaciones if mejor[1].factible else None
    historial = [_registrar(0, poblacion, mejor, evaluador, inicio)]
    sin_mejora = 0
    generacion = 0
    motivo = "presupuesto de evaluaciones agotado"

    while True:
        if mejor[1].factible and mejor[1].s == 0:
            motivo = "óptimo alcanzado (V = 0 y S = 0)"
            break
        if mejor[1].factible and sin_mejora >= cfg.paciencia:
            motivo = f"sin mejora durante {cfg.paciencia} generaciones"
            break
        if evaluador.evaluaciones + (cfg.tam_poblacion - cfg.elitismo) > cfg.max_evaluaciones:
            break

        generacion += 1
        ordenada = sorted(poblacion, key=lambda ind: ind[1].clave())
        siguiente = ordenada[:cfg.elitismo]
        while len(siguiente) < cfg.tam_poblacion:
            p1 = torneo(poblacion, cfg.k_torneo, rng)
            if rng.random() < cfg.p_cruce:
                hijo = cruce_por_tramos(p1, torneo(poblacion, cfg.k_torneo, rng), tramos, rng)
            else:
                hijo = list(p1)
            hijo = mutar(hijo, dominios, tramos, p_mut, rng)
            siguiente.append(nuevo_individuo(hijo))
            if evals_factible is None and siguiente[-1][1].factible:
                evals_factible = evaluador.evaluaciones
        poblacion = siguiente

        candidato = min(poblacion, key=lambda ind: ind[1].clave())
        if candidato[1].clave() < mejor[1].clave():
            mejor, sin_mejora = candidato, 0
        else:
            sin_mejora += 1
        registro = _registrar(generacion, poblacion, mejor, evaluador, inicio)
        historial.append(registro)
        if al_terminar_generacion is not None:
            al_terminar_generacion(registro)

    return Resultado(
        mejor=mejor[0],
        evaluacion=mejor[1],
        reporte=validar(inst, mejor[0]),
        historial=historial,
        evaluaciones=evaluador.evaluaciones,
        evaluaciones_hasta_factible=evals_factible,
        segundos=time.perf_counter() - inicio,
        motivo_fin=motivo,
        fallos_reparacion=reparar.fallos if reparar else 0,
        configuracion=cfg,
    )


def _registrar(generacion, poblacion, mejor, evaluador, inicio) -> RegistroGeneracion:
    n = len(poblacion)
    genes_mejor = mejor[0]
    num_genes = len(genes_mejor)
    distintos = sum(
        sum(1 for a, b in zip(ind[0], genes_mejor) if a != b) for ind in poblacion
    ) / (n * num_genes)
    return RegistroGeneracion(
        generacion=generacion,
        evaluaciones=evaluador.evaluaciones,
        mejor_v=mejor[1].v,
        mejor_s=mejor[1].s,
        media_v=sum(ind[1].v for ind in poblacion) / n,
        factibles=sum(1 for ind in poblacion if ind[1].factible) / n,
        diversidad=distintos,
        segundos=time.perf_counter() - inicio,
    )
