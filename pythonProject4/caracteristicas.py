import spacy
import mysql.connector
import pandas as pd

# Cargar el modelo de lenguaje en español de spaCy
nlp = spacy.load("es_core_news_sm")

# Configuración de la conexión a la base de datos
db_config = {
    'user': 'root',
    'password': 'Soccer.8a',
    'host': '127.0.0.1',
    'database': 'noticias1'
}


def cargar_datos():
    try:
        conn = mysql.connector.connect(**db_config)
        query = "SELECT id, noticia FROM extracciones"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except mysql.connector.Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None


def procesar_lote(df_lote):
    for idx, row in df_lote.iterrows():
        noticia = row['noticia']
        doc = nlp(noticia)

        # Extraer entidades nombradas
        entidades = [ent.text for ent in doc.ents]

        # Extraer palabras clave
        palabras_clave = [token.lemma_ for token in doc if token.is_alpha and not token.is_stop]

        print(f"Noticia ID {row['id']} - Entidades: {entidades[:5]}")  # Muestra un resumen de las entidades
        print(
            f"Noticia ID {row['id']} - Palabras clave: {palabras_clave[:5]}")  # Muestra un resumen de las palabras clave

        # Aquí podrías actualizar la base de datos si lo deseas


def procesar_por_lotes(df, batch_size=100):
    for i in range(0, len(df), batch_size):
        df_lote = df[i:i + batch_size]
        print(f"Procesando lote {i // batch_size + 1} de {len(df) // batch_size + 1}")
        procesar_lote(df_lote)


# Script principal
if __name__ == "__main__":
    df = cargar_datos()

    if df is not None:
        procesar_por_lotes(df, batch_size=100)  # Ajusta el tamaño del lote según sea necesario
    else:
        print("No se pudieron cargar los datos.")
