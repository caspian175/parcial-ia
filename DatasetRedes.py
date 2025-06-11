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
def get_netstat_output():
    result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)
    return result.stdout.splitlines()

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
                    if ip not in ["0.0.0.0", "[::]", "::", ""]:
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
def geolocalizar_ips(df):
    unique_ips = df['IP Remota'].unique()
    geo_data = {}

    for ip in unique_ips:
        if ip.startswith("127.") or ip in ["::1"]:
            geo_data[ip] = {'País': 'LOCAL', 'Región': 'LOCAL', 'Ciudad': 'LOCAL', 'Org': 'LOCAL', 'Latitud': None, 'Longitud': None}
            continue

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
            else:
                geo_data[ip] = {'País': 'N/A', 'Región': 'N/A', 'Ciudad': 'N/A', 'Org': 'N/A', 'Latitud': None, 'Longitud': None}
        except:
            geo_data[ip] = {'País': 'N/A', 'Región': 'N/A', 'Ciudad': 'N/A', 'Org': 'N/A', 'Latitud': None, 'Longitud': None}
        time.sleep(0.5)

    geo_df = pd.DataFrame.from_dict(geo_data, orient='index')
    geo_df.index.name = 'IP Remota'
    return df.join(geo_df, on='IP Remota')

# ========================
def mostrar_estadisticas(df):
    media = df['Puerto Remoto'].mean()
    mediana = df['Puerto Remoto'].median()
    moda = df['Puerto Remoto'].mode()[0]
    desviacion = df['Puerto Remoto'].std()

    texto = f"""
    📊 Estadísticas del Puerto Remoto

    Media: {media:.2f}
    Mediana: {mediana:.2f}
    Moda: {moda}
    Desviación estándar: {desviacion:.2f}
    """

    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("🐾 Estadísticas Básicas", texto)
    root.destroy()

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

def abrir_csv(path):
    print(f"📂 Abriendo el archivo: {path}")
    os.startfile(path)

# ========================
def main():
    todas_las_conexiones = pd.DataFrame()

    print("🐱 El monitoreo ha comenzado, presiona Ctrl + C para detenerlo... UwU")
    try:
        while True:
            lines = get_netstat_output()
            df = parse_netstat(lines)
            if not df.empty:
                df = geolocalizar_ips(df)
                todas_las_conexiones = pd.concat([todas_las_conexiones, df], ignore_index=True)
            time.sleep(5)  # puedes ajustar esto si quieres
    except KeyboardInterrupt:
        print("\n🚨 Ctrl + C detectado, terminando captura...")

    if todas_las_conexiones.empty:
        print("😿 No se recolectó ninguna conexión activa.")
        return

    file_path = "conexiones_monitorizadas.csv"
    todas_las_conexiones.to_csv(file_path, index=False)
    print(f"✅ Dataset final guardado como '{file_path}'")

    abrir_csv(file_path)
    mostrar_estadisticas(todas_las_conexiones)
    mostrar_correlacion(todas_las_conexiones)

main()
