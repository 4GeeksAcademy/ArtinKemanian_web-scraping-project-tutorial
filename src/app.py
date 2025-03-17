import os
from bs4 import BeautifulSoup
import sqlite3
import requests
import time
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

url = "https://companies-market-cap-copy.vercel.app/index.html"

response = requests.get(url)
if response.status_code != 200:
    raise Exception(f"Error al acceder a la página: {response.status_code}")

html_content = response.text

soup = BeautifulSoup(html_content, "html.parser")

table = soup.find("table")

filas = table.find_all("tr")

datos = []
for filas in filas[1:]:  # Saltar la fila de encabezado
    cols = filas.find_all("td")
    fecha = cols[0].text.strip()
    ingresos = cols[1].text.strip()
    datos.append([fecha, ingresos])

df = pd.DataFrame(datos, columns=["Fecha", "Ingresos"])

df = df.sort_values("Fecha")

def convertir_ingresos(valor):
    if "B" in valor:
        editar_valor = float(valor.replace("B", "").replace("$", "").replace(",", ""))
        return editar_valor

df["Ingresos"] = df["Ingresos"].apply(convertir_ingresos)

conn = sqlite3.connect("tesla_revenues.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS ingresos (
    fecha TEXT,
    ingresos REAL
)
""")

for index, fila in df.iterrows():
    cursor.execute("INSERT INTO ingresos (fecha, ingresos) VALUES (?, ?)", (fila["Fecha"], fila["Ingresos"]))

conn.commit()
conn.close()

plt.figure(figsize=(10, 6))
plt.plot(df["Fecha"], df["Ingresos"], marker='o', label="Ingresos")
plt.title("Ingresos anuales de Tesla")
plt.xlabel("Fecha")
plt.ylabel("Ingresos en billones(USD)")
plt.xticks(rotation=45)
plt.legend()
plt.grid(True)

plt.savefig("plot_ingresos.png")
plt.show()

url = "https://companies-market-cap-copy.vercel.app/earnings.html"

response = requests.get(url)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

table = soup.find("table", {"class": "table"})
filas = table.find_all("tr")[1:]

datos = []
for fila in filas:
    cols = fila.find_all("td")
    fecha = cols[0].text.strip()
    ganancias = cols[1].text.strip()
    datos.append({"Año": fecha, "Ganancias": ganancias})

df = pd.DataFrame(datos)

def convertir_ganancias(valor):
    try:
        valor = valor.replace(",", "").replace("$", "").strip()
        if "Billion" in valor: 
            return float(valor.replace("Billion", "")) * 1_000_000_000
        elif "Million" in valor:
            return float(valor.replace("Million", "")) * 1_000_000_000
        elif "M" in valor:  
            return float(valor.replace("M", "")) * 1_000_000
        elif "B" in valor:
            return float(valor.replace("B", "")) * 1_000_000_000
        else:
            return float(valor)
    except ValueError:
        print(f"Advertencia: No se pudo convertir el valor '{valor}'. Estableciendo como NaN.")
        return float("nan") 

def limpiar_anio(valor):
    try:
        return int(valor.split()[0]) 
    except ValueError:
        print(f"Advertencia: No se pudo procesar el valor del año '{valor}'. Estableciendo como NaN.")
        return float("nan")

df["Ganancias"] = df["Ganancias"].apply(convertir_ganancias)
df["Año"] = df["Año"].apply(limpiar_anio)

df = df.sort_values("Año", ascending=False)

fila_ultimo_anio = df.iloc[0]  

ultimo_anio = int(fila_ultimo_anio["Año"])

mensaje = f"Tesla ha generado ${fila_ultimo_anio['Ganancias']:,.2f} de ganancias en el año {ultimo_anio}."

print(mensaje)