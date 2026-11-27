# horarios: organizador de horarios con algoritmos genéticos

Estado: **fases 1 a 5 del Avance 2** + configuración en la app con varias carreras: modelo (con turnos), carga de instancias desde JSON o Excel, dominios, detección de inviabilidad, generador, evaluador, validador, GA base e interfaz en Streamlit. Falta la fase 6 (mediciones y reporte).

## Configuración inicial
Se edita dentro de la app (pestaña 1), en tablas: General y bloques, Salones, Profesores, Grupos (carreras y generaciones) y Materias. La app trabaja con CETYS Tijuana (`configuraciones/cetys_tijuana_aprox.json`, datos aproximados). La configuración se puede descargar como Excel (`plantilla_configuracion.xlsx`, mismas tablas) o JSON. Guía completa: `plan/09-guia-de-uso.md`.

## Interfaz
```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```
Se abre en el navegador (http://localhost:8501). Pestaña 1: cargar y editar la configuración (con filtro por carrera) y descargarla en JSON o Excel. Pestaña 2: elegir carreras, generar el horario y verlo por grupo, profesor o salón, con convergencia, validación y CSV.

## Uso desde Python
```python
from horarios.entrada import cargar_instancia
from horarios.ga import ejecutar, ConfiguracionGA

inst = cargar_instancia("instancias/sint_30.json")
r = ejecutar(inst, ConfiguracionGA(semilla=1))
print(r.evaluacion, r.reporte.factible, r.motivo_fin)
```

## Requisitos y pruebas
```bash
python3 -m pip install -r requirements.txt
python3 -m pytest -q
```
Probado con Python 3.13 y pytest 9.1.

## Estructura
| Archivo | Responsabilidad |
|---|---|
| `horarios/modelo.py` | Entidades inmutables: Salon, Profesor, Seccion, Evento, Instancia |
| `horarios/entrada.py` | Carga de JSON con validación (reporta todos los errores juntos) |
| `horarios/configuracion.py` | Configuración en tablas (carreras, grupos, materias…) → instancia; disponibilidad en texto |
| `horarios/entrada_excel.py` | Escribe y lee la configuración en Excel (mismas tablas que la app) |
| `crear_configuraciones.py` | Genera `configuraciones/*.json` (ICC 7.º, CETYS aproximado desde `../datos/`, vacía) |
| `crear_plantilla.py` | Genera la plantilla de Excel a partir de una configuración JSON |
| `horarios/dominios.py` | Valores permitidos por gen (capacidad y disponibilidad) y condiciones necesarias de inviabilidad |
| `horarios/evaluacion.py` | Función objetivo: V(x) por componente, 3 penalizaciones blandas (huecos, preferencias, carga diaria), clave lexicográfica |
| `horarios/validador.py` | Comprobación independiente que certifica la factibilidad |
| `horarios/operadores.py` | Inicialización, torneo, cruce por tramos, mutación, reparación primer hueco |
| `horarios/ga.py` | Motor del GA base, configuración, registro por generación |
| `horarios/salida.py` | Tablas semanales por grupo/profesor/salón y exportación CSV |
| `app.py` | Interfaz Streamlit |
| `horarios/generador.py` | Instancias sintéticas parametrizables y reproducibles |
| `generar_referencia.py` | Regenera `instancias/sint_10/30/100.json` |
| `instancias/ejemplo_minimo.json` | El ejemplo A/B de `plan/01-analisis-inicial.md` §4.3 |
| `instancias/icc7_real.json` | Caso real: ICC 7.º semestre, 2 grupos, turno vespertino (profesores inventados) |
| `instancias/icc7_real_grupo1*.json` | Sólo el grupo 1 y su horario actual, para evaluarlo |
| `instancias/icc7_ficticio.json` | Caso de prueba anterior (datos inventados) |
| `tests/` | Pruebas |

Las decisiones de diseño se explican en `plan/03-fase1-explicacion.md` a `plan/07-fase5-explicacion.md` y `plan/08-configuracion-inicial.md`.
