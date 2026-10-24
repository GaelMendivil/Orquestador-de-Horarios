"""Traduce la configuración en tablas a una instancia del GA.

Cada materia de un (carrera, semestre) se abre una vez por grupo. Si tiene
varios profesores ("Ana, Luis"), se reparten entre los grupos en orden.
"""

from __future__ import annotations

import json
import math
import re
import unicodedata
from pathlib import Path
from typing import Any

from .entrada import ErrorInstancia
from .modelo import NOMBRES_DIAS

FORMATO = "organizador-horarios/configuracion-1"

COLUMNAS: dict[str, tuple[str, ...]] = {
    "bloques": ("Inicio", "Fin", "Turno"),
    "salones": ("Salón", "Edificio", "Capacidad"),
    "profesores": ("Profesor", "Disponible", "Prefiere"),
    "grupos": ("Carrera", "Semestre", "Grupo", "Alumnos", "Turno"),
    "materias": ("Carrera", "Semestre", "Materia", "Profesor", "Sesiones", "Alumnos"),
}
TABLAS = tuple(COLUMNAS)
NOMBRES_TABLAS = {"bloques": "Bloques", "salones": "Salones", "profesores": "Profesores",
                  "grupos": "Grupos", "materias": "Materias"}
GENERAL_POR_DEFECTO = {"nombre": "Mi escuela", "dias": 5}


def configuracion_vacia() -> dict:
    return {"formato": FORMATO, "general": dict(GENERAL_POR_DEFECTO), **{t: [] for t in TABLAS}}


def es_configuracion(datos: Any) -> bool:
    return isinstance(datos, dict) and str(datos.get("formato", "")).startswith("organizador-horarios/configuracion")


def normalizar(config: dict) -> dict:
    salida = configuracion_vacia()
    salida["general"].update(config.get("general") or {})
    for tabla, columnas in COLUMNAS.items():
        for fila in config.get(tabla) or []:
            limpia = {c: _limpiar(fila.get(c)) for c in columnas}
            if any(v is not None and v != "" for v in limpia.values()):
                salida[tabla].append(limpia)
    for extra in ("nota",):
        if config.get(extra):
            salida[extra] = config[extra]
    return salida


def cargar_configuracion(ruta: str | Path) -> dict:
    with open(ruta, encoding="utf-8") as f:
        datos = json.load(f)
    if not es_configuracion(datos):
        raise ValueError(f"{ruta} no es un archivo de configuración (falta 'formato')")
    return normalizar(datos)


def guardar_configuracion(config: dict, ruta: str | Path) -> None:
    Path(ruta).write_text(json.dumps(normalizar(config), ensure_ascii=False, indent=1), encoding="utf-8")


def carreras(config: dict) -> list[str]:
    return sorted({_texto(g.get("Carrera")) for g in config.get("grupos", [])} - {""})


