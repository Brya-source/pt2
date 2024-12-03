import pymysql
import spacy
from spacy.matcher import Matcher

# Cargamos el modelo de spaCy
nlp = spacy.load('es_core_news_md')

# --- FUNCIÓN PARA EXTRAER EL MOMENTO DEL DÍA DEL SECUESTRO ---

def extraer_momento_dia(texto):
    doc = nlp(texto.lower())

    # Inicializamos el Matcher de spaCy
    matcher = Matcher(nlp.vocab)

    # Patrones para momentos del día
    momentos_dia = ["mañana", "tarde", "noche", "madrugada"]
    patrones_momento_dia = [
        [{"LOWER": {"IN": ["en", "por", "durante", "al", "a", "aproximadamente", "cerca", "pasado"]}}, {"LOWER": {"IN": ["la", "el"]}, "OP": "?"}, {"LOWER": {"IN": momentos_dia}}],
        [{"LOWER": {"IN": momentos_dia}}],
        [{"LOWER": {"IN": ["temprano", "anoche", "ayer", "hoy"]}}],
    ]

    # Agregamos los patrones al matcher
    matcher.add("MomentoDia", patrones_momento_dia)

    momentos_detectados = []

    # Aplicamos el matcher al documento
    matches = matcher(doc)
    for match_id, start, end in matches:
        span = doc[start:end]
        momento = None

        # Determinar el momento del día detectado
        for token in span:
            if token.lower_ in momentos_dia:
                momento = token.lower_
                break
            elif token.lower_ == "temprano":
                momento = "mañana"
                break
            elif token.lower_ == "anoche":
                momento = "noche"
                break

        if momento:
            # Agregamos el momento detectado a la lista
            momentos_detectados.append((momento, span.sent.text))
            break  # Detenemos después de la primera detección relevante

    # Si no se detectó ningún momento, indicamos que no hay información
    if not momentos_detectados:
        return "No hay información sobre el momento del secuestro."
    else:
        # Retornamos el momento detectado y el contexto
        momento, oracion = momentos_detectados[0]
        return f"Momento del secuestro: {momento.capitalize()}.\nContexto: '{oracion.strip()}'"

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

# --- FUNCIÓN PARA OBTENER LAS NOTICIAS CON 'Sí' EN RELACION_SPACY4 ---

def obtener_noticias():
    conexion = conectar_bd()
    try:
        with conexion.cursor() as cursor:
            sql = "SELECT id, noticia_corregida FROM extracciones WHERE relacion_spacy4 = 'Sí' LIMIT 100"
            cursor.execute(sql)
            resultados = cursor.fetchall()
            return resultados
    finally:
        conexion.close()

# --- PROCESAR Y ANALIZAR NOTICIAS ---

def procesar_noticias():
    # Obtener y procesar noticias
    noticias = obtener_noticias()
    for noticia in noticias:
        id_noticia = noticia['id']
        texto_noticia = noticia['noticia_corregida']

        # Analizar el momento del secuestro
        resultado_momento = extraer_momento_dia(texto_noticia)

        # Mostrar resultados del análisis
        print(f"\n--- Analizando noticia con ID: {id_noticia} ---")
        print(f"{resultado_momento}")

# --- EJECUCIÓN DEL PROGRAMA ---
if __name__ == "__main__":
    procesar_noticias()
