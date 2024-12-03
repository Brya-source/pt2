import mysql.connector
import spacy
import re
import pandas as pd

# Cargar modelo de spaCy (cambiar según el modelo disponible)
nlp = spacy.load("es_core_news_sm")

# Función para limpiar texto (sin eliminar stopwords esta vez)
def limpiar_texto(texto):
    texto = texto.lower()
    texto = re.sub(r'[^\w\s]', '', texto)
    return texto

# Función para extraer entidades con spaCy
def extraer_entidades(texto):
    doc = nlp(texto)
    ubicaciones = [ent.text for ent in doc.ents if ent.label_ == "GPE"]
    fechas = [ent.text for ent in doc.ents if ent.label_ == "DATE"]
    return ubicaciones, fechas

# Función para extraer fechas con regex (formato específico)
def extraer_fechas_regex(texto):
    fechas_regex = re.findall(r'\b(?:\d{1,2}\s[de]\s(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s\d{4})\b', texto)
    return fechas_regex

# Función para búsqueda manual de palabras clave de ubicación
def buscar_palabras_clave(texto):
    palabras_clave = ["mexico", "ciudad de mexico", "edomex", "estado de mexico", "toluca"]
    ubicaciones = [palabra for palabra in palabras_clave if palabra in texto]
    return ubicaciones

# Conexión a la base de datos
def conectar_base_datos():
    conexion = mysql.connector.connect(
        host="localhost",
        user="root",  # Cambia esto por tu usuario
        password="Soccer.8a",  # Cambia esto por tu contraseña
        database="noticias1"
    )
    return conexion

# Función principal para procesar las noticias
def procesar_noticias():
    conexion = conectar_base_datos()
    cursor = conexion.cursor(dictionary=True)

    # Seleccionar todas las noticias de la tabla "extracciones"
    cursor.execute("SELECT id, titulo, descripcion, noticia, fecha, url FROM extracciones")
    noticias = cursor.fetchall()

    # Almacenar resultados
    resultados = []

    for noticia in noticias:
        texto_limpio = noticia['noticia']
        print(f"Texto limpio para la ID {noticia['id']}: {texto_limpio}")  # Imprimir el texto limpio

        ubicaciones_spacy, fechas_spacy = extraer_entidades(texto_limpio)
        ubicaciones_clave = buscar_palabras_clave(texto_limpio)
        fechas_regex = extraer_fechas_regex(texto_limpio)

        resultado = {
            "ID": noticia['id'],
            "Titulo": noticia['titulo'],
            "Ubicaciones (spaCy)": ubicaciones_spacy,
            "Ubicaciones (Palabras Clave)": ubicaciones_clave,
            "Fechas (spaCy)": fechas_spacy,
            "Fechas (Regex)": fechas_regex,
            "URL": noticia['url']
        }
        resultados.append(resultado)

        # Imprimir los resultados extraídos
        print(f"ID: {noticia['id']}")
        print(f"Titulo: {noticia['titulo']}")
        print(f"Ubicaciones (spaCy): {ubicaciones_spacy}")
        print(f"Ubicaciones (Palabras Clave): {ubicaciones_clave}")
        print(f"Fechas (spaCy): {fechas_spacy}")
        print(f"Fechas (Regex): {fechas_regex}")
        print(f"URL: {noticia['url']}")
        print("-" * 40)

    # Cerrar conexión
    cursor.close()
    conexion.close()

    return resultados

# Ejecutar el procesamiento
resultados = procesar_noticias()
