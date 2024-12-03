import pymysql
import spacy

# Cargamos el modelo de spaCy para procesamiento de lenguaje natural
nlp = spacy.load('es_core_news_md')


# --- FUNCIONES PARA DETECTAR SI LA NOTICIA ESTÁ RELACIONADA CON SECUESTROS ---

def es_noticia_de_secuestro(titulo, descripcion):
    # Concatenar los campos de título y descripción para analizarlos juntos
    texto_completo = f"{titulo} {descripcion}".lower()

    # Descartar noticias relacionadas con Israel o El Mayo Zambada
    if ("israel" in texto_completo or "gaza" in texto_completo or "hamas" in texto_completo or "netanyahu" in texto_completo
        or "mayo zambada" in texto_completo or '"el mayo"' in texto_completo):
        return False, None  # No imprimir justificación si es relacionado con Israel o El Mayo Zambada

    # Pasar el texto completo al modelo de spaCy
    doc = nlp(texto_completo)

    # Variables para determinar si es secuestro y justificar
    es_secuestro = False
    justificacion = []

    # Análisis semántico: buscar relaciones entre verbos de acción y contextos de secuestro
    for sent in doc.sents:
        # Verificar si hay términos que impliquen secuestro, retención o privación de libertad
        if ("víctima" in sent.text and ("privada de su libertad" in sent.text or "retenida" in sent.text)) or \
           ("menor" in sent.text and ("sustraído" in sent.text or "secuestrado" in sent.text)):
            es_secuestro = True
            justificacion.append(f"Contexto analizado como secuestro en la oración: '{sent.text.strip()}'")

        # Analizar si menciona "secuestro" o "plagio"
        elif "secuestro" in sent.text or "plagio" in sent.text or "rapto" in sent.text:
            es_secuestro = True
            justificacion.append(f"Palabra clave relacionada con secuestro en la oración: '{sent.text.strip()}'")

        # Contextos con delincuentes y retención de personas
        elif "delincuentes" in sent.text and "retenido" in sent.text:
            es_secuestro = True
            justificacion.append(f"Contexto analizado como secuestro en la oración: '{sent.text.strip()}'")

        # Detectar robo de menores solo si está relacionado con secuestro
        elif "menor" in sent.text and ("robo" in sent.text or "sustraído" in sent.text or "secuestrado" in sent.text):
            es_secuestro = True
            justificacion.append(f"Contexto relacionado con robo de menores en la oración: '{sent.text.strip()}'")

    # Si no se encuentra suficiente contexto de secuestro, agregar justificación
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


# --- FUNCIÓN PARA OBTENER LOS REGISTROS DE TÍTULO Y DESCRIPCIÓN ---

def obtener_noticias():
    conexion = conectar_bd()
    try:
        with conexion.cursor() as cursor:
            # Consulta para incluir solo registros relacionados con secuestros y excluir "Mayo Zambada" y "El Mayo"
            sql = """
            SELECT id, titulo, descripcion
            FROM extracciones
            WHERE (descripcion LIKE '%secuestro%' 
            OR descripcion LIKE '%secuestr%' 
            OR titulo LIKE '%secuestro%' 
            OR titulo LIKE '%secuestr%')
            AND (descripcion NOT LIKE '%Mayo Zambada%' 
            AND descripcion NOT LIKE '%El Mayo%' 
            AND titulo NOT LIKE '%Mayo Zambada%' 
            AND titulo NOT LIKE '%El Mayo%');
            """
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

        # Verificar si la noticia está relacionada con un secuestro y obtener justificación
        relacionada_con_secuestro, justificacion = es_noticia_de_secuestro(titulo, descripcion)

        # Imprimir el resultado
        print(f"\n--- Analizando noticia con ID: {id_noticia} ---")
        if relacionada_con_secuestro:
            print(f"La noticia con ID {id_noticia} está relacionada con secuestro.")
        else:
            print(f"La noticia con ID {id_noticia} NO está relacionada con secuestro.")

        # Imprimir la justificación solo si existe y no es una noticia relacionada con Israel o El Mayo Zambada
        if justificacion:
            print("Justificación:")
            for exp in justificacion:
                print(f"- {exp}")

# --- EJECUCIÓN DEL PROGRAMA ---
if __name__ == "__main__":
    procesar_noticias()

