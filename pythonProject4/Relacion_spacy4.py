import pymysql
import spacy

# Cargamos el modelo de spaCy para procesamiento de lenguaje natural
nlp = spacy.load('es_core_news_md')


# --- FUNCIONES PARA DETECTAR SI LA NOTICIA ESTÁ RELACIONADA CON SECUESTROS ---

def es_noticia_de_secuestro(titulo, descripcion):
    # Combinar título y descripción para un análisis más completo
    texto_combinado = f"{titulo} {descripcion}"
    doc = nlp(texto_combinado)

    # Variables para determinar si es secuestro y justificar
    es_secuestro = False
    justificacion = ""

    # Palabras clave relacionadas con secuestros y términos excluyentes
    palabras_clave_secuestro = ['secuestro', 'secuestrado', 'secuestrada', 'plagio', 'rapto', 'retenido', 'privado de libertad']
    terminos_excluyentes = ['simulacro', 'película', 'serie', 'ficticio', 'ficción', 'documental', 'novela', 'obra de teatro']

    # Verificar si los términos excluyentes están presentes
    for termino in terminos_excluyentes:
        if termino in texto_combinado.lower():
            es_secuestro = False
            justificacion = f"Se detectó un término excluyente relacionado con ficción o simulación: '{termino}'"
            return es_secuestro, justificacion

    # Buscar frases que indiquen un secuestro real
    for sent in doc.sents:
        sent_lower = sent.text.lower()
        if any(palabra in sent_lower for palabra in palabras_clave_secuestro):
            # Verificar si la frase menciona víctimas reales y acciones de secuestro
            if any(ent.label_ == 'PER' for ent in sent.ents):
                es_secuestro = True
                justificacion = f"Se encontró una frase que indica un secuestro real: '{sent.text}'"
                return es_secuestro, justificacion

    # Si no se encontraron indicadores claros de secuestro
    justificacion = "No se encontraron indicios claros de un secuestro real."
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


# --- FUNCIÓN PARA OBTENER LOS REGISTROS CON TÍTULO Y DESCRIPCIÓN ---

def obtener_noticias():
    conexion = conectar_bd()
    try:
        with conexion.cursor() as cursor:
            # Seleccionar id, título y descripción, excluyendo ciertos términos
            sql = """
            SELECT id, titulo, descripcion
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
            # Verificar si la columna 'relacion_spacy5' ya existe, si no, crearla
            cursor.execute("SHOW COLUMNS FROM extracciones LIKE 'relacion_spacy5';")
            resultado = cursor.fetchone()

            if not resultado:
                cursor.execute("ALTER TABLE extracciones ADD COLUMN relacion_spacy5 VARCHAR(3);")

            # Procesar cada noticia y analizar si está relacionada con secuestros
            for noticia in noticias:
                id_noticia = noticia['id']
                titulo = noticia['titulo'] or ""
                descripcion = noticia['descripcion'] or ""

                # Realizar el análisis semántico
                relacionada_con_secuestro, justificacion = es_noticia_de_secuestro(titulo, descripcion)

                # Actualizar el campo 'relacion_spacy5' en la base de datos
                if relacionada_con_secuestro:
                    cursor.execute("UPDATE extracciones SET relacion_spacy5 = 'sí' WHERE id = %s", (id_noticia,))
                    print(f"Noticia ID {id_noticia} relacionada con secuestro. Justificación: {justificacion}")
                else:
                    cursor.execute("UPDATE extracciones SET relacion_spacy5 = 'no' WHERE id = %s", (id_noticia,))
                    print(f"Noticia ID {id_noticia} NO relacionada con secuestro. Justificación: {justificacion}")

                # Guardar los cambios inmediatamente después de procesar cada noticia
                conexion.commit()

    finally:
        conexion.close()


# --- EJECUCIÓN DEL PROGRAMA ---
if __name__ == "__main__":
    procesar_noticias()

