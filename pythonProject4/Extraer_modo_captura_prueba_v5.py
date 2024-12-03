import pymysql
import spacy
from spacy.matcher import Matcher
import unicodedata

# Cargamos el modelo de spaCy
nlp = spacy.load('es_core_news_md')

def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return ''.join([c for c in nfkd_form if not unicodedata.combining(c)])

# --- FUNCIÓN PARA DETECTAR EL MÉTODO DE CAPTURA ---
def detectar_metodo_captura(texto):
    doc = nlp(texto.lower())
    matcher = Matcher(nlp.vocab)

    # Definir lemas de palabras clave de secuestro
    lemas_clave_secuestro = [
        "secuestro", "secuestrar", "secuestrador", "plagiar", "plagiario",
        "raptar", "rapto", "privar", "desaparicion", "levantar", "retener"
    ]

    # Patrones para identificar diferentes métodos de captura utilizando lemas
    patrones_metodo_captura = [
        # Captura mediante engaño
        [{"LEMMA": {"IN": ["engañar", "fingir", "simular"]}}, {"OP": "+"}],
        [{"LEMMA": {"IN": ["bajo", "mediante"]}}, {"LEMMA": {"IN": ["pretexto", "promesa"]}}, {"OP": "+"}],
        [{"LEMMA": {"IN": ["prometer", "ofrecer"]}}, {"OP": "+"}],

        # Captura mediante uso de la fuerza
        [{"LEMMA": {"IN": ["golpear", "forzar", "someter", "empujar", "agarrar", "amenazar"]}}, {"OP": "+"}],
        [{"LEMMA": {"IN": ["golpeado", "forzado", "sometido", "empujado", "agarrado"]}}, {"OP": "+"}],
        [{"TEXT": {"REGEX": "a punta de pistola|con violencia|bajo amenaza(s)?"}}, {"OP": "+"}],

        # Captura mediante emboscada
        [{"LEMMA": {"IN": ["emboscar", "interceptar", "rodear", "bloquear"]}}, {"OP": "+"}],
        [{"LEMMA": {"IN": ["emboscada"]}}, {"OP": "+"}],
        [{"LEMMA": {"IN": ["emboscar", "interceptar"]}}, {"LEMMA": {"IN": ["en"]}}, {"OP": "+"}],

        # Captura mediante intimidación o amenazas
        [{"LEMMA": {"IN": ["amenazar", "intimidar", "coaccionar", "chantajear"]}}, {"OP": "+"}],
        [{"LEMMA": {"IN": ["amenazado", "intimidado"]}}, {"LEMMA": {"IN": ["con"]}}, {"OP": "+"}],
        [{"TEXT": {"REGEX": "amenaza(s)? de muerte|amenazándolo con"}}, {"OP": "+"}],

        # Captura mediante proximidad o confianza
        [{"TEXT": {"REGEX": "vista por última vez"}}, {"OP": "?"}],
        [{"LEMMA": {"IN": ["casa", "hogar", "amigo", "amiga", "familiar", "pariente"]}}, {"OP": "+"}],
        [{"LEMMA": {"IN": ["cercano", "cercana"]}}, {"OP": "?"}],
        [{"LEMMA": {"IN": ["salir", "meter"]}}, {"LEMMA": {"IN": ["bulto", "taxi"]}}, {"OP": "+"}],

        # Detención o intervención de autoridad (refinada)
        [{"LEMMA": {"IN": ["policía", "agente", "militar", "soldado", "marina", "federal"]}},
         {"LEMMA": {"IN": ["secuestrar", "extorsionar", "detener", "arrestar", "privar"]}}],
        [{"LEMMA": {"IN": ["detener", "arrestar", "capturar"]}},
         {"TEXT": {"REGEX": "ilegalmente|sin motivo|sin justificación|arbitrariamente"}}],

        # Captura en Transporte
        [
            {"LEMMA": {"IN": ["interceptar", "abordar", "secuestrar", "asaltar", "emboscar", "atacar"]}},
            {"OP": "*"},
            {"LEMMA": {"IN": ["autobús", "camioneta", "coche", "vehículo", "taxi", "transporte", "metro", "tren", "camión", "bus"]}}
        ],
        [{"LEMMA": {"IN": ["en", "desde", "hacia"]}}, {"OP": "*"}, {"LEMMA": {"IN": ["autobús", "camioneta", "coche", "vehículo", "taxi", "transporte", "metro", "tren", "camión", "bus"]}}],

        # Método de Extorsión
        [{"LEMMA": {"IN": ["llamar"]}}, {"LEMMA": {"IN": ["extorsionar"]}}],
        [{"LEMMA": {"IN": ["exigir"]}}, {"LEMMA": {"IN": ["dinero", "rescate"]}}],
        [{"LEMMA": {"IN": ["pedir"]}}, {"LEMMA": {"IN": ["rescate"]}}, {"LEMMA": {"IN": ["familiar"]}}],

        # Método Virtual
        [{"LEMMA": {"IN": ["secuestro", "fingir", "simular"]}}, {"LEMMA": {"IN": ["virtual"]}}, {"OP": "?"}],
        [{"LEMMA": {"IN": ["extorsión"]}}, {"LEMMA": {"IN": ["sin"]}}, {"LEMMA": {"IN": ["retención"]}}],

        # Método con Complicidad de Conocidos
        [{"LEMMA": {"IN": ["amigo", "conocido", "confianza", "familiar", "pariente", "cómplice"]}}, {"OP": "+"}],
        [{"LEMMA": {"IN": ["complicidad"]}}, {"OP": "?"}, {"LEMMA": {"IN": ["cercano", "cercana"]}}, {"OP": "?"}],

        # Suplantación de identidad (mejorada)
        [{"LEMMA": {"IN": ["hacerse pasar", "suplantar", "fingir ser", "imitar", "aparentar", "simular"]}},
         {"OP": "*"},
         {"LEMMA": {"IN": ["policía", "agente", "autoridad", "militar", "soldado", "funcionario", "empleado"]}}]
    ]

    # Añadimos los patrones al matcher enfocándonos en el método de captura
    matcher.add("Captura_Engaño", [patrones_metodo_captura[0], patrones_metodo_captura[1], patrones_metodo_captura[2]])
    matcher.add("Captura_Fuerza", [patrones_metodo_captura[3], patrones_metodo_captura[4], patrones_metodo_captura[5]])
    matcher.add("Captura_Emboscada", [patrones_metodo_captura[6], patrones_metodo_captura[7], patrones_metodo_captura[8]])
    matcher.add("Captura_Intimidacion", [patrones_metodo_captura[9], patrones_metodo_captura[10], patrones_metodo_captura[11]])
    matcher.add("Captura_Confianza", [patrones_metodo_captura[12], patrones_metodo_captura[13], patrones_metodo_captura[14], patrones_metodo_captura[15]])
    matcher.add("Captura_Autoridad", [patrones_metodo_captura[16], patrones_metodo_captura[17]])
    matcher.add("Captura_Transporte", [patrones_metodo_captura[18], patrones_metodo_captura[19]])
    matcher.add("Captura_Extorsion", [patrones_metodo_captura[20], patrones_metodo_captura[21], patrones_metodo_captura[22]])
    matcher.add("Captura_Virtual", [patrones_metodo_captura[23], patrones_metodo_captura[24]])
    matcher.add("Captura_Complicidad", [patrones_metodo_captura[25], patrones_metodo_captura[26]])
    matcher.add("Suplantacion_Identidad", [patrones_metodo_captura[27]])

    explicacion = {}
    metodos_detectados = set()
    intento_secuestro = False
    suplantacion_detectada = False

    oraciones_ignoradas = set()
    palabras_clave_reporte = ["reportó", "denunció", "informó", "declaró"]
    palabras_clave_contexto_policial = ["detenido", "arrestado", "capturado", "investigado", "acusado"]

    matches = matcher(doc)
    for match_id, start, end in matches:
        span = doc[start:end]
        oracion_completa = span.sent
        metodo = nlp.vocab.strings[match_id]

        # Verificar si la referencia es un reporte o contexto policial no relevante
        if any(palabra in oracion_completa.text for palabra in palabras_clave_reporte + palabras_clave_contexto_policial):
            continue  # Saltar esta coincidencia

        # Verificar si la oración tiene relación con secuestro utilizando lemas
        contexto_secuestro = any(token.lemma_ in lemas_clave_secuestro for token in oracion_completa)
        if not contexto_secuestro:
            continue  # Saltar esta coincidencia

        # Verificar construcción semántica de intento de secuestro
        if any(palabra in oracion_completa.text for palabra in ["intento", "intentó", "intentar", "no logró"]):
            intento_secuestro = True
            explicacion["Intento_Secuestro"] = f"Intento de secuestro detectado con contexto: '{oracion_completa.text}'"
        else:
            # Detectar y registrar suplantación de identidad
            if metodo == "Suplantacion_Identidad":
                suplantacion_detectada = True
                explicacion["Suplantacion_Identidad"] = f"Se detectó suplantación de identidad: '{oracion_completa.text}'"

            # Agregar el método detectado al conjunto de métodos de captura
            metodos_detectados.add(metodo)
            if metodo not in explicacion:
                explicacion[metodo] = f"Método de captura detectado: '{metodo}'. Contexto: '{oracion_completa.text}'"

    # Si no se detectó ningún método de captura y hay indicios de intento
    if not metodos_detectados and intento_secuestro:
        metodos_detectados.add("Intento_Secuestro")
        explicacion["Intento_Secuestro"] = "Clasificación asignada como 'Intento de Secuestro' debido a contexto de intento detectado."

    # Si se detectó suplantación y un método relevante, agregarlo como una combinación
    if suplantacion_detectada:
        if "Captura_Autoridad" in metodos_detectados:
            metodos_detectados.add("Suplantacion_Identidad_Autoridad")
            explicacion["Suplantacion_Identidad_Autoridad"] = "Suplantación de identidad detectada para simular autoridad."
        elif "Captura_Confianza" in metodos_detectados:
            metodos_detectados.add("Suplantacion_Identidad_Confianza")
            explicacion["Suplantacion_Identidad_Confianza"] = "Suplantación de identidad detectada para simular confianza."

    metodos_final = list(metodos_detectados)
    explicaciones_final = [explicacion[metodo] for metodo in metodos_final]

    return metodos_final, explicaciones_final