def construir_instancia(config: dict, carreras: list[str] | None = None) -> tuple[dict, list[str]]:
    """Devuelve (instancia, avisos); `carreras=None` incluye todas. Lanza ErrorInstancia."""
    config = normalizar(config)
    errores: list[str] = []
    avisos: list[str] = []
    filtro = None if carreras is None else set(carreras)

    g = config["general"]
    dias = _entero(g.get("dias"))
    if dias is None or not 1 <= dias <= len(NOMBRES_DIAS):
        errores.append(f"General: los días de clase deben ser un número entre 1 y {len(NOMBRES_DIAS)}")
        dias = None

    etiquetas, horas = [], []
    turnos: dict[str, list[int]] = {}
    nombres_turno: dict[str, str] = {}
    for i, fila in enumerate(config["bloques"], 1):
        ctx = f"Bloques, fila {i}"
        inicio, fin = _texto(fila["Inicio"]), _texto(fila["Fin"])
        m_ini, m_fin = _minutos(inicio), _minutos(fin)
        if inicio and fin and (m_ini is None or m_fin is None):
            errores.append(f"{ctx}: las horas deben escribirse como 16:00")
        if m_ini is not None and m_fin is not None and m_fin <= m_ini:
            errores.append(f"{ctx}: el fin ({fin}) debe ser después del inicio ({inicio})")
        etiquetas.append(f"{inicio}-{fin}" if inicio and fin else inicio or fin or f"Bloque {i}")
        horas.append((m_ini, m_fin))
        turno = _texto(fila["Turno"])
        if turno:
            nombre = nombres_turno.setdefault(_clave(turno), turno)
            turnos.setdefault(nombre, []).append(i)
    if not etiquetas:
        errores.append("Bloques: falta al menos un bloque del día")
    num_bloques = len(etiquetas)

    salones = []
    for i, fila in enumerate(config["salones"], 1):
        ctx = f"Salones, fila {i}"
        sid = _texto(fila["Salón"])
        cap = _entero(fila["Capacidad"])
        if not sid:
            errores.append(f"{ctx}: falta el nombre del salón")
        if cap is None or cap < 1:
            errores.append(f"{ctx} ({sid}): la capacidad debe ser un número entero mayor que 0")
        salones.append({"id": sid, "capacidad": cap or 0})
    if not salones:
        errores.append("Salones: falta al menos un salón")
    _duplicados([s["id"] for s in salones if s["id"]], "Salones: el salón", errores)

    turnos_idx = {_clave(n): {b - 1 for b in bs} for n, bs in turnos.items()}
    profesores: dict[str, dict] = {}
    for i, fila in enumerate(config["profesores"], 1):
        pid = _texto(fila["Profesor"])
        ctx = f"Profesores, fila {i}" + (f" ({pid})" if pid else "")
        if not pid:
            errores.append(f"{ctx}: falta el nombre del profesor")
            continue
        if pid in profesores:
            errores.append(f"Profesores: el profesor {pid!r} está repetido")
        prof = {"id": pid}
        for columna, campo in (("Disponible", "disponibles"), ("Prefiere", "preferidos")):
            if dias is None or not num_bloques:
                continue
            try:
                bloques = interpretar_franjas(_texto(fila[columna]), dias, horas, turnos_idx)
            except ValueError as exc:
                errores.append(f"{ctx}, {columna}: {exc}")
                continue
            if bloques is not None:
                prof[campo] = [f"{NOMBRES_DIAS[t // num_bloques]}-{t % num_bloques + 1}" for t in sorted(bloques)]
        profesores[pid] = prof

    grupos: dict[tuple[str, str], list[dict]] = {}
    ids_grupo = []
    for i, fila in enumerate(config["grupos"], 1):
        carrera, semestre, grupo = (_texto(fila[c]) for c in ("Carrera", "Semestre", "Grupo"))
        gid = id_grupo(carrera, semestre, grupo)
        ctx = f"Grupos, fila {i}" + (f" ({gid})" if gid else "")
        if not carrera:
            errores.append(f"{ctx}: falta la carrera")
        alumnos = _entero(fila["Alumnos"])
        if alumnos is None or alumnos < 1:
            errores.append(f"{ctx}: los alumnos deben ser un número entero mayor que 0")
        turno = _texto(fila["Turno"])
        if turno and _clave(turno) not in nombres_turno:
            errores.append(f"{ctx}: el turno {turno!r} no existe en Bloques "
                           f"(turnos definidos: {', '.join(turnos) or 'ninguno'})")
        ids_grupo.append(gid)
        if filtro is not None and carrera not in filtro:
            continue
        grupos.setdefault((carrera, semestre), []).append({
            "id": gid, "alumnos": alumnos or 0, "carrera": carrera,
            "turno": nombres_turno.get(_clave(turno)) if turno else None,
        })
    _duplicados([g for g in ids_grupo if g], "Grupos: el grupo", errores)

    secciones = []
    usados: dict[str, None] = {}
    faltantes: dict[str, None] = {}
    sin_grupo = set()
    con_materias = set()
    for i, fila in enumerate(config["materias"], 1):
        carrera, semestre = _texto(fila["Carrera"]), _texto(fila["Semestre"])
        materia = _texto(fila["Materia"])
        ctx = f"Materias, fila {i}" + (f" ({materia})" if materia else "")
        if filtro is not None and carrera not in filtro:
            continue
        if not materia:
            errores.append(f"{ctx}: falta el nombre de la materia")
        nombres_prof = [p.strip() for p in _texto(fila["Profesor"]).split(",") if p.strip()]
        if not nombres_prof:
            errores.append(f"{ctx}: falta el profesor")
        sesiones = _entero(fila["Sesiones"])
        if sesiones is None or sesiones < 1:
            errores.append(f"{ctx}: las sesiones por semana deben ser un número entero mayor que 0")
        alumnos = _entero(fila["Alumnos"])
        if fila["Alumnos"] not in (None, "") and (alumnos is None or alumnos < 1):
            errores.append(f"{ctx}: los alumnos deben ser un número entero mayor que 0 (o vacío)")
        de_grupo = grupos.get((carrera, semestre), [])
        if not de_grupo:
            sin_grupo.add(id_grupo(carrera, semestre, ""))
            continue
        con_materias.add((carrera, semestre))
        if not (materia and nombres_prof and sesiones):
            continue
        for k, grupo in enumerate(de_grupo):
            profesor = nombres_prof[k % len(nombres_prof)]
            usados[profesor] = None
            if profesor not in profesores:
                faltantes[profesor] = None
            seccion = {
                "id": f"{grupo['id']} · {materia}", "materia": materia, "profesor": profesor,
                "inscritos": alumnos or grupo["alumnos"], "sesiones": sesiones,
                "bloque_curricular": grupo["id"], "carrera": carrera,
            }
            if grupo["turno"]:
                seccion["turno"] = grupo["turno"]
            secciones.append(seccion)
    _duplicados([s["id"] for s in secciones], "Materias: la materia", errores,
                sufijo=" (una materia aparece dos veces en el mismo semestre)")

    if sin_grupo:
        avisos.append("Hay materias de semestres sin grupos, así que no se programan: "
                      + _lista(sorted(sin_grupo)))
    vacios = [g["id"] for clave, gs in grupos.items() if clave not in con_materias for g in gs]
    if vacios:
        avisos.append("Estos grupos no tienen materias: " + _lista(vacios))
    if faltantes:
        avisos.append(f"{len(faltantes)} profesores de Materias no están en Profesores; se toman como "
                      "siempre disponibles: " + _lista(list(faltantes)))
    if not secciones and not errores:
        errores.append("No hay ninguna materia que programar (revisa Grupos y Materias)")

    if errores:
        raise ErrorInstancia(errores)

    datos = {
        "nombre": _texto(g.get("nombre")) or "sin nombre",
        "dias": dias,
        "bloques_por_dia": num_bloques,
        "etiquetas_bloques": etiquetas,
        "turnos": turnos,
        "sesiones_en_dias_distintos": False,
        "salones": salones,
        "profesores": [profesores.get(p, {"id": p}) for p in usados],
        "secciones": secciones,
    }
    return datos, avisos


