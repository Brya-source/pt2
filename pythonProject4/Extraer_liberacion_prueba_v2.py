import pymysql
import spacy
from spacy.matcher import Matcher

# Cargamos el modelo de spaCy
nlp = spacy.load('es_core_news_md')


# --- FUNCIÓN PARA CLASIFICAR LIBERACIÓN ---

def clasificar_liberacion(texto):
    doc = nlp(texto.lower())
    matcher = Matcher(nlp.vocab)

    # Patrones específicos para clasificar liberación
    patrones_liberacion_general = [
        [{"LEMMA": {"IN": ["liberar", "rescatar"]}}, {"OP": "+"}],
        [{"TEXT": {"REGEX": "liberado|liberaron|rescatado|rescatados|apareció sano y salvo|retornó a su hogar"}}]
    ]

    patrones_operativo = [
        [{"LEMMA": {"IN": ["operativo", "rescatar", "encontrar"]}}, {"LOWER": "policiaco", "OP": "?"}],
        [{"TEXT": {"REGEX": "fueron rescatados|fueron liberados"}}]
    ]

    patrones_autoridad = [
        [{"LEMMA": {"IN": ["elemento", "ejército", "autoridad"]}}, {"LOWER": "mexicano", "OP": "?"},
         {"LOWER": "liberar", "OP": "+"}]
    ]

    patrones_retorno = [
        [{"LEMMA": {"IN": ["retornar", "regresar", "volver"]}}, {"TEXT": {"REGEX": "a su hogar|sano y salvo"}}]
    ]

    # Agregamos los patrones al matcher
    matcher.add("LiberacionGeneral", patrones_liberacion_general)
    matcher.add("Operativo", patrones_operativo)
    matcher.add("Autoridad", patrones_autoridad)
    matcher.add("Retorno", patrones_retorno)

    # Inicializamos variables de clasificación y justificación
    tipo_liberacion = "No clasificado"
    justificacion = None

    # Aplicamos el matcher para buscar coincidencias
    matches = matcher(doc)
    liberacion_detectada = set()

    for match_id, start, end in matches:
        span = doc[start:end]
        tipo = nlp.vocab.strings[match_id]

        # Clasificación basada en tipo de patrón detectado
        if tipo == "LiberacionGeneral":
            tipo_liberacion = "Liberación general"
            justificacion = f"Liberación detectada en el fragmento: '{span.sent.text}'"
            break  # Detección prioritaria
        elif tipo == "Operativo":
            tipo_liberacion = "Liberación en operativo"
            justificacion = f"Liberación detectada en un contexto de operativo: '{span.sent.text}'"
        elif tipo == "Autoridad":
            tipo_liberacion = "Liberación por autoridad"
            justificacion = f"Liberación detectada por intervención de autoridades: '{span.sent.text}'"
        elif tipo == "Retorno":
            tipo_liberacion = "Retorno sin detalles"
            justificacion = f"Retorno detectado sin detalles claros de liberación: '{span.sent.text}'"

    if not justificacion:
        justificacion = "No se encontró evidencia de liberación en el texto."

    return tipo_liberacion, justificacion


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
    noticias = obtener_noticias()
    for noticia in noticias:
        id_noticia = noticia['id']
        texto_noticia = noticia['noticia_corregida']
        print(f"\n--- Analizando noticia con ID: {id_noticia} ---")

        # Clasificación del tipo de liberación y justificación
        tipo_liberacion, justificacion = clasificar_liberacion(texto_noticia)

        # Mostrar resultados de la clasificación
        print(f"¿Hubo liberación?: {'Sí' if tipo_liberacion != 'No clasificado' else 'No'}")
        print(f"Tipo de liberación: {tipo_liberacion}")
        print(f"Justificación: {justificacion}\n")


# --- EJECUCIÓN DEL PROGRAMA ---
if __name__ == "__main__":
    procesar_noticias()


