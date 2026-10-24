"""Interfaz en Streamlit. Ejecutar: python -m streamlit run app.py"""

import io
import json
from dataclasses import asdict
from pathlib import Path

import pandas as pd
import streamlit as st

from horarios.configuracion import COLUMNAS, carreras, cargar_configuracion, construir_instancia, normalizar, _texto
from horarios.dominios import calcular_dominios, diagnosticar_inviabilidad
from horarios.entrada import ErrorInstancia, instancia_desde_dict
from horarios.entrada_excel import AYUDA, crear_plantilla
from horarios.ga import ConfiguracionGA, InstanciaInviable, ejecutar
from horarios.generador import ocupacion
from horarios.salida import horario_csv, tabla_semanal

AQUI = Path(__file__).parent
CONFIG_CETYS = AQUI / "configuraciones" / "cetys_tijuana_aprox.json"
NOMBRES_VISTA = {"bloque_curricular": "Grupo", "profesor": "Profesor", "salon": "Salón"}
MAX_MENSAJES = 20

st.set_page_config(page_title="Organizador de horarios", layout="wide")
ss = st.session_state


def cargar(config: dict) -> None:
    ss.config = normalizar(config)
    ss.version = ss.get("version", 0) + 1
    ss.vista_carrera = 0
    ss.actual = {}
    ss.pop("resultado", None)


if "config" not in ss:
    cargar(cargar_configuracion(CONFIG_CETYS))

with st.sidebar:
    st.header("Datos")
    if st.button("Restaurar los datos originales de CETYS", width="stretch",
                 help="Descarta los cambios hechos en la pestaña 1."):
        cargar(cargar_configuracion(CONFIG_CETYS))
        st.rerun()


def a_tabla(tabla: str, filas: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(filas, columns=COLUMNAS[tabla])
    for col in ("Semestre", "Alumnos", "Capacidad", "Sesiones"):
        if col in df:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].fillna("").astype(str)
    return df


def de_tabla(df: pd.DataFrame) -> list[dict]:
    return df.astype(object).where(df.notna(), None).to_dict("records")


def columnas_editor(tabla: str, turnos: list[str]) -> dict:
    cc = st.column_config

    def columna(c):
        ayuda = AYUDA[(tabla, c)]
        if c in ("Capacidad", "Semestre", "Alumnos", "Sesiones"):
            return cc.NumberColumn(c, help=ayuda, min_value=1, max_value=7 if c == "Sesiones" else None,
                                   step=1, format="%d")
        if c == "Turno" and tabla == "grupos":
            return cc.SelectboxColumn(c, help=ayuda, options=turnos)
        return cc.TextColumn(c, help=ayuda, width="large" if c in ("Disponible", "Materia") else None)

    return {c: columna(c) for c in COLUMNAS[tabla]}


def editor(tabla: str, turnos: list[str], carrera: str | None = None) -> list[dict]:
    """Muestra la tabla (o las filas de una carrera) y devuelve la tabla completa."""
    base = ss.config[tabla]
    dentro = lambda f: carrera is None or _texto(f["Carrera"]) == carrera
    editado = st.data_editor(
        a_tabla(tabla, [f for f in base if dentro(f)]),
        key=f"ed_{tabla}_{ss.version}_{ss.vista_carrera}", num_rows="dynamic", hide_index=True,
        width="stretch", column_config=columnas_editor(tabla, turnos),
    )
    filas = de_tabla(editado)
    if carrera is not None:
        for f in filas:
            f["Carrera"] = f["Carrera"] or carrera
    return [f for f in base if not dentro(f)] + filas


def cambiar_vista_carrera() -> None:
    for tabla, filas in ss.actual.items():
        ss.config[tabla] = sorted(filas, key=lambda f: _texto(f["Carrera"])) if "Carrera" in COLUMNAS[tabla] else filas
    ss.vista_carrera += 1


@st.cache_data(max_entries=4, show_spinner=False)
def excel_de(config_json: str) -> bytes:
    libro = io.BytesIO()
    crear_plantilla(json.loads(config_json), libro)
    return libro.getvalue()


st.title("Organizador de horarios con algoritmos genéticos")
tab_conf, tab_gen = st.tabs(["1. Configuración inicial", "2. Generar horario"])
v = ss.version

