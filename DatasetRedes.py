# Dependencias Necesarias:
# pip install pandas seaborn matplotlib requests psutil

# Ernesto Morán (4-828-1810)
# Aurelio Parra (8-1024-554)

import subprocess
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import requests
import psutil
import re
import time

# ========================
# Paso 1: Capturar conexiones con netstat
# ========================

def get_netstat_output():
    print("⌛ Obteniendo conexiones activas (netstat)...")
    result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)
    return result.stdout.splitlines()

# ========================
# Paso 2: Parsear resultados
# ========================

def parse_netstat(lines):
    connections = []
    for line in lines:
        if line.startswith("  TCP") or line.startswith("  UDP"):
            parts = re.split(r"\s+", line.strip())
            if len(parts) >= 5:
                protocolo = parts[0]
                local = parts[1]
                remote = parts[2]
                estado = parts[3] if protocolo == "TCP" else "ESTABLISHED"
                pid = parts[4] if protocolo == "TCP" else parts[3]

                if ":" in remote:
                    ip, port = remote.rsplit(":", 1)
                    if ip != "0.0.0.0" and ip != "[::]":
                        try:
                            process_name = psutil.Process(int(pid)).name()
                        except:
                            process_name = "Desconocido"
                        connections.append({
                            "Protocolo": protocolo,
                            "IP Remota": ip,
                            "Puerto Remoto": int(port),
                            "Estado": estado,
                            "PID": int(pid),
                            "Proceso": process_name
                        })
    return pd.DataFrame(connections)

# ========================
# Paso 3: Geolocalización IP (ip-api.com)
# ========================

def geolocalizar_ips(df):
    print("🌍 Obteniendo geolocalización de IPs únicas...")
    unique_ips = df['IP Remota'].unique()
    geo_data = {}

    for ip in unique_ips:
        try:
            response = requests.get(f"http://ip-api.com/json/{ip}").json()
            if response['status'] == 'success':
                geo_data[ip] = {
                    'País': response.get('country', 'N/A'),
                    'Región': response.get('regionName', 'N/A'),
                    'Ciudad': response.get('city', 'N/A'),
                    'Org': response.get('org', 'N/A'),
                    'Latitud': response.get('lat', None),
                    'Longitud': response.get('lon', None)
                }
        except:
            geo_data[ip] = {'País': 'N/A', 'Región': 'N/A', 'Ciudad': 'N/A', 'Org': 'N/A', 'Latitud': None, 'Longitud': None}
        time.sleep(0.5)  # para evitar bloqueo por rate limit

    geo_df = pd.DataFrame.from_dict(geo_data, orient='index')
    geo_df.index.name = 'IP Remota'
    return df.join(geo_df, on='IP Remota')

# ========================
# Paso 4: Análisis estadístico y correlación
# ========================

def analizar(df):
    print("📊 Estadísticas básicas:")
    print("Media:", df['Puerto Remoto'].mean())
    print("Mediana:", df['Puerto Remoto'].median())
    print("Moda:", df['Puerto Remoto'].mode()[0])
    print("Desviación estándar:", df['Puerto Remoto'].std())

    print("\n📌 Matriz de correlación:")
    df['ProtocoloNum'] = df['Protocolo'].map({'TCP': 1, 'UDP': 2})
    df['EstadoNum'] = df['Estado'].astype('category').cat.codes
    df['ProcesoID'] = df['Proceso'].astype('category').cat.codes

    correlacion = df[['Puerto Remoto', 'PID', 'ProtocoloNum', 'EstadoNum', 'ProcesoID']].corr()
    print(correlacion)

    sns.heatmap(correlacion, annot=True, cmap="coolwarm")
    plt.title("💻 Matriz de correlación")
    plt.show()

# ========================
# Paso 5: Ejecutar todo y guardar
# ========================

def main():
    lines = get_netstat_output()
    df = parse_netstat(lines)
    if df.empty:
        print("No se encontraron conexiones activas.")
        return

    df = geolocalizar_ips(df)
    df.to_csv("conexiones_con_geolocalizacion.csv", index=False)
    print("✅ Dataset guardado como 'conexiones_con_geolocalizacion.csv'")
    analizar(df)

main()
