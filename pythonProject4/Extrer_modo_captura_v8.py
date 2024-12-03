import pymysql
import spacy
from spacy.matcher import Matcher

# Cargamos el modelo de spaCy
nlp = spacy.load('es_core_news_md')

# --- FUNCIÓN PARA DETECTAR CARACTERÍSTICAS ---
def detectar_metodo_captura(texto):
    doc = nlp(texto.lower())
    matcher = Matcher(nlp.vocab)

    # Definimos los patrones como un diccionario
    patrones_metodo_captura = {
        "Captura_Fuerza": [
            [{"LEMMA": {"IN": ["golpear", "forzar", "someter", "empujar", "agarrar"]}}],
            [{"TEXT": {"REGEX": "(golpeado|forzado|sometido|empujado|agarrado)"}}],
            [{"TEXT": {"REGEX": "a punta de pistola|con violencia|bajo amenazas"}}],
        ],
        "Captura_Emboscada": [
            [{"LEMMA": {"IN": ["emboscar", "interceptar", "rodear", "bloquear"]}}],
            [{"TEXT": {"REGEX": "en una emboscada|interceptaron su vehículo"}}],
            [{"TEXT": {"REGEX": "(emboscado|interceptado) en"}}],
        ],
        "Captura_Intimidacion": [
            [{"LEMMA": {"IN": ["amenazar", "intimidar", "coaccionar", "chantajear"]}}],
            [{"TEXT": {"REGEX": "(amenazado|intimidado) con"}}],
            [{"TEXT": {"REGEX": "amenazas de muerte|amenazándolo con"}}],
        ],
        "Captura_Tecnologica": [
            [
                {"TEXT": {"REGEX": "contactó|contactaron|engañado|engañada|citó|citaron"}},
                {"OP": "*"},
                {"TEXT": {"REGEX": "facebook|twitter|redes sociales|internet|aplicación móvil|app de citas"}}
            ],
            [
                {"LEMMA": {"IN": ["conocer", "interactuar"]}},
                {"TEXT": {"REGEX": "en línea|por internet|por redes sociales"}}
            ],
        ],
        "Captura_Confianza": [
            [{"TEXT": {"REGEX": "amigo|amiga|familiar|conocido|cercano"}}],
            [{"TEXT": {"REGEX": "persona de confianza|relación cercana"}}],
        ],
        "Captura_Autoridad": [
            [
                {"LEMMA": {"IN": ["policía", "policías", "agente", "agentes", "militar", "militares", "ejército", "autoridad", "autoridades"]}},
                {"OP": "+"},
                {"LEMMA": {"IN": ["secuestrar", "privar", "detener"]}, "OP": "+"}
            ],
        ],
        "Captura_Transporte": [
            [{"TEXT": {"REGEX": "autobús|camioneta|vehículo interceptado|taxi|transporte público"}}],
            [{"TEXT": {"REGEX": "camino a su destino|en tránsito|en ruta"}}],
        ],
        "Captura_Complicidad": [
            [{"TEXT": {"REGEX": "empleado|empleada|colaborador|compañero"}}],
            [{"TEXT": {"REGEX": "complicidad|alguien del entorno laboral"}}],
        ],
        "Captura_Cartel": [
            [{"TEXT": {"REGEX": "cártel|grupo criminal|La Familia|Los Zetas"}}],
            [{"TEXT": {"REGEX": "vinculado a cartel|como represalia"}}],
        ],
        "Suplantacion_Identidad": [
            [{"LEMMA": {"IN": ["hacerse", "suplantar", "pretender", "imitar", "aparentar", "fingir", "simular"]}},
             {"OP": "*"},
             {"LEMMA": {"IN": ["policía", "agente", "militar", "autoridad", "funcionario"]}}]
        ],
        "Captura_Casa": [
            [{"TEXT": {"REGEX": "en su (propia )?casa|en su (propio )?domicilio|cerca de su hogar|afuera de su casa|entrando a su casa|saliendo de su casa"}}],
            [{"LEMMA": {"IN": ["hogar", "casa", "domicilio"]}}],
            [{"TEXT": {"REGEX": "propiedad"}}],
        ],
    }

    # Añadimos los patrones al matcher
    for method_name, patterns in patrones_metodo_captura.items():
        matcher.add(method_name, patterns)

    captor_methods = []
    lugar_methods = []
    captura_methods = []  # Cambiado a lista
    suplantacion_detectada = False
    explicacion = {}  # Diccionario para almacenar explicaciones de cada método

    # Conjunto para evitar impresiones duplicadas de oraciones ignoradas
    oraciones_ignoradas = set()
    palabras_clave_reporte = ["reportó", "denunció", "informó a la policía", "declaró a las autoridades"]
    palabras_clave_victima = ["policía fue secuestrado", "agente fue secuestrado", "militar fue secuestrado"]

    matches = matcher(doc)
    if not matches:
        print("No se encontraron coincidencias en el texto.")

    for match_id, start, end in matches:
        span = doc[start:end]
        oracion_completa = span.sent.text
        metodo = nlp.vocab.strings[match_id]

        # Verificar si la referencia a la autoridad es un reporte o la autoridad es víctima
        if metodo == "Captura_Autoridad":
            # Si la oración contiene palabras que indican que es un reporte, ignorar
            if any(palabra in oracion_completa for palabra in palabras_clave_reporte):
                if oracion_completa not in oraciones_ignoradas:
                    oraciones_ignoradas.add(oracion_completa)
                continue  # No clasificar como Captura_Autoridad

            # Si la autoridad es víctima, ignorar
            if any(palabra in oracion_completa for palabra in palabras_clave_victima):
                continue  # No clasificar como Captura_Autoridad

            # **Nueva Verificación**: Comprobar que están perpetrando un secuestro o privación de libertad
            palabras_clave_acciones = ["secuestrar", "secuestro", "privación de libertad", "privar de libertad", "raptar"]
            if not any(palabra in oracion_completa for palabra in palabras_clave_acciones):
                continue

            # Si llega aquí, la autoridad es el perpetrador de secuestro o privación de libertad
            if not captor_methods:
                captor_methods.append("autoridad")
                explicacion[metodo] = f"Método de captor detectado: 'autoridad'. Contexto: '{oracion_completa}'"
            continue  # Pasar a la siguiente coincidencia

        # Detectar y registrar suplantación de identidad
        if metodo == "Suplantacion_Identidad":
            suplantacion_detectada = True
            if not captor_methods:
                captor_methods.append("suplantación de identidad")
                explicacion["Suplantacion_Identidad"] = f"Se detectó suplantación de identidad: '{oracion_completa}'"
            continue  # Pasar a la siguiente coincidencia

        # Procesar métodos de captor
        if metodo in ["Captura_Confianza", "Captura_Cartel", "Captura_Complicidad"]:
            captor_name = metodo.split('_')[1].lower()  # Obtener 'confianza', 'cartel', 'complicidad'
            if not captor_methods:
                captor_methods.append(captor_name)
                explicacion[metodo] = f"Método de captor detectado: '{captor_name}'. Contexto: '{oracion_completa}'"

        # Procesar métodos de lugar
        if metodo in ["Captura_Transporte", "Captura_Casa"]:
            lugar_name = metodo.split('_')[1].lower()  # Obtener 'transporte', 'casa'
            if not lugar_methods:
                lugar_methods.append(lugar_name)
                explicacion[metodo] = f"Lugar detectado: '{lugar_name}'. Contexto: '{oracion_completa}'"

        # Procesar métodos de captura
        if metodo in ["Captura_Fuerza", "Captura_Emboscada", "Captura_Intimidacion", "Captura_Tecnologica"]:
            captura_name = metodo.split('_')[1].lower()  # Obtener 'fuerza', 'emboscada', etc.
            if not captura_methods:
                captura_methods.append(captura_name)
                explicacion[metodo] = f"Método de captura detectado: '{captura_name}'. Contexto: '{oracion_completa}'"

    # Si no se detectó captor, asignar 'persona común'
    if not captor_methods:
        captor_methods.append("persona común")

    # Si no se detectó lugar, asignar 'vía pública'
    if not lugar_methods:
        lugar_methods.append("vía pública")

    # Asignar 'no especifico' si no se detectó método de captura
    if not captura_methods:
        captura = "no especifico"
    else:
        captura = captura_methods[0]  # Solo el primero

    # Convertir listas a cadenas
    captor = captor_methods[0]  # Solo el primero
    lugar = lugar_methods[0]  # Solo el primero

    # Preparar explicaciones
    explicaciones_final = list(explicacion.values())

    return captor, lugar, captura, explicaciones_final

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

