import pymysql
import spacy
from spacy.matcher import Matcher
import re
import dateparser  # Importamos dateparser
from dateparser.search import search_dates

# Cargamos el modelo de spaCy
nlp = spacy.load('es_core_news_md')

# --- FUNCIÓN PARA EXTRAER LA FECHA DEL SECUESTRO ---

def extraer_fecha_secuestro(texto):
    doc = nlp(texto.lower())

    # Inicializamos el Matcher de spaCy
    matcher = Matcher(nlp.vocab)

    # Patrones para identificar oraciones relacionadas con el secuestro
    patrones_secuestro = [
        [{"LEMMA": {"IN": ["secuestro", "privar", "raptar", "levantar"]}}],
        [{"TEXT": {"REGEX": "privado de su libertad|privada de su libertad"}}],
        [{"LEMMA": {"IN": ["ocurrir", "suceder", "registrar"]}}, {"POS": "ADP", "OP": "?"}, {"LOWER": "el", "OP": "?"}, {"LOWER": "secuestro"}],
    ]

    # Agregamos los patrones al matcher
    matcher.add("Secuestro", patrones_secuestro)

    # Obtenemos la lista de oraciones del documento
    sentences = list(doc.sents)

    # Buscamos oraciones que mencionen el secuestro
    matches = matcher(doc)
    fechas_detectadas = []

    for match_id, start, end in matches:
        span = doc[start:end]
        sent = span.sent  # Obtenemos la oración completa
        texto_oracion = sent.text

        # Buscamos fechas en la oración usando expresiones regulares
        fechas_en_oracion = extraer_fechas_en_texto(texto_oracion)
        if fechas_en_oracion:
            for fecha_texto in fechas_en_oracion:
                fechas_detectadas.append((fecha_texto, texto_oracion))
        else:
            # Si no se encuentra fecha en la oración, buscamos en la oración anterior
            sentence_index = sentences.index(sent)
            if sentence_index > 0:
                oracion_anterior = sentences[sentence_index - 1]
                texto_oracion_anterior = oracion_anterior.text
                fechas_en_oracion_anterior = extraer_fechas_en_texto(texto_oracion_anterior)
                if fechas_en_oracion_anterior:
                    for fecha_texto in fechas_en_oracion_anterior:
                        fechas_detectadas.append((fecha_texto, texto_oracion_anterior))

    # Si no se detectó ninguna fecha en contextos relevantes, indicamos que no hay información
    if not fechas_detectadas:
        return "No hay información suficiente sobre la fecha del secuestro.", None
    else:
        # Asumimos que la primera fecha detectada es la relevante
        fecha_texto, contexto = fechas_detectadas[0]
        fecha_formateada = formatear_fecha(fecha_texto)
        resultado = f"Fecha del secuestro: {fecha_formateada}\nContexto: '{contexto.strip()}'"
        return resultado, fecha_formateada

# --- FUNCIÓN PARA EXTRAER FECHAS EN UN TEXTO USANDO EXPRESIONES REGULARES ---

def extraer_fechas_en_texto(texto):
    patrones_fecha = [
        r"\b(\d{1,2} de (enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)( de \d{4})?)\b",
        r"\b((enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre) de \d{4})\b",
        r"\b(el|los) (pasado|día \d{1,2})\b",
        r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",  # Formato dd/mm/aaaa
    ]
    fechas_encontradas = []
    for patron in patrones_fecha:
        coincidencias = re.findall(patron, texto, re.IGNORECASE)
        for coincidencia in coincidencias:
            if isinstance(coincidencia, tuple):
                fechas_encontradas.append(coincidencia[0])
            else:
                fechas_encontradas.append(coincidencia)
    return fechas_encontradas

# --- FUNCIÓN PARA FORMATEAR LA FECHA EXTRAÍDA ---

def formatear_fecha(fecha_texto):
    fecha_parseada = dateparser.parse(fecha_texto, languages=['es'])
    if fecha_parseada:
        # Determinamos qué componentes tiene la fecha
        componentes = fecha_parseada.timetuple()
        dia = componentes.tm_mday
        mes = componentes.tm_mon
        año = componentes.tm_year

        partes_fecha = []
        # Verificamos si el día fue mencionado explícitamente
        if re.search(r"\b\d{1,2}\b", fecha_texto):
            partes_fecha.append(f"{dia:02d}")
        if re.search(r"(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)", fecha_texto.lower()):
            partes_fecha.append(f"{mes:02d}")
        if re.search(r"\b\d{4}\b", fecha_texto):
            partes_fecha.append(str(año))

        fecha_formateada = "-".join(partes_fecha)
        return fecha_formateada if partes_fecha else fecha_texto
    else:
        return fecha_texto  # Retornamos el texto original si no se pudo parsear

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

# --- FUNCIÓN PARA VERIFICAR Y AGREGAR EL CAMPO SI NO EXISTE ---

def verificar_y_agregar_campo_fecha():
    conexion = conectar_bd()
    try:
        with conexion.cursor() as cursor:
            # Verificar si el campo existe en la tabla
            cursor.execute("SHOW COLUMNS FROM extracciones LIKE 'fecha_secuestro'")
            existe_fecha = cursor.fetchone()

            # Si no existe 'fecha_secuestro', lo agregamos
            if not existe_fecha:
                cursor.execute("ALTER TABLE extracciones ADD COLUMN fecha_secuestro VARCHAR(20)")
                print("Campo 'fecha_secuestro' agregado.")
            conexion.commit()
    finally:
        conexion.close()

# --- FUNCIÓN PARA ACTUALIZAR LA NOTICIA CON LA FECHA DEL SECUESTRO ---

def actualizar_fecha_noticia(id_noticia, fecha_secuestro):
    conexion = conectar_bd()
    try:
        with conexion.cursor() as cursor:
            sql = "UPDATE extracciones SET fecha_secuestro = %s WHERE id = %s"
            cursor.execute(sql, (fecha_secuestro, id_noticia))
            conexion.commit()
    finally:
        conexion.close()

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
    # Verificamos y agregamos el campo si no existe
    verificar_y_agregar_campo_fecha()

    # Obtener y procesar noticias
    noticias = obtener_noticias()
    for noticia in noticias:
        id_noticia = noticia['id']
        texto_noticia = noticia['noticia_corregida']

        # Analizar la fecha del secuestro
        resultado_fecha, fecha_secuestro = extraer_fecha_secuestro(texto_noticia)

        # Mostrar resultados del análisis
        print(f"\n--- Analizando noticia con ID: {id_noticia} ---")
        print(f"{resultado_fecha}")

        # Si se obtuvo una fecha, actualizar la base de datos
        if fecha_secuestro:
            actualizar_fecha_noticia(id_noticia, fecha_secuestro)
        else:
            actualizar_fecha_noticia(id_noticia, "No disponible")

# --- EJECUCIÓN DEL PROGRAMA ---
if __name__ == "__main__":
    procesar_noticias()
