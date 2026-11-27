import json
import math
import random
from pathlib import Path

from openpyxl import load_workbook

from horarios.configuracion import FORMATO, guardar_configuracion, normalizar
from materias_cetys import MATERIAS

AQUI = Path(__file__).resolve().parent
DESTINO = AQUI / "configuraciones"
EXCEL_CETYS = AQUI.parent / "datos" / "CETYS_Tijuana_base_aproximada.xlsx"

BLOQUES = [
    {"Inicio": "08:00", "Fin": "09:40", "Turno": "matutino"},
    {"Inicio": "10:00", "Fin": "11:40", "Turno": "matutino"},
    {"Inicio": "12:00", "Fin": "13:40", "Turno": "matutino"},
    {"Inicio": "16:00", "Fin": "17:40", "Turno": "vespertino"},
    {"Inicio": "18:00", "Fin": "19:40", "Turno": "vespertino"},
    {"Inicio": "20:00", "Fin": "21:40", "Turno": "vespertino"},
]
CUPO_GRUPO = 30            # alumnos máximos por grupo al dividir una generación
MATERIAS_POR_SEMESTRE = 6
SECCIONES_POR_PROFESOR = 3


NOMBRES = ["Alejandro", "Ana", "Andrés", "Beatriz", "Carlos", "Carmen", "Claudia", "Daniel", "Diana",
           "Eduardo", "Elena", "Fernando", "Gabriela", "Guillermo", "Héctor", "Isabel", "Javier", "Jorge",
           "José Luis", "Karla", "Laura", "Leticia", "Luis", "Manuel", "Marcela", "María José", "Mariana",
           "Mario", "Martha", "Miguel", "Mónica", "Norma", "Óscar", "Patricia", "Pablo", "Raúl", "Ricardo",
           "Roberto", "Rosa", "Sandra", "Sergio", "Silvia", "Sofía", "Teresa", "Verónica", "Víctor",
           "Ximena", "Yolanda", "Arturo", "Adriana", "Francisco", "Lorena", "Ernesto", "Paola", "Rodrigo",
           "Alicia", "Gerardo", "Cecilia", "Iván", "Natalia"]
APELLIDOS = ["García", "Hernández", "Martínez", "López", "González", "Rodríguez", "Pérez", "Sánchez",
             "Ramírez", "Flores", "Torres", "Rivera", "Gómez", "Díaz", "Cruz", "Morales", "Reyes",
             "Gutiérrez", "Ortiz", "Castillo", "Jiménez", "Mendoza", "Ruiz", "Vargas", "Romero", "Herrera",
             "Medina", "Aguilar", "Castro", "Ramos", "Vázquez", "Salazar", "Navarro", "Delgado", "Soto",
             "Ríos", "Contreras", "Guerrero", "Estrada", "Ochoa", "Valenzuela", "Ibarra", "Carrillo",
             "Zamora", "Beltrán", "Quintero", "Montoya", "Peralta", "Acosta", "Cervantes"]
_FEMENINOS = {"Ana", "Beatriz", "Carmen", "Claudia", "Diana", "Elena", "Gabriela", "Isabel", "Karla",
              "Laura", "Leticia", "Marcela", "María José", "Mariana", "Martha", "Mónica", "Norma",
              "Patricia", "Rosa", "Sandra", "Silvia", "Sofía", "Teresa", "Verónica", "Ximena", "Yolanda",
              "Adriana", "Lorena", "Paola", "Alicia", "Cecilia", "Natalia"}
PROPORCION_CON_PREFERENCIA = 0.4
INICIO_TURNO = {"matutino": "08:00-11:40", "vespertino": "16:00-19:40"}  # dos primeros bloques
FIN_TURNO = {"matutino": "10:00-13:40", "vespertino": "18:00-21:40"}     # dos últimos bloques


def nombre_profesor(rng: random.Random, usados: set[str]) -> str:
    """Nombre inventado y único, con grado (Dr./Dra., Mtro./Mtra., Ing., Lic.)."""
    while True:
        nombre = rng.choice(NOMBRES)
        f = nombre in _FEMENINOS
        grado = rng.choice(["Dra." if f else "Dr.", "Mtra." if f else "Mtro.", "Mtra." if f else "Mtro.",
                            "Ing.", "Lic."])
        completo = f"{grado} {nombre} {rng.choice(APELLIDOS)} {rng.choice(APELLIDOS)}"
        if completo not in usados:
            usados.add(completo)
            return completo


def preferencia(rng: random.Random, turnos: list[str], disponible: str | None) -> str | None:
    """Preferencia inventada (temprano, tarde, sin viernes o días alternos) o None."""
    if rng.random() >= PROPORCION_CON_PREFERENCIA:
        return None
    tipos = ["temprano", "tarde"] + ([] if disponible else ["sin_viernes", "alternos"])
    tipo = rng.choice(tipos)
    partes = []
    for turno in turnos:
        if tipo == "temprano":
            partes.append(f"Lun-Vie {INICIO_TURNO[turno]}")
        elif tipo == "tarde":
            partes.append(f"Lun-Vie {FIN_TURNO[turno]}")
        elif tipo == "sin_viernes":
            partes.append(f"Lun-Jue {turno}")
        else:
            partes.append(f"Lun,Mié,Vie {turno}")
    return "; ".join(partes)


