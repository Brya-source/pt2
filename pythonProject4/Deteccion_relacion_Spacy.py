import pymysql
import spacy

# Cargamos el modelo de spaCy para procesamiento de lenguaje natural
nlp = spacy.load('es_core_news_md')


# --- FUNCIONES PARA DETECTAR SI LA NOTICIA ESTÁ RELACIONADA CON SECUESTROS ---

def es_noticia_de_secuestro(texto_completo):
    # Pasar el texto completo al modelo de spaCy
    doc = nlp(texto_completo)

    # Variables para determinar si es secuestro
    es_secuestro = False

    # Análisis semántico: buscar relaciones entre verbos de acción y contextos de secuestro
    for sent in doc.sents:
        # Verificar si hay términos que impliquen secuestro, retención o privación de libertad
        if ("víctima" in sent.text and ("privada de su libertad" in sent.text or "retenida" in sent.text)) or \
           ("menor" in sent.text and ("sustraído" in sent.text or "secuestrado" in sent.text)):
            es_secuestro = True

        # Analizar si menciona "secuestro" o "rapto"
        elif "secuestro" in sent.text or "rapto" in sent.text:
            es_secuestro = True

        # Contextos con delincuentes y retención de personas
        elif "delincuentes" in sent.text and "retenido" in sent.text:
            es_secuestro = True

        # Detectar robo de menores solo si está relacionado con secuestro
        elif "menor" in sent.text and ("robo" in sent.text or "sustraído" in sent.text or "secuestrado" in sent.text):
            es_secuestro = True

    return es_secuestro


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


# --- FUNCIÓN PARA OBTENER LOS REGISTROS CON TÍTULO, DESCRIPCIÓN Y NOTICIA ---

def obtener_noticias():
    conexion = conectar_bd()
    try:
        with conexion.cursor() as cursor:
            # Seleccionar id, título, descripción y noticia, excluyendo ciertas palabras clave en el título y descripción
            sql = """
            SELECT id, titulo, descripcion, noticia
            FROM extracciones
            WHERE (titulo NOT LIKE '%El Mayo Zambada%' 
            AND descripcion NOT LIKE '%El Mayo Zambada%' 
            AND titulo NOT LIKE '%El Mayo%' 
            AND descripcion NOT LIKE '%El Mayo%' 
            AND titulo NOT LIKE '%Israel%' 
            AND descripcion NOT LIKE '%Israel%' 
            AND titulo NOT LIKE '%Gaza%' 
            AND descripcion NOT LIKE '%Gaza%' 
            AND titulo NOT LIKE '%Hamas%' 
            AND descripcion NOT LIKE '%Hamas%' 
            AND titulo NOT LIKE '%Netanyahu%' 
            AND descripcion NOT LIKE '%Netanyahu%');
            """
            cursor.execute(sql)
            resultados = cursor.fetchall()
            return resultados
    finally:
        conexion.close()


# --- PROCESAR Y CLASIFICAR NOTICIAS ---

def procesar_noticias():
    noticias = obtener_noticias()
    conexion = conectar_bd()
    try:
        with conexion.cursor() as cursor:
            # Verificar si la columna 'relacion_spacy' ya existe, si no, crearla
            cursor.execute("SHOW COLUMNS FROM extracciones LIKE 'relacion_spacy2';")
            resultado = cursor.fetchone()

            if not resultado:
                cursor.execute("ALTER TABLE extracciones ADD COLUMN relacion_spacy2 VARCHAR(3);")

            # Procesar cada noticia y analizar si está relacionada con secuestros
            for noticia in noticias:
                id_noticia = noticia['id']
                titulo = noticia['titulo']
                descripcion = noticia['descripcion']
                texto_noticia = noticia['noticia']

                # Verificamos si título o descripción contienen las palabras clave
                if titulo and descripcion:
                    texto_completo = f"{titulo} {descripcion}"

                    # Si no hay coincidencias con las palabras clave, analizamos la noticia
                    relacionada_con_secuestro = es_noticia_de_secuestro(texto_noticia)

                    # Actualizar el campo 'relacion_spacy' en la base de datos
                    if relacionada_con_secuestro:
                        cursor.execute("UPDATE extracciones SET relacion_spacy2 = 'sí' WHERE id = %s", (id_noticia,))
                    else:
                        cursor.execute("UPDATE extracciones SET relacion_spacy2 = '' WHERE id = %s", (id_noticia,))

                    # Guardar los cambios inmediatamente después de procesar cada noticia
                    conexion.commit()

    finally:
        conexion.close()


# --- EJECUCIÓN DEL PROGRAMA ---
if __name__ == "__main__":
    procesar_noticias()
