import pymysql
import spacy
from spacy.matcher import Matcher

# Cargamos el modelo de spaCy
nlp = spacy.load('es_core_news_md')


# --- FUNCIONES PARA DETECTAR SI HUBO LIBERACIÓN Y RESCATE ---

def detectar_liberacion_rescate(texto):
    doc = nlp(texto.lower())

    # Inicializamos el Matcher
    matcher = Matcher(nlp.vocab)

    # Patrones para detectar liberación con contexto
    patrones_liberacion = [
        [{"LEMMA": {"IN": ["liberar", "escapar", "huir", "fugarse"]}}, {"OP": "+"}],
        [{"TEXT": {"REGEX": "liberado|escapó|logró escapar|dejado en libertad"}}, {"OP": "+"}],
        [{"TEXT": {"REGEX": "se liberaron|se escaparon|huyeron"}}, {"OP": "+"}]
    ]

    # Patrones para detectar rescate con contexto
    patrones_rescate = [
        [{"LEMMA": {"IN": ["rescatar", "salvar", "liberar"]}}, {"OP": "+"}],
        [{"TEXT": {"REGEX": "rescatado|liberación tras|fue rescatado"}}, {"OP": "+"}]
    ]

    # Añadimos los patrones al matcher
    matcher.add("Liberacion", patrones_liberacion)
    matcher.add("Rescate", patrones_rescate)

    explicacion = []  # Para almacenar las explicaciones
    hubo_liberacion = False  # Variable para determinar si hubo liberación
    hubo_rescate = False  # Variable para determinar si hubo rescate
    fragmentos_liberacion = []  # Fragmentos de texto relevantes para la liberación
    fragmentos_rescate = []  # Fragmentos de texto relevantes para el rescate

    # Para controlar duplicados
    liberacion_detectada = False
    rescate_detectado = False

    # Buscar coincidencias de liberación y rescate
    matches = matcher(doc)
    for match_id, start, end in matches:
        span = doc[start:end]
        span_texto = span.text
        oracion_completa = span.sent.text  # Extraer la oración completa para más contexto

        # Verificamos si es liberación
        if nlp.vocab.strings[match_id] == "Liberacion" and not liberacion_detectada:
            hubo_liberacion = True
            fragmentos_liberacion.append(oracion_completa)
            explicacion.append(
                f"Liberación detectada en el fragmento: '{span_texto}'. Contexto completo: '{oracion_completa}'")
            liberacion_detectada = True  # Evitar duplicados

        # Verificamos si es rescate
        if nlp.vocab.strings[match_id] == "Rescate" and not rescate_detectado:
            hubo_rescate = True
            fragmentos_rescate.append(oracion_completa)
            explicacion.append(
                f"Rescate detectado en el fragmento: '{span_texto}'. Contexto completo: '{oracion_completa}'")
            rescate_detectado = True  # Evitar duplicados

    # Si no se detectó liberación, agregar una explicación
    if not hubo_liberacion:
        explicacion.append("No se detectó liberación en el texto.")

    # Si no se detectó rescate, agregar una explicación
    if not hubo_rescate:
        explicacion.append("No se detectó rescate en el texto.")

    return hubo_liberacion, hubo_rescate, explicacion


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


# --- FUNCIÓN PARA OBTENER LOS PRIMEROS 100 REGISTROS ---

def obtener_noticias():
    conexion = conectar_bd()
    try:
        with conexion.cursor() as cursor:
            sql = "SELECT id, noticia FROM extracciones LIMIT 100"
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
        texto_noticia = noticia['noticia']
        print(f"\n--- Analizando noticia con ID: {id_noticia} ---")
        hubo_liberacion, hubo_rescate, explicacion_rescate = detectar_liberacion_rescate(texto_noticia)

        # Imprimir la explicación
        for exp in explicacion_rescate:
            print(f"- {exp}")

        # Imprimir si hubo liberación o rescate
        if hubo_liberacion:
            print(f"¿Hubo liberación?: Sí")
        else:
            print(f"¿Hubo liberación?: No")

        if hubo_rescate:
            print(f"¿Hubo rescate?: Sí")
        else:
            print(f"¿Hubo rescate?: No")


# --- EJECUCIÓN DEL PROGRAMA ---
if __name__ == "__main__":
    procesar_noticias()