with tab_conf:
    opciones_carrera = carreras(ss.config)
    vista = "Todas las carreras"
    if len(opciones_carrera) > 1:
        vista = st.selectbox("Carrera a mostrar en Grupos y Materias", ["Todas las carreras", *opciones_carrera],
                             key=f"vista_{v}", on_change=cambiar_vista_carrera,
                             help="Para trabajar una carrera a la vez. Las filas nuevas toman esta carrera.")
    filtro = None if vista == "Todas las carreras" else vista
    p_gen, p_sal, p_prof, p_gru, p_mat = st.tabs(
        ["General y bloques", "Salones", "Profesores", "Grupos (carreras y generaciones)", "Materias (plan de estudios)"])
    actual = {}

    with p_gen:
        g = ss.config["general"]
        c1, c2, _ = st.columns([2, 1, 2])
        general = {
            "nombre": c1.text_input("Nombre de la configuración", g.get("nombre") or "", key=f"g_nombre_{v}"),
            "dias": c2.number_input("Días de clase", 1, 7, int(g.get("dias") or 5), key=f"g_dias_{v}",
                                    help="5 = lunes a viernes; 6 = lunes a sábado."),
        }
        st.markdown("**Bloques del día.** Un renglón por bloque de clase, en orden. El turno agrupa bloques: "
                    "un grupo vespertino sólo puede usar bloques vespertinos. Las horas sirven para mostrar el "
                    "horario y para capturar disponibilidades como `16:00-22:00`.")
        actual["bloques"] = editor("bloques", [])
    turnos = sorted({_texto(f["Turno"]) for f in actual["bloques"]} - {""})

    with p_sal:
        st.markdown("**Salones** disponibles y su **capacidad**. Una clase sólo se asigna a salones donde caben sus "
                    "alumnos. Ningún salón se reserva para un grupo: el algoritmo los reparte.")
        actual["salones"] = editor("salones", turnos)

    with p_prof:
        st.markdown("**Disponible** es una regla dura: nunca se pone una clase fuera de ella. **Prefiere** es "
                    "blanda: se intenta respetar. Vacío = siempre / sin preferencia.")
        st.markdown("Se escribe como texto: `vespertino` · `Lun-Vie 16:00-20:00` · `Lun,Mié 4-6; Vie todo` "
                    "(días opcionales; luego un turno, números de bloque, horas o `todo`; separa partes con `;`). "
                    "Los profesores que aparecen en Materias y no aquí se toman como siempre disponibles.")
        actual["profesores"] = editor("profesores", turnos)

    with p_gru:
        st.markdown("**Grupos** de cada carrera y semestre (generación). Cada grupo lleva todas las materias de su "
                    "semestre y sus clases no se pueden empalmar. Si una generación no cabe en un salón, divídela "
                    "en varios grupos (A, B…).")
    with p_mat:
        st.markdown("**Materias** de cada semestre de cada carrera. Cada materia se abre una vez por cada grupo "
                    "de esa carrera y semestre. Varios profesores separados por coma se reparten entre los grupos "
                    "en orden. **Alumnos** vacío = los del grupo.")
    with p_gru:
        actual["grupos"] = editor("grupos", turnos, filtro)
    with p_mat:
        actual["materias"] = editor("materias", turnos, filtro)

    ss.actual = actual
    config_actual = normalizar({**ss.config, "general": general, **actual})

    st.divider()
    c1, c2, _ = st.columns([1, 1, 2])
    c1.download_button("Descargar configuración (JSON)",
                       json.dumps(config_actual, ensure_ascii=False, indent=1),
                       file_name="configuracion.json", mime="application/json", width="stretch")
    c2.download_button("Descargar como Excel", excel_de(json.dumps(config_actual, ensure_ascii=False)),
                       file_name="configuracion.xlsx", width="stretch")


with st.sidebar:
    st.header("Algoritmo genético")
    c1, c2 = st.columns(2)
    poblacion = c1.number_input("Población", 10, 1000, 100, 10)
    presupuesto = c2.number_input("Evaluaciones máx.", 500, 500_000, 20_000, 500)
    with st.expander("Más parámetros"):
        k = st.number_input("Tamaño de torneo", 2, 10, 2)
        elitismo = st.number_input("Élite", 0, 20, 2)
        p_cruce = st.slider("Probabilidad de cruce", 0.0, 1.0, 0.9, 0.05)
        auto_pm = st.checkbox("Mutación automática (1 / nº de sesiones)", value=True)
        p_mut = None if auto_pm else st.slider("Probabilidad de mutación por gen", 0.0, 0.5, 0.05, 0.01)
        reparacion = st.selectbox("Reparación", ["primer_hueco", "ninguna"],
                                  format_func={"primer_hueco": "Primer hueco (PF01)", "ninguna": "Sin reparación"}.get)
        semilla = st.number_input("Semilla del GA", 0, 10_000, 1)
    with st.expander("Pesos de los criterios blandos"):
        st.caption("Costo de cada ocurrencia (1 = lo que cuesta una hora muerta).")
        w_huecos = st.slider("Hora muerta", 0.0, 1.0, 1.0, 0.05)
        w_pref = st.slider("Clase fuera de la preferencia del profesor", 0.0, 1.0, 1.0, 0.05)
        w_carga = st.slider("Clase por encima del reparto parejo por día", 0.0, 1.0, 1.0, 0.05)
        w_dia = st.slider("Dos sesiones de una materia el mismo día", 0.0, 1.0, 0.1, 0.05)