def id_grupo(carrera: str, semestre: str, grupo: str) -> str:
    return " ".join(p for p in (carrera, semestre, grupo) if p)


_DIAS = {"lun": 0, "lunes": 0, "mar": 1, "martes": 1, "mie": 2, "miercoles": 2,
         "jue": 3, "jueves": 3, "vie": 4, "viernes": 4, "sab": 5, "sabado": 5,
         "dom": 6, "domingo": 6}
_TODO = {"todo", "siempre", "todos"}
EJEMPLOS_FRANJAS = "Ejemplos: 'vespertino', 'Lun-Vie 16:00-20:00', 'Lun,Mié 4-6; Vie todo'"


def interpretar_franjas(texto: str, dias: int, horas: list[tuple[int | None, int | None]],
                        turnos: dict[str, set[int]]) -> frozenset[int] | None:
    """Texto como "Lun-Jue 16:00-22:00; Vie matutino" -> bloques t (None si está vacío).

    Cada parte: [días] [bloques]. Bloques: "todo", un turno, números ("4-6")
    o horas ("16:00-20:00").
    """
    texto = _clave(texto)
    if not texto:
        return None
    texto = re.sub(r"\s*([-,])\s*", r"\1", texto)
    num_bloques = len(horas)
    resultado: set[int] = set()
    for parte in re.split(r"[;\n]+", texto):
        parte = parte.strip()
        if not parte:
            continue
        primero, _, resto = parte.partition(" ")
        dias_parte = _leer_dias(primero, dias)
        if dias_parte is None:
            dias_parte, resto = range(dias), parte
        bloques = _leer_bloques(resto.strip() or "todo", horas, turnos)
        resultado.update(d * num_bloques + b for d in dias_parte for b in bloques)
    return frozenset(resultado)


