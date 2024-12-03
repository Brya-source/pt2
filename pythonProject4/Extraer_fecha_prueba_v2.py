import pymysql
import spacy
from spacy.matcher import Matcher
import re
import dateparser  # Importamos dateparser
from dateparser.search import search_dates
from datetime import datetime

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
        return "No hay información suficiente sobre la fecha del secuestro.", '', '', ''
    else:
        # Asumimos que la primera fecha detectada es la relevante
        fecha_texto, contexto = fechas_detectadas[0]
        dia, mes, año = obtener_componentes_fecha(fecha_texto)
        resultado = f"Fecha del secuestro: {fecha_texto}\nContexto: '{contexto.strip()}'"
        return resultado, dia, mes, año

# --- FUNCIÓN PARA EXTRAER FECHAS EN UN TEXTO USANDO EXPRESIONES REGULARES ---

def extraer_fechas_en_texto(texto):
    patrones_fecha = [
        r"\b(\d{1,2} de (enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)( de \d{4}| de este año| del año pasado)?)\b",
        r"\b((enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)( de \d{4}| de este año| del año pasado)?)\b",
        r"\b(el|los) (pasado|día \d{1,2}|año pasado)\b",
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

# --- FUNCIÓN PARA OBTENER LOS COMPONENTES DE LA FECHA ---

def obtener_componentes_fecha(fecha_texto):
    # Definimos la fecha base como la fecha actual
    fecha_base = datetime.now()
    # Configuramos dateparser para interpretar fechas relativas
    fecha_parseada = dateparser.parse(
        fecha_texto,
        languages=['es'],
        settings={'RELATIVE_BASE': fecha_base, 'PREFER_DATES_FROM': 'past'}
    )
    if fecha_parseada:
        dia = ''
        mes = ''
        año = ''

        # Verificar si el día está presente en fecha_texto
        if re.search(r'\b\d{1,2}\b', fecha_texto):
            dia = str(fecha_parseada.day)

        # Verificar si el mes está presente en fecha_texto
        meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
                 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
        if any(mes_nombre in fecha_texto.lower() for mes_nombre in meses):
            mes = str(fecha_parseada.month)

        # Verificar si el año está presente en fecha_texto
        if re.search(r'\b\d{4}\b', fecha_texto) or 'este año' in fecha_texto.lower() or 'del año pasado' in fecha_texto.lower():
            año = str(fecha_parseada.year)

        return dia, mes, año
    else:
        return '', '', ''

# --- CONEXIÓN A LA BASE DE DATOS ---

def conectar_bd():
    conexion = pymysql.connect(
        host='localhost',
        user='root',
        password='Soccer.8a',  # Actualiza con tu contraseña
        database='noticias_prueba',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    return conexion

# --- FUNCIÓN PARA VERIFICAR Y AGREGAR CAMPOS SI NO EXISTEN ---

def verificar_y_agregar_campos_fecha():
    conexion = conectar_bd()
    try:
        with conexion.cursor() as cursor:
            # Verificar si los campos existen en la tabla
            campos = ['dia_secuestro', 'mes_secuestro', 'año_secuestro']
            for campo in campos:
                cursor.execute(f"SHOW COLUMNS FROM extracciones LIKE '{campo}'")
                existe_campo = cursor.fetchone()
                if not existe_campo:
                    cursor.execute(f"ALTER TABLE extracciones ADD COLUMN {campo} VARCHAR(10)")
                    print(f"Campo '{campo}' agregado.")
            conexion.commit()
    finally:
        conexion.close()

# --- FUNCIÓN PARA ACTUALIZAR LA NOTICIA CON LA FECHA DEL SECUESTRO ---

def actualizar_fecha_noticia(id_noticia, dia, mes, año):
    conexion = conectar_bd()
    try:
        with conexion.cursor() as cursor:
            sql = """
            UPDATE extracciones SET dia_secuestro = %s, mes_secuestro = %s, año_secuestro = %s WHERE id = %s
            """
            cursor.execute(sql, (dia or '', mes or '', año or '', id_noticia))
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
    # Verificamos y agregamos los campos si no existen
    verificar_y_agregar_campos_fecha()

    # Obtener y procesar noticias
    noticias = obtener_noticias()
    for noticia in noticias:
        id_noticia = noticia['id']
        texto_noticia = noticia['noticia_corregida']

        # Analizar la fecha del secuestro
        resultado_fecha, dia, mes, año = extraer_fecha_secuestro(texto_noticia)

        # Mostrar resultados del análisis
        print(f"\n--- Analizando noticia con ID: {id_noticia} ---")
        print(f"{resultado_fecha}")

        # Actualizar la base de datos con el resultado
        actualizar_fecha_noticia(id_noticia, dia, mes, año)

# --- EJECUCIÓN DEL PROGRAMA ---
if __name__ == "__main__":
    procesar_noticias()
