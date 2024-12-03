import pymysql
import spacy

# Cargamos el modelo de spaCy para procesamiento de lenguaje natural
nlp = spacy.load('es_core_news_md')


# --- FUNCIONES PARA DETECTAR SI LA NOTICIA ESTÁ RELACIONADA CON SECUESTROS ---

def es_noticia_de_secuestro(texto_completo):
    # Pasar el texto completo al modelo de spaCy
    doc = nlp(texto_completo)

    # Variables para determinar si es secuestro y justificar
    es_secuestro = False
    justificacion = ""

    # Análisis semántico profundo: buscamos relaciones entre el contexto y situaciones de secuestro
    for ent in doc.ents:
        contexto = ent.sent.text

        # Evitar catalogar como secuestro si se detecta simulacro, película o contexto no relacionado
        if any(term in contexto.lower() for term in ['simulacro', 'película', 'serie', 'ficticio', 'ficción']):
            es_secuestro = False
            justificacion = f"Contexto detectado relacionado con simulacros, películas o ficción: '{contexto}'"
            break

        # Análisis de entidades y contexto real de secuestro
        if ent.label_ in ['PER', 'ORG', 'MISC']:
            # Verificar contexto que implique secuestro real o privación de libertad
            if any(verb in contexto for verb in ['retenido', 'privado', 'capturado', 'detenido', 'secuestrado']):
                es_secuestro = True
                justificacion = f"Se encontró contexto de posible secuestro o privación de libertad en: '{contexto}'"
                break

        # Analizar relaciones entre víctimas y acciones asociadas con secuestro
        if "víctima" in ent.text and any(action in ent.sent.text for action in ['retenida', 'privada de libertad']):
            es_secuestro = True
            justificacion = f"Contexto de víctima privada de libertad en: '{ent.sent.text}'"
            break

    return es_secuestro, justificacion


# --- CONEXIÓN A LA BASE DE DATOS ---

def conectar_bd():
    conexion = pymysql.connect(
        host='localhost',
        user='root',
        password='Soccer.8a',
        database='noticias',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    return conexion


# --- FUNCIÓN PARA OBTENER LOS REGISTROS CON TÍTULO Y DESCRIPCIÓN, PERO ANALIZAR SOLO EL CAMPO NOTICIA_CORREGIDA ---

def obtener_noticias():
    conexion = conectar_bd()
    try:
        with conexion.cursor() as cursor:
            # Seleccionar id, noticia_corregida, excluyendo ciertos términos en los campos título y descripción
            sql = """
            SELECT id, noticia_corregida
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
            AND descripcion NOT LIKE '%Netanyahu%'
            AND titulo NOT LIKE '%Chapo Guzmán%' 
            AND descripcion NOT LIKE '%Chapo Guzmán%' 
            AND titulo NOT LIKE '%Ovidio Guzmán%' 
            AND descripcion NOT LIKE '%Ovidio Guzmán%');
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
            # Verificar si la columna 'relacion_spacy4' ya existe, si no, crearla
            cursor.execute("SHOW COLUMNS FROM extracciones LIKE 'relacion_spacy4';")
            resultado = cursor.fetchone()

            if not resultado:
                cursor.execute("ALTER TABLE extracciones ADD COLUMN relacion_spacy4 VARCHAR(3);")

            # Procesar cada noticia y analizar si está relacionada con secuestros usando solo el campo noticia_corregida
            for noticia in noticias:
                id_noticia = noticia['id']
                texto_completo = noticia['noticia_corregida']

                # Realizar el análisis semántico en el campo noticia_corregida
                relacionada_con_secuestro, justificacion = es_noticia_de_secuestro(texto_completo)

                # Actualizar el campo 'relacion_spacy4' en la base de datos
                if relacionada_con_secuestro:
                    cursor.execute("UPDATE extracciones SET relacion_spacy4 = 'sí' WHERE id = %s", (id_noticia,))
                    print(f"Noticia ID {id_noticia} relacionada con secuestro. Justificación: {justificacion}")
                else:
                    cursor.execute("UPDATE extracciones SET relacion_spacy4 = 'no' WHERE id = %s", (id_noticia,))
                    print(f"Noticia ID {id_noticia} NO relacionada con secuestro. Justificación: {justificacion}")

                # Guardar los cambios inmediatamente después de procesar cada noticia
                conexion.commit()

    finally:
        conexion.close()


# --- EJECUCIÓN DEL PROGRAMA ---
if __name__ == "__main__":
    procesar_noticias()