def franjas_a_texto(bloques_t, dias: int, num_bloques: int) -> str:
    if bloques_t is None:
        return ""
    por_dia = [sorted(t % num_bloques for t in bloques_t if t // num_bloques == d) for d in range(dias)]
    if all(len(b) == num_bloques for b in por_dia):
        return "todo"
    if all(b == por_dia[0] for b in por_dia):
        return _rangos(por_dia[0])
    partes = [f"{NOMBRES_DIAS[d]} {_rangos(b)}" for d, b in enumerate(por_dia) if b]
    return "; ".join(partes) or "nunca"


def _leer_dias(token: str, dias: int) -> list[int] | None:
    resultado = []
    for pieza in token.split(","):
        extremos = pieza.split("-")
        if len(extremos) > 2 or not all(e in _DIAS for e in extremos):
            return None
        a, b = _DIAS[extremos[0]], _DIAS[extremos[-1]]
        if a > b:
            raise ValueError(f"el rango de días {pieza!r} está al revés")
        if b >= dias:
            raise ValueError(f"{NOMBRES_DIAS[b]} no es día de clase (la semana tiene {dias} días)")
        resultado.extend(range(a, b + 1))
    return resultado


def _leer_bloques(texto: str, horas, turnos) -> set[int]:
    num_bloques = len(horas)
    resultado: set[int] = set()
    for pieza in texto.replace(" ", ",").split(","):
        if not pieza:
            continue
        if pieza in _TODO:
            resultado.update(range(num_bloques))
        elif pieza in turnos:
            resultado.update(turnos[pieza])
        elif m := re.fullmatch(r"(\d{1,2}:\d{2})-(\d{1,2}:\d{2})", pieza):
            ini, fin = _minutos(m[1]), _minutos(m[2])
            if any(h[0] is None or h[1] is None for h in horas):
                raise ValueError(f"para usar horas ({pieza}) todos los bloques deben tener Inicio y Fin")
            dentro = {b for b, (a, z) in enumerate(horas) if a >= ini and z <= fin}
            if not dentro:
                raise ValueError(f"ningún bloque cabe completo entre {m[1]} y {m[2]}")
            resultado.update(dentro)
        elif m := re.fullmatch(r"(\d+)(?:-(\d+))?", pieza):
            a, b = int(m[1]), int(m[2] or m[1])
            if not 1 <= a <= b <= num_bloques:
                raise ValueError(f"el bloque {pieza} no existe (hay {num_bloques} bloques por día; "
                                 "para horas escribe 16:00-22:00)")
            resultado.update(range(a - 1, b))
        else:
            raise ValueError(f"no entiendo {pieza!r}. {EJEMPLOS_FRANJAS}")
    return resultado


def _rangos(numeros: list[int]) -> str:
    """[0, 1, 2, 4] -> "1-3,5" (bloques en base 1)."""
    partes, i = [], 0
    while i < len(numeros):
        j = i
        while j + 1 < len(numeros) and numeros[j + 1] == numeros[j] + 1:
            j += 1
        a, b = numeros[i] + 1, numeros[j] + 1
        partes.append(f"{a}-{b}" if b > a else f"{a}")
        i = j + 1
    return ",".join(partes)


def configuracion_desde_instancia(datos: dict) -> dict:
    """Convierte una instancia a tablas editables (cada bloque curricular es un grupo)."""
    dias, nb = datos["dias"], datos["bloques_por_dia"]
    etiquetas = datos.get("etiquetas_bloques") or []
    turno_de = {}
    for nombre, bloques in (datos.get("turnos") or {}).items():
        for b in bloques:
            turno_de.setdefault(b, nombre)
    bloques = []
    for b in range(1, nb + 1):
        inicio, fin = "", ""
        if b <= len(etiquetas):
            m = re.fullmatch(r"\s*(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})\s*", etiquetas[b - 1])
            inicio, fin = (m[1], m[2]) if m else (etiquetas[b - 1], "")
        inicio = inicio or f"B{b}"
        bloques.append({"Inicio": inicio or None, "Fin": fin or None, "Turno": turno_de.get(b)})

    def a_t(lista):
        if lista is None:
            return None
        return {NOMBRES_DIAS.index(x.split("-")[0]) * nb + int(x.split("-")[1]) - 1 for x in lista}

    profesores = [{"Profesor": p["id"],
                   "Disponible": franjas_a_texto(a_t(p.get("disponibles")), dias, nb) or None,
                   "Prefiere": franjas_a_texto(a_t(p.get("preferidos")), dias, nb) or None}
                  for p in datos["profesores"]]

    por_bc: dict[str, list[dict]] = {}
    for s in datos["secciones"]:
        por_bc.setdefault(s["bloque_curricular"], []).append(s)
    grupos, materias = [], []
    for bc, secciones in sorted(por_bc.items()):
        alumnos = max(s["inscritos"] for s in secciones)
        turnos_bc = {s.get("turno") for s in secciones}
        grupos.append({"Carrera": bc, "Semestre": None, "Grupo": None, "Alumnos": alumnos,
                       "Turno": turnos_bc.pop() if len(turnos_bc) == 1 else None})
        for s in secciones:
            materias.append({"Carrera": bc, "Semestre": None, "Materia": s["materia"],
                             "Profesor": s["profesor"], "Sesiones": s["sesiones"],
                             "Alumnos": s["inscritos"] if s["inscritos"] != alumnos else None})
    return normalizar({
        "formato": FORMATO,
        "general": {"nombre": datos.get("nombre", "sin nombre"), "dias": dias},
        "bloques": bloques,
        "salones": [{"Salón": s["id"], "Edificio": None, "Capacidad": s["capacidad"]} for s in datos["salones"]],
        "profesores": profesores, "grupos": grupos, "materias": materias,
    })


def _limpiar(v):
    if v is None or isinstance(v, float) and math.isnan(v):
        return None
    if isinstance(v, str):
        v = v.strip()
        return v or None
    if hasattr(v, "item"):
        return _limpiar(v.item())
    if isinstance(v, float) and v.is_integer():
        return int(v)
    return v


def _texto(v) -> str:
    v = _limpiar(v)
    return "" if v is None else str(v).strip()


def _entero(v) -> int | None:
    v = _limpiar(v)
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, str) and re.fullmatch(r"\d+", v):
        return int(v)
    return None


def _booleano(v) -> bool:
    v = _limpiar(v)
    if v is None:
        return False
    if isinstance(v, bool):
        return v
    t = _clave(str(v))
    if t in ("si", "s", "true", "verdadero", "1", "x"):
        return True
    if t in ("no", "n", "false", "falso", "0"):
        return False
    raise ValueError(v)


def _minutos(hora: str) -> int | None:
    m = re.fullmatch(r"(\d{1,2}):(\d{2})", hora or "")
    if not m or int(m[1]) > 23 or int(m[2]) > 59:
        return None
    return int(m[1]) * 60 + int(m[2])


def _clave(texto: str) -> str:
    sin = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", sin.lower()).strip()


def _duplicados(ids, prefijo, errores, sufijo="") -> None:
    vistos = set()
    for i in ids:
        if i in vistos:
            errores.append(f"{prefijo} {i!r} está repetido{sufijo}")
        vistos.add(i)


def _lista(nombres: list[str], maximo: int = 8) -> str:
    texto = ", ".join(nombres[:maximo])
    return texto + (f" y {len(nombres) - maximo} más" if len(nombres) > maximo else "")
