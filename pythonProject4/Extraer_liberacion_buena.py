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
    hubo_liberacion = False

    # Aplicamos el matcher para buscar coincidencias
    matches = matcher(doc)

    for match_id, start, end in matches:
        span = doc[start:end]
        tipo = nlp.vocab.strings[match_id]

        # Clasificación basada en tipo de patrón detectado
        if tipo == "LiberacionGeneral":
            tipo_liberacion = "Liberación general"
            hubo_liberacion = True
            break
        elif tipo == "Operativo":
            tipo_liberacion = "Liberación en operativo"
            hubo_liberacion = True
        elif tipo == "Autoridad":
            tipo_liberacion = "Liberación por autoridad"
            hubo_liberacion = True
        elif tipo == "Retorno":
            tipo_liberacion = "Retorno sin detalles"
            hubo_liberacion = True

    return hubo_liberacion, tipo_liberacion


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


# --- FUNCIÓN PARA VERIFICAR Y AGREGAR CAMPOS SI NO EXISTEN ---

def verificar_y_agregar_campos():
    conexion = conectar_bd()
    try:
        with conexion.cursor() as cursor:
            # Verificar si los campos existen en la tabla
            cursor.execute("SHOW COLUMNS FROM extracciones LIKE 'liberacion'")
            existe_liberacion = cursor.fetchone()

            cursor.execute("SHOW COLUMNS FROM extracciones LIKE 'tipo_liberacion'")
            existe_tipo_liberacion = cursor.fetchone()

            # Si no existe 'liberacion', lo agregamos
            if not existe_liberacion:
                cursor.execute("ALTER TABLE extracciones ADD COLUMN liberacion VARCHAR(3)")
                print("Campo 'liberacion' agregado.")

            # Si no existe 'tipo_liberacion', lo agregamos
            if not existe_tipo_liberacion:
                cursor.execute("ALTER TABLE extracciones ADD COLUMN tipo_liberacion VARCHAR(50)")
                print("Campo 'tipo_liberacion' agregado.")

            conexion.commit()
    finally:
        conexion.close()


# --- FUNCIÓN PARA OBTENER LAS NOTICIAS CON 'Sí' EN RELACION_SPACY4 ---

def obtener_noticias():
    conexion = conectar_bd()
    try:
        with conexion.cursor() as cursor:
            sql = "SELECT id, noticia_corregida FROM extracciones WHERE relacion_spacy4 = 'Sí'"
            cursor.execute(sql)
            resultados = cursor.fetchall()
            return resultados
    finally:
        conexion.close()


# --- FUNCIÓN PARA ACTUALIZAR LA BASE DE DATOS CON LOS RESULTADOS ---

def actualizar_noticia(id_noticia, liberacion, tipo_liberacion):
    conexion = conectar_bd()
    try:
        with conexion.cursor() as cursor:
            sql = """
            UPDATE extracciones 
            SET liberacion = %s, tipo_liberacion = %s 
            WHERE id = %s
            """
            cursor.execute(sql, (liberacion, tipo_liberacion, id_noticia))
            conexion.commit()
    finally:
        conexion.close()


# --- PROCESAR Y ANALIZAR NOTICIAS ---

def procesar_noticias():
    # Verificamos y agregamos los campos si no existen
    verificar_y_agregar_campos()

    # Obtener y procesar noticias
    noticias = obtener_noticias()
    for noticia in noticias:
        id_noticia = noticia['id']
        texto_noticia = noticia['noticia_corregida']

        # Clasificación del tipo de liberación y justificación
        hubo_liberacion, tipo_liberacion = clasificar_liberacion(texto_noticia)

        # Mostrar resultados de la clasificación
        print(f"\n--- Analizando noticia con ID: {id_noticia} ---")
        print(f"¿Hubo liberación?: {'Sí' if hubo_liberacion else 'No'}")
        print(f"Tipo de liberación: {tipo_liberacion}")

        # Actualizar la base de datos con los resultados
        actualizar_noticia(id_noticia, 'Sí' if hubo_liberacion else 'No', tipo_liberacion)


# --- EJECUCIÓN DEL PROGRAMA ---
if __name__ == "__main__":
    procesar_noticias()
