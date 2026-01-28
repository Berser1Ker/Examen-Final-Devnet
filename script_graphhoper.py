import os
import sys
import requests
from typing import Tuple

API_KEY = os.getenv("GRAPHHOPER_IPLACEX_KEY")


def km_to_miles(km: float) -> float:
    return km * 0.621371


def ms_to_hms(ms: float) -> Tuple[int, int, int]:
    total_sec = int(ms / 1000)
    h = total_sec // 3600
    m = (total_sec % 3600) // 60
    s = total_sec % 60
    return h, m, s


def geocode(query: str) -> Tuple[float, float]:
    """
    Convierte un texto de ubicación (ej: 'Santiago, Chile') en coordenadas lat/lng.
    """
    url = "https://graphhopper.com/api/1/geocode"
    params = {
        "q": query,
        "limit": 1,
        "locale": "es",
        "key": API_KEY
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()

    hits = data.get("hits", [])
    if not hits:
        raise ValueError(f"No se encontró la ciudad: {query}")

    p = hits[0]["point"]
    return p["lat"], p["lng"]


def route(lat1: float, lng1: float, lat2: float, lng2: float, vehicle: str) -> dict:
    url = "https://graphhopper.com/api/1/route"
    params = {
        "point": [f"{lat1},{lng1}", f"{lat2},{lng2}"],
        "vehicle": vehicle,
        "locale": "es",
        "instructions": "true",
        "calc_points": "true",       # ayuda a traer instrucciones/narrativa
        "points_encoded": "false",   # evita polyline codificado
        "key": API_KEY,
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def main():
    if not API_KEY:
        print("ERROR: No se encontró la API Key en GRAPHHOPER_IPLACEX_KEY")
        print('Ejemplo: export GRAPHHOPER_IPLACEX_KEY="TU_API_KEY"')
        sys.exit(1)

    print("=== GraphHopper: Distancia Chile ↔ Argentina ===")
    print("Escriba 'v' para salir en cualquier paso.\n")

    while True:
        origen = input("Ciudad de Origen: ").strip()
        if origen.lower() == "v":
            print("Saliendo del programa...")
            break

        destino = input("Ciudad de Destino: ").strip()
        if destino.lower() == "v":
            print("Saliendo del programa...")
            break

        print("\nMedio de transporte:")
        print("1) Auto")
        print("2) Bicicleta")
        print("3) A pie")
        opcion = input("Seleccione opción (1/2/3) o 'v' para salir: ").strip().lower()
        if opcion == "v":
            print("Saliendo del programa...")
            break

        vehiculos = {"1": "car", "2": "bike", "3": "foot"}
        if opcion not in vehiculos:
            print("Opción inválida. Intente nuevamente.\n")
            continue

        vehicle = vehiculos[opcion]

        try:
            # Recomendación: si el usuario no pone país, igual funcionará,
            # pero es mejor usar 'Santiago, Chile' / 'Mendoza, Argentina'.
            o_lat, o_lng = geocode(origen)
            d_lat, d_lng = geocode(destino)

            data = route(o_lat, o_lng, d_lat, d_lng, vehicle)

            if "paths" not in data or not data["paths"]:
                print("\nNo fue posible calcular la ruta. Respuesta API:")
                print(data)
                print("")
                continue

            path = data["paths"][0]

            dist_km = path.get("distance", 0) / 1000
            dist_mi = km_to_miles(dist_km)

            h, m, s = ms_to_hms(path.get("time", 0))

            print("\n--- Resultados ---")
            print(f"Distancia: {dist_km:.2f} km")
            print(f"Distancia: {dist_mi:.2f} millas")
            print(f"Duración:  {h}h {m}m {s}s")

            print("\n--- Narrativa del viaje ---")
            steps = path.get("instructions", [])
            if not steps:
                print("No se recibieron indicaciones.")
                print("Sugerencia: use ciudades más específicas, por ejemplo 'Santiago, Chile' o 'Mendoza, Argentina'.")
            else:
                for idx, step in enumerate(steps, start=1):
                    txt = step.get("text", "")
                    d_step_km = step.get("distance", 0) / 1000
                    print(f"{idx}) {txt} | {d_step_km:.2f} km")

            print("\n")

        except Exception as e:
            print(f"\nError: {e}")
            print("Sugerencia: pruebe con 'Santiago, Chile' y 'Mendoza, Argentina'.\n")


if __name__ == "__main__":
    main()
