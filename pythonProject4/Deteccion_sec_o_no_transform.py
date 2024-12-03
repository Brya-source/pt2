import pymysql
from transformers import pipeline
import time

# --- CONFIGURACIÓN DEL MODELO BART ---

# Cargamos un modelo de clasificación zero-shot con BART
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# --- FUNCIÓN PARA DETECTAR SI LA NOTICIA ESTÁ RELACIONADA CON SECUESTROS Y DESCARTAR "El Mayo Zambada" ---

def es_noticia_de_secuestro_bert(titulo, descripcion, noticia):
    # Concatenar los campos para analizarlos juntos
    texto_completo = f"{titulo} {descripcion} {noticia}"

    # Descartamos la noticia si menciona a "El Mayo Zambada"
    if "El Mayo Zambada" in texto_completo:
        return False, "Noticia descartada por mencionar a El Mayo Zambada."

    # Definimos etiquetas para el análisis
    etiquetas = ["Secuestro", "No Secuestro"]

    # Utilizamos BART para clasificar si la noticia está relacionada con secuestro o no
    resultado = classifier(texto_completo, candidate_labels=etiquetas, hypothesis_template="Este texto trata sobre {}.")

    # Extraemos la etiqueta más probable y su puntuación
    etiqueta = resultado['labels'][0]
    puntuacion = resultado['scores'][0]

    # Si la etiqueta más probable es "Secuestro" y la puntuación es suficientemente alta (70%)
    es_secuestro = etiqueta == "Secuestro" and puntuacion > 0.7

    # Justificación del resultado
    justificacion = f"Etiqueta predicha: {etiqueta} con una puntuación de {puntuacion:.2f}"

    return es_secuestro, justificacion

# --- CONEXIÓN A LA BASE DE DATOS ---

def conectar_bd():
    conexion = pymysql.connect(
        host='localhost',
        user='root',
        password='Soccer.8a',
        database='noticias_prueba',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    return conexion

# --- FUNCIÓN PARA OBTENER LOS REGISTROS DE TÍTULO, DESCRIPCIÓN Y NOTICIA ---

def obtener_noticias():
    conexion = conectar_bd()
    try:
        with conexion.cursor() as cursor:
            sql = "SELECT id, titulo, descripcion, noticia FROM extracciones LIMIT 100"
            cursor.execute(sql)
            resultados = cursor.fetchall()
            return resultados
    finally:
        conexion.close()

# --- PROCESAR Y CLASIFICAR NOTICIAS ---

def procesar_noticias():
    noticias = obtener_noticias()
    for idx, noticia in enumerate(noticias):
        id_noticia = noticia['id']
        titulo = noticia['titulo']
        descripcion = noticia['descripcion']
        texto_noticia = noticia['noticia']

        # Imprimimos un mensaje para indicar que estamos procesando la noticia
        print(f"\n--- Analizando noticia {idx + 1} con ID: {id_noticia} ---")
        start_time = time.time()  # Marcamos el tiempo de inicio

        # Verificar si la noticia está relacionada con un secuestro utilizando BART
        relacionada_con_secuestro, justificacion = es_noticia_de_secuestro_bert(titulo, descripcion, texto_noticia)

        # Imprimir el resultado
        if relacionada_con_secuestro:
            print(f"La noticia con ID {id_noticia} está relacionada con secuestro.")
        else:
            print(f"La noticia con ID {id_noticia} NO está relacionada con secuestro.")

        # Imprimir la justificación
        print(f"Justificación: {justificacion}")

        # Mostrar el tiempo que tomó procesar la noticia
        end_time = time.time()
        print(f"Tiempo de procesamiento para la noticia {idx + 1}: {end_time - start_time:.2f} segundos")

# --- EJECUCIÓN DEL PROGRAMA ---
if __name__ == "__main__":
    procesar_noticias()
