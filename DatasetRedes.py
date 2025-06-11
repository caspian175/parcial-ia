# Dependencias Necesarias:
# pip install pandas seaborn matplotlib requests psutil

# Se Requiere pip, Y Ejecutar El Comando Arriba Para La Ejecucion De Este Codigo.

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

import subprocess
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import requests
import psutil
import re
import time
import os
import tkinter as tk
from tkinter import messagebox

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
                        try:
                            port = int(port)
                            pid = int(pid)
                            connections.append({
                                "Protocolo": protocolo,
                                "IP Remota": ip,
                                "Puerto Remoto": port,
                                "Estado": estado,
                                "PID": pid,
                                "Proceso": process_name
                            })
                        except:
                            continue
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
        time.sleep(0.5)  # evitar bloqueo por rate limit

    geo_df = pd.DataFrame.from_dict(geo_data, orient='index')
    geo_df.index.name = 'IP Remota'
    return df.join(geo_df, on='IP Remota')

# ========================
# Paso 4: Mostrar estadísticas básicas
# ========================

def mostrar_estadisticas(df):
    media = df['Puerto Remoto'].mean()
    mediana = df['Puerto Remoto'].median()
    moda = df['Puerto Remoto'].mode()[0]
    desviacion = df['Puerto Remoto'].std()

    estadisticas = f"""
    📊 Estadísticas del Puerto Remoto

    Media: {media:.2f}
    Mediana: {mediana:.2f}
    Moda: {moda}
    Desviación estándar: {desviacion:.2f}
    """

    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("🐾 Estadísticas Básicas", estadisticas)
    root.destroy()

# ========================
# Paso 5: Mostrar correlación
# ========================

def mostrar_correlacion(df):
    df['ProtocoloNum'] = df['Protocolo'].map({'TCP': 1, 'UDP': 2})
    df['EstadoNum'] = df['Estado'].astype('category').cat.codes
    df['ProcesoID'] = df['Proceso'].astype('category').cat.codes

    correlacion = df[['Puerto Remoto', 'PID', 'ProtocoloNum', 'EstadoNum', 'ProcesoID']].corr()
    print("\n📌 Matriz de correlación:")
    print(correlacion)

    sns.heatmap(correlacion, annot=True, cmap="coolwarm")
    plt.title("💻 Matriz de correlación")
    plt.show()

# ========================
# Paso 6: Abrir CSV automáticamente
# ========================

def abrir_csv(path):
    print(f"📂 Abriendo el archivo: {path}")
    os.startfile(path)

# ========================
# Paso 7: Ejecutar Todo
# ========================

def main():
    lines = get_netstat_output()
    df = parse_netstat(lines)
    if df.empty:
        print("😿 No se encontraron conexiones activas.")
        return

    df = geolocalizar_ips(df)
    file_path = "conexiones_con_geolocalizacion.csv"
    df.to_csv(file_path, index=False)
    print(f"✅ Dataset guardado como '{file_path}'")

    abrir_csv(file_path)
    mostrar_estadisticas(df)
    mostrar_correlacion(df)

main()
