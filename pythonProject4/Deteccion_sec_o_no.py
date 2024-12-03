import pymysql
import spacy

# Cargamos el modelo de spaCy para procesamiento de lenguaje natural
nlp = spacy.load('es_core_news_md')


# --- FUNCIONES PARA DETECTAR SI LA NOTICIA ESTÁ RELACIONADA CON SECUESTROS ---

def es_noticia_de_secuestro(titulo, descripcion, noticia):
    # Concatenar los campos para analizarlos juntos
    texto_completo = f"{titulo} {descripcion} {noticia}".lower()

    # Pasar el texto completo al modelo de spaCy
    doc = nlp(texto_completo)

    # Palabras clave que podrían indicar relación con secuestros
    palabras_clave_secuestro = ["secuestro", "rapto", "plagio", "rehenes", "secuestrados"]

    # Variables para determinar si es secuestro y justificar
    es_secuestro = False
    justificacion = []

    # Analizar las oraciones para detectar el contexto
    for sent in doc.sents:
        # Analizamos si la oración contiene alguna palabra clave y verificamos si el contexto indica secuestro
        if any(palabra in sent.text for palabra in palabras_clave_secuestro):
            es_secuestro = True
            justificacion.append(f"Palabra clave encontrada en la oración: '{sent.text.strip()}'")
        else:
            # Si no hay palabra clave, analizamos el contexto
            if "víctima" in sent.text and ("privada de su libertad" in sent.text or "retenida" in sent.text):
                es_secuestro = True
                justificacion.append(f"Contexto analizado como secuestro en la oración: '{sent.text.strip()}'")
            elif "delincuentes" in sent.text and "retenido" in sent.text:
                es_secuestro = True
                justificacion.append(f"Contexto analizado como secuestro en la oración: '{sent.text.strip()}'")

    # Si no hay una palabra clave ni contexto claro, agregar una justificación
    if not es_secuestro:
        justificacion.append("No se encontró suficiente evidencia para clasificar la noticia como secuestro.")

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
            sql = "SELECT id, titulo, descripcion, noticia FROM extracciones"
            cursor.execute(sql)
            resultados = cursor.fetchall()
            return resultados
    finally:
        conexion.close()


# --- PROCESAR Y CLASIFICAR NOTICIAS ---

def procesar_noticias():
    noticias = obtener_noticias()
    for noticia in noticias:
        id_noticia = noticia['id']
        titulo = noticia['titulo']
        descripcion = noticia['descripcion']
        texto_noticia = noticia['noticia']

        # Verificar si la noticia está relacionada con un secuestro y obtener justificación
        relacionada_con_secuestro, justificacion = es_noticia_de_secuestro(titulo, descripcion, texto_noticia)

        # Imprimir el resultado
        print(f"\n--- Analizando noticia con ID: {id_noticia} ---")
        if relacionada_con_secuestro:
            print(f"La noticia con ID {id_noticia} está relacionada con secuestro.")
        else:
            print(f"La noticia con ID {id_noticia} NO está relacionada con secuestro.")

        # Imprimir la justificación
        print("Justificación:")
        for exp in justificacion:
            print(f"- {exp}")


# --- EJECUCIÓN DEL PROGRAMA ---
if __name__ == "__main__":
    procesar_noticias()
