import sys

from horarios.configuracion import cargar_configuracion
from horarios.entrada_excel import crear_plantilla

if __name__ == "__main__":
    origen, destino = sys.argv[1], sys.argv[2]
    crear_plantilla(cargar_configuracion(origen), destino)
    print(f"Plantilla creada: {destino}")
