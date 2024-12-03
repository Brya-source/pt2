import pymysql
import spacy
from spacy.matcher import Matcher

# Cargamos el modelo de spaCy
nlp = spacy.load('es_core_news_md')

# --- FUNCIONES PARA DETECTAR EL MÉTODO DE CAPTURA ---
def detectar_metodo_captura(texto):
    doc = nlp(texto.lower())
    matcher = Matcher(nlp.vocab)

    # Patrones para identificar diferentes métodos de captura conocidos
    patrones_metodo_captura = [
        # Captura mediante engaño
        [{"LEMMA": {"IN": ["engañar", "fingir", "simular", "hacerse pasar"]}}, {"OP": "+"}],
        [{"TEXT": {"REGEX": "(bajo|mediante) (pretextos|promesas)"}}, {"OP": "+"}],
        [{"TEXT": {"REGEX": "prometiendo|ofrecieron"}}, {"OP": "+"}],

        # Captura mediante uso de la fuerza
        [{"LEMMA": {"IN": ["golpear", "forzar", "someter", "empujar", "agarrar"]}}, {"OP": "+"}],
        [{"TEXT": {"REGEX": "(golpeado|forzado|sometido|empujado|agarrado)"}}, {"OP": "+"}],
        [{"TEXT": {"REGEX": "a punta de pistola|con violencia|bajo amenazas"}}, {"OP": "+"}],

        # Captura mediante emboscada
        [{"LEMMA": {"IN": ["emboscar", "interceptar", "rodear", "bloquear"]}}, {"OP": "+"}],
        [{"TEXT": {"REGEX": "en una emboscada|interceptaron su vehículo"}}, {"OP": "+"}],
        [{"TEXT": {"REGEX": "(emboscado|interceptado) en"}}, {"OP": "+"}],

        # Captura mediante intimidación o amenazas
        [{"LEMMA": {"IN": ["amenazar", "intimidar", "coaccionar", "chantajear"]}}, {"OP": "+"}],
        [{"TEXT": {"REGEX": "(amenazado|intimidado) con"}}, {"OP": "+"}],
        [{"TEXT": {"REGEX": "amenazas de muerte|amenazándolo con"}}, {"OP": "+"}],

        # Captura mediante proximidad o confianza
        [{"TEXT": {"REGEX": "vista por última vez"}}, {"OP": "?"}],
        [{"TEXT": {"REGEX": "casa de|hogar de|amigo|amiga"}}, {"OP": "+"}],
        [{"TEXT": {"REGEX": "cercano"}}, {"OP": "?"}],
        [{"TEXT": {"REGEX": "salieron con bultos|metieron en un taxi"}}, {"OP": "+"}],

        # Detención o intervención de autoridad
        [{"TEXT": {"REGEX": "policía|policías|agente|agentes|fiscalía|detenidos|fiscales"}}, {"OP": "+"}],
        [{"TEXT": {"REGEX": "fuerzas armadas|ejército|autoridades"}}, {"OP": "?"}],
        [{"TEXT": {"REGEX": "detenidos por|retención por"}}, {"OP": "+"}],
        [{"TEXT": {"REGEX": "arresto|intervención de"}}, {"OP": "+"}],

        # Método en Transporte Público o en Tránsito
        [{"TEXT": {"REGEX": "autobús|camioneta|vehículo interceptado|taxi"}}, {"OP": "+"}],
        [{"TEXT": {"REGEX": "camino a su destino"}}, {"OP": "?"}],

        # Método de Extorsión
        [{"TEXT": {"REGEX": "llamadas de extorsión|exigencias de dinero"}}, {"OP": "+"}],
        [{"TEXT": {"REGEX": "pedir rescate a familiares"}}, {"OP": "?"}],

        # Método Virtual
        [{"TEXT": {"REGEX": "secuestro virtual|fingido|simulación de secuestro"}}, {"OP": "+"}],
        [{"TEXT": {"REGEX": "extorsión sin retención"}}, {"OP": "?"}],

        # Método con Complicidad de Conocidos
        [{"TEXT": {"REGEX": "amigo|conocido|persona de confianza"}}, {"OP": "+"}],
        [{"TEXT": {"REGEX": "complicidad|fue llevado por alguien cercano"}}, {"OP": "?"}],

        # Método de Cárteles o Grupos Criminales
        [{"TEXT": {"REGEX": "cártel|grupo criminal|La Familia"}}, {"OP": "+"}],
        [{"TEXT": {"REGEX": "vinculado a cartel|como represalia"}}, {"OP": "?"}],

        # Suplantación de identidad
        [{"LEMMA": {"IN": ["hacerse", "suplantar", "pretender", "imitar", "aparentar"]}}, {"TEXT": {"REGEX": "policía|agente|amigo|familiar"}}]
    ]

    # Añadimos los patrones al matcher enfocándonos en el método de captura
    matcher.add("Captura_Engaño", [patrones_metodo_captura[0], patrones_metodo_captura[1], patrones_metodo_captura[2]])
    matcher.add("Captura_Fuerza", [patrones_metodo_captura[3], patrones_metodo_captura[4], patrones_metodo_captura[5]])
    matcher.add("Captura_Emboscada", [patrones_metodo_captura[6], patrones_metodo_captura[7], patrones_metodo_captura[8]])
    matcher.add("Captura_Intimidación", [patrones_metodo_captura[9], patrones_metodo_captura[10], patrones_metodo_captura[11]])
    matcher.add("Captura_Confianza", [patrones_metodo_captura[12], patrones_metodo_captura[13], patrones_metodo_captura[14], patrones_metodo_captura[15]])
    matcher.add("Captura_Autoridad", [patrones_metodo_captura[16], patrones_metodo_captura[17], patrones_metodo_captura[18], patrones_metodo_captura[19]])
    matcher.add("Captura_Transporte", [patrones_metodo_captura[20], patrones_metodo_captura[21]])
    matcher.add("Captura_Extorsion", [patrones_metodo_captura[22], patrones_metodo_captura[23]])
    matcher.add("Captura_Virtual", [patrones_metodo_captura[24], patrones_metodo_captura[25]])
    matcher.add("Captura_Complicidad", [patrones_metodo_captura[26], patrones_metodo_captura[27]])
    matcher.add("Captura_Cartel", [patrones_metodo_captura[28], patrones_metodo_captura[29]])
    matcher.add("Suplantacion_Identidad", [patrones_metodo_captura[30]])

    explicacion = {}  # Diccionario para almacenar explicaciones de cada método de captura
    metodos_detectados = set()  # Usar un conjunto para evitar duplicados
    intento_secuestro = False  # Variable para asignar intento de secuestro si la construcción es ambigua
    suplantacion_detectada = False  # Para identificar si hubo suplantación de identidad

    # Conjunto para evitar impresiones duplicadas de oraciones ignoradas
    oraciones_ignoradas = set()
    palabras_clave_reporte = ["reportó", "denunció", "informó a la policía", "declaró a las autoridades"]
    palabras_clave_sospechosos = ["sospechoso", "detención de criminales", "arresto de implicados", "detención de secuestradores"]

    matches = matcher(doc)
    if not matches:
        print("No se encontraron coincidencias en el texto.")

    for match_id, start, end in matches:
        span = doc[start:end]
        oracion_completa = span.sent.text
        metodo = nlp.vocab.strings[match_id]

        # Verificar si la referencia a la policía o autoridad es un reporte, no captura
        if metodo == "Captura_Autoridad" and any(palabra in oracion_completa for palabra in palabras_clave_reporte):
            if oracion_completa not in oraciones_ignoradas:
                oraciones_ignoradas.add(oracion_completa)
            continue  # Saltar esta coincidencia para no clasificarla como Captura_Autoridad

        # Verificar construcción semántica de intento de secuestro
        if any(palabra in oracion_completa for palabra in ["intento", "intentó", "intentar", "no logró"]):
            intento_secuestro = True
            explicacion["Intento_Secuestro"] = f"Intento de secuestro detectado con contexto: '{oracion_completa}'"
        else:
            # Detectar y registrar suplantación de identidad
            if metodo == "Suplantacion_Identidad":
                suplantacion_detectada = True
                explicacion["Suplantacion_Identidad"] = f"Se detectó suplantación de identidad: '{oracion_completa}'"

            # Agregar el método detectado al conjunto de métodos de captura
            metodos_detectados.add(metodo)
            if metodo not in explicacion:
                explicacion[metodo] = f"Método de captura detectado: '{metodo}'. Contexto completo: '{oracion_completa}'"

    # Imprimir mensaje de ignorado solo una vez por cada oración descartada
    for oracion in oraciones_ignoradas:
        print(f"Ignorado como método de captura por tratarse de un reporte: '{oracion}'")

    # Si no se detectó ningún método de captura y hay indicios de intento
    if not metodos_detectados and intento_secuestro:
        metodos_detectados.add("Intento_Secuestro")
        explicacion["Intento_Secuestro"] = "Clasificación asignada como 'Intento de Secuestro' debido a contexto de intento detectado."

    # Si se detectó suplantación y un método relevante (como autoridad o confianza), agregarlo como una combinación
    if suplantacion_detectada:
        if "Captura_Autoridad" in metodos_detectados:
            metodos_detectados.add("Suplantacion_Identidad_Autoridad")
            explicacion["Suplantacion_Identidad_Autoridad"] = "Suplantación de identidad detectada para simular autoridad."
        elif "Captura_Confianza" in metodos_detectados:
            metodos_detectados.add("Suplantacion_Identidad_Confianza")
            explicacion["Suplantacion_Identidad_Confianza"] = "Suplantación de identidad detectada para simular proximidad o confianza."

    # Convertir el conjunto a una lista y seleccionar la justificación más significativa (primera ocurrencia)
    metodos_final = list(metodos_detectados)
    explicaciones_final = [explicacion[metodo] for metodo in metodos_detectados]

    return list(metodos_detectados), [explicacion[metodo] for metodo in metodos_detectados]

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
                    captura_cartel TINYINT(1) DEFAULT 0,
                    suplantacion_identidad TINYINT(1) DEFAULT 0
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            conexion.commit()
            print("Tabla 'capturas_noticias' verificada/creada exitosamente.")
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
        "captura_cartel": 0,
        "suplantacion_identidad": 0
    }

    for metodo in metodos_detectados:
        columna = metodo.lower().replace("captura_", "")
        columna = f"captura_{columna}" if "suplantacion" not in columna else columna
        if columna in datos_captura:
            datos_captura[columna] = 1

    try:
        with conexion.cursor() as cursor:
            sql = """
            INSERT INTO capturas_noticias (noticia_id, captura_engaño, captura_fuerza, captura_emboscada, 
                                            captura_intimidacion, captura_confianza, captura_autoridad, 
                                            captura_transporte, captura_extorsion, captura_virtual, 
                                            captura_complicidad, captura_cartel, suplantacion_identidad)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                captura_cartel = VALUES(captura_cartel),
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
                                 datos_captura["captura_cartel"],
                                 datos_captura["suplantacion_identidad"]))
        conexion.commit()
        print(f"Resultados guardados exitosamente para la noticia ID {noticia_id}")
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
        print(f"\n--- Analizando noticia con ID: {id_noticia} ---")
        metodos_captura, explicacion_captura = detectar_metodo_captura(texto_noticia)

        # Guardar resultados en la base de datos
        guardar_resultados_captura(id_noticia, metodos_captura)

        # Imprimir la explicación
        for exp in explicacion_captura:
            print(f"- {exp}")

        if metodos_captura:
            print(f"Métodos de captura detectados: {', '.join(metodos_captura)}")
        else:
            print("Método de captura: No detectado")


# --- EJECUCIÓN DEL PROGRAMA ---
if __name__ == "__main__":
    procesar_noticias()
