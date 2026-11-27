# Organizador de horarios con algoritmos genéticos

Genera horarios universitarios sin empalmes con un algoritmo genético. El caso de estudio es CETYS Tijuana, con datos aproximados.

## Cómo usarlo
```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```
Se abre en el navegador (http://localhost:8501).

1. **Configuración inicial:** edita salones, profesores, grupos y materias. Puedes descargar la configuración en JSON o en Excel.
2. **Generar horario:** elige las carreras, genera el horario y consúltalo por grupo, profesor o salón. Puedes exportarlo en CSV.

## Pruebas
```bash
python -m pytest -q
```

## Experimentos
Corre una variante de reparación (`ninguna`, `primer_hueco` o `guiada`) con varias semillas. Los resultados se guardan en `resultados/`.
```bash
python experimento.py guiada --semillas 1-30
```

## Estructura
| Carpeta / archivo | Contenido |
|---|---|
| `app.py` | Interfaz en Streamlit |
| `horarios/` | Modelo, evaluación, validador, operadores y algoritmo genético |
| `configuraciones/` | Configuraciones de ejemplo (la app usa `cetys_tijuana_aprox.json`) |
| `instancias/` | Instancias sintéticas y el caso real de ICC 7.º semestre |
| `tests/` | Pruebas |
| `linea_base.json`, `experimento.py` | Configuración congelada del algoritmo y script de experimentos |
| `crear_configuraciones.py`, `crear_plantilla.py`, `generar_referencia.py` | Scripts que regeneran los datos de ejemplo |