# --- FUNCIÓN PARA VERIFICAR Y CREAR CAMPOS EN LA TABLA 'extracciones' ---
def verificar_y_crear_campos():
    conexion = conectar_bd()
    try:
        with conexion.cursor() as cursor:
            # Obtener las columnas existentes en la tabla
            cursor.execute("SHOW COLUMNS FROM extracciones")
            columnas = [row['Field'] for row in cursor.fetchall()]

            # Lista de nuevos campos que queremos agregar
            nuevos_campos = {
                'captor': "VARCHAR(255) DEFAULT NULL",
                'lugar': "VARCHAR(255) DEFAULT NULL",
                'captura': "VARCHAR(255) DEFAULT NULL"
            }

            # Iterar sobre los nuevos campos y agregarlos si no existen
            for campo, definicion in nuevos_campos.items():
                if campo not in columnas:
                    sql_alter = f"ALTER TABLE extracciones ADD COLUMN {campo} {definicion};"
                    cursor.execute(sql_alter)
                    print(f"Campo '{campo}' agregado a la tabla 'extracciones'.")
        conexion.commit()
    except pymysql.MySQLError as e:
        print(f"Error al verificar o agregar campos: {e}")
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

# --- FUNCIÓN PARA GUARDAR RESULTADOS EN EXTRACCIONES ---
def guardar_resultados_en_extracciones(noticia_id, captor, lugar, captura):
    conexion = conectar_bd()
    try:
        with conexion.cursor() as cursor:
            sql = """
            UPDATE extracciones
            SET captor = %s, lugar = %s, captura = %s
            WHERE id = %s
            """
            cursor.execute(sql, (captor, lugar, captura, noticia_id))
        conexion.commit()
        print(f"Resultados guardados exitosamente para la noticia ID {noticia_id}")
    except pymysql.MySQLError as e:
        print(f"Error al guardar los resultados en 'extracciones': {e}")
        conexion.rollback()
    finally:
        conexion.close()

# --- PROCESAR Y ANALIZAR NOTICIAS ---
def procesar_noticias():
    # Verificar y crear los campos necesarios
    verificar_y_crear_campos()

    noticias = obtener_noticias()
    for noticia in noticias:
        id_noticia = noticia['id']
        texto_noticia = noticia['noticia_corregida']
        print(f"\n--- Analizando noticia con ID: {id_noticia} ---")
        captor, lugar, captura, explicaciones = detectar_metodo_captura(texto_noticia)

        # Guardar resultados en la base de datos
        guardar_resultados_en_extracciones(id_noticia, captor, lugar, captura)

        # Imprimir la explicación
        for exp in explicaciones:
            print(f"- {exp}")

        print(f"Captor: {captor}")
        print(f"Lugar: {lugar}")
        print(f"Captura: {captura}")

# --- EJECUCIÓN DEL PROGRAMA ---
if __name__ == "__main__":
    procesar_noticias()

