import pandas as pd
import mysql.connector
from collections import Counter
import re

# Configuración de la conexión a la base de datos
db_config = {
    'user': 'root',
    'password': 'Soccer.8a',
    'host': '127.0.0.1',
    'database': 'noticias_prueba'
}


def cargar_datos():
    try:
        # Conectar a la base de datos
        conn = mysql.connector.connect(**db_config)

        # Leer los datos de la tabla 'extracciones'
        query = "SELECT id, noticia FROM extracciones"
        df = pd.read_sql(query, conn)

        conn.close()
        return df

    except mysql.connector.Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None


def contar_frases_repetidas(df, min_palabras=3, top_n=20):
    # Unir todas las noticias en un solo texto
    texto_completo = ' '.join(df['noticia'].dropna().tolist())

    # Tokenizar el texto en palabras
    palabras = re.findall(r'\b\w+\b', texto_completo.lower())

    # Crear una lista de frases de
    frases = [' '.join(palabras[i:i + min_palabras]) for i in range(len(palabras) - min_palabras + 1)]

    # Contar las frases repetidas
    contador_frases = Counter(frases)

    # Obtener las frases más comunes
    frases_comunes = contador_frases.most_common(top_n)

    print(f"Las {top_n} frases más repetidas de {min_palabras} palabras:")
    for frase, conteo in frases_comunes:
        print(f"{frase}: {conteo} veces")

    return frases_comunes


def guardar_frases_comunes(frases_comunes, filename='frases_comunes.csv'):
    # Guardar las frases más comunes en un archivo CSV para referencia futura
    df_frases = pd.DataFrame(frases_comunes, columns=['frase', 'conteo'])
    df_frases.to_csv(filename, index=False)
    print(f"Frases comunes guardadas en {filename}")


# Script principal
if __name__ == "__main__":
    # Cargar datos desde la base de datos
    df = cargar_datos()

    if df is not None:
        # Contar frases repetidas (puedes ajustar min_palabras y top_n según tus necesidades)
        frases_comunes = contar_frases_repetidas(df, min_palabras=10, top_n=50)

        # Guardar las frases más comunes en un archivo CSV
        guardar_frases_comunes(frases_comunes)
    else:
        print("No se pudieron cargar los datos.")