def parar(mensaje: str | None = None) -> None:
    if mensaje:
        st.info(mensaje)
    st.stop()


with tab_gen:
    todas = carreras(config_actual)
    elegidas = todas
    if len(todas) > 1:
        elegidas = st.multiselect("Carreras a programar", todas, default=todas, key=f"carreras_{v}",
                                  help="Comparten salones y profesores. Puedes programar una carrera, varias o todas.")
        if not elegidas:
            parar("Elige al menos una carrera.")
    try:
        datos, avisos = construir_instancia(config_actual, None if elegidas == todas else elegidas)
        inst = instancia_desde_dict(datos)
    except ErrorInstancia as exc:
        st.error("La configuración tiene errores. Corrígelos en la pestaña 1:")
        st.markdown("\n".join(f"- {e}" for e in exc.errores))
        parar()
    for a in avisos:
        st.warning(a)

    c = st.columns(6)
    c[0].metric("Carreras", len({s.carrera for s in inst.secciones}))
    c[1].metric("Grupos", len(inst.bloques_curriculares()))
    c[2].metric("Clases (materia × grupo)", len(inst.secciones))
    c[3].metric("Sesiones a asignar", len(inst.eventos))
    c[4].metric("Profesores · Salones", f"{len(inst.profesores)} · {len(inst.salones)}")
    c[5].metric("Ocupación de salones", f"{ocupacion(datos):.0%}",
                help="Sesiones / (salones × bloques de la semana). Más alta = más difícil.")

    motivos = diagnosticar_inviabilidad(inst, calcular_dominios(inst))
    if motivos:
        st.error("Con estos datos no existe ningún horario posible:")
        st.markdown("\n".join(f"- {m}" for m in motivos))
        parar()

    correr = st.button("Generar horario", type="primary")
    firma = json.dumps(datos, sort_keys=True, ensure_ascii=False)

    if correr:
        if w_huecos + w_pref + w_carga + w_dia == 0:
            parar("Al menos un criterio blando debe tener peso mayor que cero.")
        try:
            cfg = ConfiguracionGA(tam_poblacion=poblacion, k_torneo=min(k, poblacion), p_cruce=p_cruce,
                                  p_mutacion=p_mut, elitismo=min(elitismo, poblacion - 1),
                                  max_evaluaciones=max(presupuesto, poblacion), reparacion=reparacion,
                                  pesos={"huecos": w_huecos, "preferencias": w_pref,
                                         "carga_diaria": w_carga, "mismo_dia": w_dia},
                                  semilla=semilla)
        except ValueError as exc:
            parar(str(exc))
        barra = st.progress(0.0, text="Evolucionando…")

        def progreso(reg):
            barra.progress(min(reg.evaluaciones / presupuesto, 1.0),
                           text=f"Generación {reg.generacion} · V = {reg.mejor_v} · S = {reg.mejor_s:.3f}")

        try:
            ss.resultado = (firma, inst, ejecutar(inst, cfg, progreso))
        except InstanciaInviable as exc:
            parar(str(exc))
        barra.empty()

    if "resultado" not in ss:
        parar("Revisa el resumen y pulsa **Generar horario**.")

    firma_r, inst, r = ss.resultado
    if firma_r != firma:
        st.warning("La configuración cambió desde que se generó este horario. Pulsa **Generar horario** de nuevo.")
    ev = r.evaluacion

    if r.reporte.factible:
        st.success("Horario sin empalmes, certificado por el validador independiente.")
    else:
        st.error(f"El mejor horario encontrado todavía tiene {r.reporte.total} violaciones de restricciones "
                 "duras. Cuáles son (también en la pestaña Validación):\n\n"
                 + "\n".join(f"- {m}" for m in r.reporte.mensajes[:MAX_MENSAJES])
                 + (f"\n- … y {len(r.reporte.mensajes) - MAX_MENSAJES} más"
                    if len(r.reporte.mensajes) > MAX_MENSAJES else ""))

    c = st.columns(5)
    c[0].metric("Violaciones duras (V)", ev.v)
    c[1].metric("Penalización blanda (S)", f"{ev.s:.3f}", help="0 = perfecto; 1 = peor posible")
    c[2].metric("Horas muertas", ev.huecos, help="En bloques, sumando todos los grupos y días")
    pref_total = sum(1 for e in inst.eventos if inst.profesores[e.seccion.profesor].preferidos is not None)
    c[3].metric("Sesiones en horario preferido",
                f"{1 - ev.fuera_preferencia / pref_total:.0%}" if pref_total else "sin datos")
    c[4].metric("Exceso de clases por día", ev.exceso_diario,
                help="Por grupo y día, sesiones que exceden techo(sesiones del grupo / días)")
    st.caption(f"Materias con sus dos sesiones el mismo día (penalización leve): {ev.mismo_dia}. "
               f"{r.evaluaciones:,} evaluaciones en {r.segundos:.1f} s. Terminó por: {r.motivo_fin}. "
               + (f"Primer horario sin empalmes tras {r.evaluaciones_hasta_factible:,} evaluaciones."
                  if r.evaluaciones_hasta_factible else "No se alcanzó un horario sin empalmes."))

    t_horario, t_conv, t_valid = st.tabs(["Horario", "Convergencia", "Validación"])

    with t_horario:
        c1, c2, c3 = st.columns([1, 1, 2])
        vista_h = c1.radio("Ver por", list(NOMBRES_VISTA), format_func=NOMBRES_VISTA.get)
        if vista_h == "bloque_curricular":
            carreras_r = sorted({s.carrera for s in inst.secciones})
            carrera_h = c2.selectbox("Carrera", carreras_r) if len(carreras_r) > 1 else None
            opciones = sorted({s.bloque_curricular for s in inst.secciones
                               if carrera_h is None or s.carrera == carrera_h})
        elif vista_h == "profesor":
            opciones = sorted(inst.profesores)
        else:
            opciones = [s.id for s in inst.salones]
        clave = c3.selectbox(NOMBRES_VISTA[vista_h], opciones)
        tabla = tabla_semanal(inst, r.mejor, vista_h, clave)
        st.table(pd.DataFrame(tabla["celdas"], index=tabla["filas"], columns=tabla["columnas"]))
        st.download_button("Descargar horario completo (CSV)", horario_csv(inst, r.mejor),
                           file_name="horario.csv", mime="text/csv")

    with t_conv:
        hist = pd.DataFrame([asdict(h) for h in r.historial]).set_index("evaluaciones")
        st.subheader("Violaciones duras del mejor horario (V)")
        st.line_chart(hist["mejor_v"], x_label="Evaluaciones", y_label="V")
        st.caption("Empalmes del mejor horario encontrado hasta ese momento. Debe bajar hasta 0; si se queda "
                   "plana arriba de 0, el algoritmo no logró quitar ese empalme.")
        st.subheader("Penalización blanda del mejor horario (S)")
        st.line_chart(hist["mejor_s"], x_label="Evaluaciones", y_label="S")
        st.caption("Qué tan lejos está el mejor horario de lo ideal (horas muertas, preferencias, reparto, mismo "
                   "día): 0 = perfecto. Sólo baja o se queda igual; los escalones son mejoras.")
        st.subheader("Diversidad de la población")
        st.line_chart(hist["diversidad"], x_label="Evaluaciones", y_label="Genes distintos al mejor")
        st.caption("Fracción promedio de sesiones que cada horario de la población tiene en un lugar distinto al "
                   "mejor. Alta = la población todavía explora; cerca de 0 = todos se parecen al mejor (convergió).")
        with st.expander("Tabla por generación"):
            st.caption("Una fila por generación. mejor_v / mejor_s: el mejor horario hasta ese momento; media_v: "
                       "empalmes promedio de la población; factibles: fracción de la población sin empalmes; "
                       "diversidad: la de la gráfica; segundos: tiempo acumulado.")
            st.dataframe(hist, width="stretch")

    with t_valid:
        rep = r.reporte
        st.table(pd.DataFrame({
            "Restricción": ["Salón ocupado dos veces", "Profesor en dos clases", "Grupo con dos clases",
                            "Capacidad del salón", "Disponibilidad del profesor", "Fuera del turno"],
            "Violaciones": [rep.salon, rep.profesor, rep.curricular, rep.capacidad,
                            rep.disponibilidad, rep.turno],
        }))
        for m in rep.mensajes:
            st.write(f"- {m}")
        if r.fallos_reparacion:
            st.caption(f"La reparación no encontró hueco {r.fallos_reparacion} veces durante la ejecución.")