def icc7() -> dict:
    """ICC 7.º semestre desde instancias/icc7_real.json."""
    real = json.loads((AQUI / "instancias" / "icc7_real.json").read_text(encoding="utf-8"))
    g1 = [s for s in real["secciones"] if s["bloque_curricular"] == "ICC7-G1"]
    return {
        "grupos": [
            {"Carrera": "ICC", "Semestre": 7, "Grupo": "G1", "Alumnos": 21, "Turno": "vespertino"},
            {"Carrera": "ICC", "Semestre": 7, "Grupo": "G2", "Alumnos": 19, "Turno": "vespertino"},
        ],
        "materias": [
            {"Carrera": "ICC", "Semestre": 7, "Materia": s["materia"], "Profesor": s["profesor"],
             "Sesiones": s["sesiones"], "Alumnos": None}
            for s in g1
        ],
        "profesores": [{"Profesor": p["id"], "Disponible": None, "Prefiere": None} for p in real["profesores"]],
    }


def config_icc7() -> dict:
    datos = icc7()
    return {
        "formato": FORMATO,
        "general": {"nombre": "ICC 7.º semestre (2 grupos)", "dias": 5},
        "bloques": BLOQUES,
        "salones": [{"Salón": "Salón ICC-1", "Edificio": None, "Capacidad": 30},
                    {"Salón": "Salón ICC-2", "Edificio": None, "Capacidad": 25}],
        **datos,
    }


def config_cetys() -> dict:
    wb = load_workbook(EXCEL_CETYS, data_only=True)
    rng = random.Random(2026)

    # Sólo aulas con capacidad numérica (los laboratorios no se modelan).
    salones = []
    for fila in wb["Aulas"].iter_rows(min_row=4, values_only=True):
        bloque, _, aula, _, capacidad = fila[:5]
        if aula is not None and isinstance(capacidad, int):
            salones.append({"Salón": str(aula), "Edificio": str(bloque), "Capacidad": capacidad})

    # Cada generación se divide en grupos parejos de a lo más CUPO_GRUPO.
    grupos, materias = [], []
    for fila in wb["Generaciones"].iter_rows(min_row=4, values_only=True):
        clave = fila[1]
        if not clave or not isinstance(fila[3], int):
            continue
        for semestre, alumnos in enumerate(fila[3:11], 1):
            if not alumnos:
                continue
            if (clave, semestre) == ("ICC", 7):
                continue  # se reemplaza con el caso real (abajo)
            k = math.ceil(alumnos / CUPO_GRUPO)
            # Supuesto: semestres 1 a 4 en la mañana, 5 a 8 en la tarde.
            turno = "matutino" if semestre <= 4 else "vespertino"
            for j in range(k):
                grupos.append({"Carrera": clave, "Semestre": semestre, "Grupo": "ABCDEFGH"[j],
                               "Alumnos": alumnos // k + (1 if j < alumnos % k else 0), "Turno": turno})
            for m in range(1, MATERIAS_POR_SEMESTRE + 1):
                materias.append({"Carrera": clave, "Semestre": semestre,
                                 "Materia": MATERIAS[clave][semestre][m - 1], "Profesor": None,
                                 "Sesiones": 2, "Alumnos": None})

    # rng_nombres aparte para no alterar el reparto de materias ya generado.
    rng_nombres = random.Random(1115)
    usados = {p["Profesor"] for p in icc7()["profesores"]}
    profesores = []
    por_carrera: dict[str, list[dict]] = {}
    for m in materias:
        por_carrera.setdefault(m["Carrera"], []).append(m)
    for clave, lista in por_carrera.items():
        orden = list(lista)
        rng.shuffle(orden)
        for n in range(0, len(orden), SECCIONES_POR_PROFESOR):
            nombre = nombre_profesor(rng_nombres, usados)
            suyas = orden[n:n + SECCIONES_POR_PROFESOR]
            for m in suyas:
                m["Profesor"] = nombre
            # Supuesto: 1 de cada 4 profesores sólo puede de lunes a jueves.
            disponible = "Lun-Jue" if rng.random() < 0.25 else None
            turnos = sorted({"matutino" if m["Semestre"] <= 4 else "vespertino" for m in suyas})
            profesores.append({"Profesor": nombre, "Disponible": disponible,
                               "Prefiere": preferencia(rng_nombres, turnos, disponible)})

    real = icc7()
    grupos += real["grupos"]
    materias += real["materias"]
    profesores += real["profesores"]
    orden_grupo = lambda f: (f["Carrera"], f["Semestre"], f.get("Grupo") or "")  # noqa: E731
    grupos.sort(key=orden_grupo)
    materias.sort(key=lambda f: (f["Carrera"], f["Semestre"]))

    return {
        "formato": FORMATO,
        "general": {"nombre": "CETYS Tijuana, Universidad", "dias": 5},
        "bloques": BLOQUES,
        "salones": salones,
        "profesores": profesores,
        "grupos": grupos,
        "materias": materias,
    }


def config_vacia() -> dict:
    return {"formato": FORMATO,
            "general": {"nombre": "Nueva configuración", "dias": 5},
            "bloques": BLOQUES}


if __name__ == "__main__":
    DESTINO.mkdir(exist_ok=True)
    for nombre, config in (("icc7_ejemplo.json", config_icc7()),
                           ("cetys_tijuana_aprox.json", config_cetys()),
                           ("vacia.json", config_vacia())):
        guardar_configuracion(normalizar(config), DESTINO / nombre)
        c = normalizar(config)
        print(f"{nombre}: {len(c['grupos'])} grupos, {len(c['materias'])} materias, "
              f"{len(c['profesores'])} profesores, {len(c['salones'])} salones")