# --- CONEXIÓN A LA BASE DE DATOS ---

def conectar_bd():
    conexion = pymysql.connect(
        host='localhost',
        user='root',
        password='Soccer.8a',  # Reemplaza con tu contraseña
        database='noticias_prueba',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    return conexion

# --- FUNCIÓN PARA VERIFICAR Y CREAR LA TABLA 'capturas_noticias' ---

def verificar_y_crear_tabla():
    conexion = conectar_bd()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS capturas_noticias (
                    noticia_id INT PRIMARY KEY,
                    captura_engaño TINYINT(1) DEFAULT 0,
                    captura_fuerza TINYINT(1) DEFAULT 0,
                    captura_emboscada TINYINT(1) DEFAULT 0,
                    captura_intimidacion TINYINT(1) DEFAULT 0,
                    captura_confianza TINYINT(1) DEFAULT 0,
                    captura_autoridad TINYINT(1) DEFAULT 0,
                    captura_transporte TINYINT(1) DEFAULT 0,
                    captura_extorsion TINYINT(1) DEFAULT 0,
                    captura_virtual TINYINT(1) DEFAULT 0,
                    captura_complicidad TINYINT(1) DEFAULT 0,
                    suplantacion_identidad TINYINT(1) DEFAULT 0
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            conexion.commit()
    except pymysql.MySQLError as e:
        print(f"Error al verificar o crear la tabla: {e}")
        conexion.rollback()
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

# --- FUNCIÓN PARA GUARDAR RESULTADOS ---
def guardar_resultados_captura(noticia_id, metodos_detectados):
    conexion = conectar_bd()

    datos_captura = {
        "captura_engaño": 0,
        "captura_fuerza": 0,
        "captura_emboscada": 0,
        "captura_intimidacion": 0,
        "captura_confianza": 0,
        "captura_autoridad": 0,
        "captura_transporte": 0,
        "captura_extorsion": 0,
        "captura_virtual": 0,
        "captura_complicidad": 0,
        "suplantacion_identidad": 0
    }

    for metodo in metodos_detectados:
        columna = metodo.lower().replace("captura_", "")
        columna = remove_accents(columna)
        columna = f"captura_{columna}" if "suplantacion" not in columna else columna
        if columna in datos_captura:
            datos_captura[columna] = 1

    try:
        with conexion.cursor() as cursor:
            sql = """
            INSERT INTO capturas_noticias (noticia_id, captura_engaño, captura_fuerza, captura_emboscada, 
                                            captura_intimidacion, captura_confianza, captura_autoridad, 
                                            captura_transporte, captura_extorsion, captura_virtual, 
                                            captura_complicidad, suplantacion_identidad)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                captura_engaño = VALUES(captura_engaño),
                captura_fuerza = VALUES(captura_fuerza),
                captura_emboscada = VALUES(captura_emboscada),
                captura_intimidacion = VALUES(captura_intimidacion),
                captura_confianza = VALUES(captura_confianza),
                captura_autoridad = VALUES(captura_autoridad),
                captura_transporte = VALUES(captura_transporte),
                captura_extorsion = VALUES(captura_extorsion),
                captura_virtual = VALUES(captura_virtual),
                captura_complicidad = VALUES(captura_complicidad),
                suplantacion_identidad = VALUES(suplantacion_identidad)
            """
            cursor.execute(sql, (noticia_id,
                                 datos_captura["captura_engaño"],
                                 datos_captura["captura_fuerza"],
                                 datos_captura["captura_emboscada"],
                                 datos_captura["captura_intimidacion"],
                                 datos_captura["captura_confianza"],
                                 datos_captura["captura_autoridad"],
                                 datos_captura["captura_transporte"],
                                 datos_captura["captura_extorsion"],
                                 datos_captura["captura_virtual"],
                                 datos_captura["captura_complicidad"],
                                 datos_captura["suplantacion_identidad"]))
        conexion.commit()
    except pymysql.MySQLError as e:
        print(f"Error al guardar los resultados: {e}")
        conexion.rollback()
    finally:
        conexion.close()

# --- PROCESAR Y ANALIZAR NOTICIAS ---
def procesar_noticias():
    # Verificar y crear la tabla si no existe
    verificar_y_crear_tabla()

    noticias = obtener_noticias()
    for noticia in noticias:
        id_noticia = noticia['id']
        texto_noticia = noticia['noticia_corregida']
        metodos_captura, explicacion_captura = detectar_metodo_captura(texto_noticia)

        # Guardar resultados en la base de datos
        guardar_resultados_captura(id_noticia, metodos_captura)

        # Imprimir la justificación de las asignaciones
        for exp in explicacion_captura:
            print(f"Noticia ID {id_noticia}: {exp}")

# --- EJECUCIÓN DEL PROGRAMA ---
if __name__ == "__main__":
    procesar_noticias()
