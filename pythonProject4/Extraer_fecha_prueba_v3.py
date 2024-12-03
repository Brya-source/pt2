import pymysql
import spacy
from spacy.matcher import Matcher
import re
import dateparser
from dateparser.search import search_dates
from datetime import datetime

# Cargamos el modelo de spaCy
nlp = spacy.load('es_core_news_md')

# --- FUNCIÓN PARA EXTRAER LA FECHA DEL SECUESTRO ---

def extraer_fecha_secuestro(texto, fecha_publicacion):
    doc = nlp(texto.lower())

    # Inicializamos el Matcher de spaCy
    matcher = Matcher(nlp.vocab)

    # Patrones para identificar oraciones relacionadas con el secuestro
    patrones_secuestro = [
        [{"LEMMA": {"IN": ["secuestro", "privar", "raptar", "levantar"]}}],
        [{"TEXT": {"REGEX": "privado de su libertad|privada de su libertad"}}],
        [{"LEMMA": {"IN": ["ocurrir", "suceder", "registrar"]}},
         {"POS": "ADP", "OP": "?"}, {"LOWER": "el", "OP": "?"},
         {"LOWER": "secuestro"}],
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

    # Si no se detectó ninguna fecha en contextos relevantes, utilizamos la fecha de publicación
    if not fechas_detectadas:
        dia_pub, mes_pub, año_pub = extraer_fecha_publicacion(fecha_publicacion)
        return "No se encontró fecha en el texto; se utiliza la fecha de publicación.", dia_pub, mes_pub, año_pub
    else:
        # Asumimos que la primera fecha detectada es la relevante
        fecha_texto, contexto = fechas_detectadas[0]
        dia, mes, año = obtener_componentes_fecha(fecha_texto, texto)
        # Si no se pudo obtener el año numérico, verificamos la fecha de publicación
        if not año:
            dia_pub, mes_pub, año_pub = extraer_fecha_publicacion(fecha_publicacion)
            año = año_pub
        if not mes:
            dia_pub, mes_pub, año_pub = extraer_fecha_publicacion(fecha_publicacion)
            mes = mes_pub
        resultado = f"Fecha del secuestro: {fecha_texto}\nContexto: '{contexto.strip()}'"
        return resultado, dia, mes, año

# --- FUNCIÓN PARA EXTRAER FECHAS EN UN TEXTO USANDO EXPRESIONES REGULARES ---

def extraer_fechas_en_texto(texto):
    patrones_fecha = [
        r"\b(\d{1,2} de (enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)( de \d{4})?)\b",
        r"\b((enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre) de \d{4})\b",
        r"\b(\d{1,2}/\d{1,2}/\d{2,4})\b",  # Formato dd/mm/aaaa
        r"\b(este año|el año pasado|este mes|el mes pasado)\b",
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

def obtener_componentes_fecha(fecha_texto, texto_completo):
    fecha_base = datetime.now()

    # Ajustamos la fecha base si en el texto se menciona "este año", "el año pasado", etc.
    if 'el año pasado' in fecha_texto.lower():
        fecha_base = fecha_base.replace(year=fecha_base.year - 1)
    elif 'este año' in fecha_texto.lower():
        pass  # Usamos el año actual
    elif 'este mes' in fecha_texto.lower():
        pass  # Usamos el mes actual
    elif 'el mes pasado' in fecha_texto.lower():
        mes_anterior = fecha_base.month - 1 if fecha_base.month > 1 else 12
        año_ajustado = fecha_base.year if fecha_base.month > 1 else fecha_base.year - 1
        fecha_base = fecha_base.replace(month=mes_anterior, year=año_ajustado)

    fecha_parseada = dateparser.parse(
        fecha_texto,
        languages=['es'],
        settings={'RELATIVE_BASE': fecha_base, 'PREFER_DATES_FROM': 'past'}
    )

    dia = ''
    mes = ''
    año = ''

    if fecha_parseada:
        # Verificar si el día está presente en fecha_texto
        if re.search(r'\b\d{1,2}\b', fecha_texto):
            dia = str(fecha_parseada.day)

        # Verificar si el mes está presente en fecha_texto
        meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
                 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
        if any(mes_nombre in fecha_texto.lower() for mes_nombre in meses):
            mes = str(fecha_parseada.month)

        # Verificar si el año está presente en fecha_texto
        if re.search(r'\b\d{4}\b', fecha_texto):
            año = str(fecha_parseada.year)
        elif 'el año pasado' in fecha_texto.lower() or 'este año' in fecha_texto.lower():
            año = str(fecha_parseada.year)

    return dia, mes, año

# --- FUNCIÓN PARA EXTRAER LA FECHA DE PUBLICACIÓN ---

def extraer_fecha_publicacion(fecha_publicacion_texto):
    # Asumimos que el formato es '| dd/mm/aaaa | hh:mm |'
    match = re.search(r'\|\s*(\d{1,2}/\d{1,2}/\d{4})\s*\|', fecha_publicacion_texto)
    if match:
        fecha_str = match.group(1)
        fecha_pub = datetime.strptime(fecha_str, '%d/%m/%Y')
        dia = str(fecha_pub.day)
        mes = str(fecha_pub.month)
        año = str(fecha_pub.year)
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
            sql = "SELECT id, noticia_corregida, fecha FROM extracciones WHERE relacion_spacy4 = 'Sí' LIMIT 100"
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
        fecha_publicacion = noticia['fecha']

        # Analizar la fecha del secuestro
        resultado_fecha, dia, mes, año = extraer_fecha_secuestro(texto_noticia, fecha_publicacion)

        # Mostrar resultados del análisis
        print(f"\n--- Analizando noticia con ID: {id_noticia} ---")
        print(f"{resultado_fecha}")

        # Actualizar la base de datos con el resultado
        actualizar_fecha_noticia(id_noticia, dia, mes, año)

# --- EJECUCIÓN DEL PROGRAMA ---
if __name__ == "__main__":
    procesar_noticias()
