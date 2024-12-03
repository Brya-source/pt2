import pymysql
import spacy
from spacy.matcher import Matcher

# Cargamos el modelo de spaCy
nlp = spacy.load('es_core_news_md')

# --- FUNCIONES PARA DETECTAR EL MÉTODO DE CAPTURA ---

def detectar_metodo_captura(texto):
    doc = nlp(texto.lower())

    # Inicializamos el Matcher
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
        [{"TEXT": {"REGEX": "vinculado a cartel|como represalia"}}, {"OP": "?"}]
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

    explicacion = {}  # Diccionario para almacenar explicaciones de cada método de captura
    metodos_detectados = set()  # Usar un conjunto para evitar duplicados
    intento_secuestro = False  # Variable para asignar intento de secuestro si la construcción es ambigua
    nuevo_metodo_detectado = False  # Para identificar métodos desconocidos

    # Buscar coincidencias en el texto
    matches = matcher(doc)
    if not matches:
        print("No se encontraron coincidencias en el texto.")

    for match_id, start, end in matches:
        span = doc[start:end]
        oracion_completa = span.sent.text  # Extraer la oración completa para más contexto
        metodo = nlp.vocab.strings[match_id]

        # Verificar si "familia" está en un contexto delictivo
        if metodo == "Captura_Confianza" and "familia michoacana" in oracion_completa:
            explicacion["Captura_Confianza"] = "Palabra 'familia' detectada en contexto de grupo delictivo, no clasificado como confianza."
            continue

        # Verificar si la referencia a la policía o autoridad es un reporte, no captura
        if metodo == "Captura_Autoridad" and any(palabra in oracion_completa for palabra in ["reportó", "denunció", "informó a la policía"]):
            explicacion["Captura_Autoridad"] = "Mención de policía o autoridad corresponde a un reporte, no a una captura."
            continue

        # Verificar construcción semántica de intento de secuestro
        if any(palabra in oracion_completa for palabra in ["intento", "intentó", "intentar", "no logró"]):
            intento_secuestro = True
            explicacion["Intento_Secuestro"] = f"Intento de secuestro detectado con contexto: '{oracion_completa}'"
        else:
            # Agregar el método detectado al conjunto de métodos de captura
            metodos_detectados.add(metodo)
            # Solo añadir la justificación si aún no hay una para este método (así guardamos la primera ocurrencia)
            if metodo not in explicacion:
                explicacion[metodo] = f"Método de captura detectado: '{metodo}'. Contexto completo: '{oracion_completa}'"

    # Verificar si no se encontró un método de captura conocido
    if not metodos_detectados and not intento_secuestro:
        nuevo_metodo_detectado = True
        metodos_detectados.add("Nuevo_Metodo")
        explicacion["Nuevo_Metodo"] = "Posible método de captura no identificado encontrado. Contexto detectado: '{}'".format(texto)

    # Si no se detectó ningún método de captura y hay indicios de intento
    if not metodos_detectados and intento_secuestro:
        metodos_detectados.add("Intento_Secuestro")
        explicacion["Intento_Secuestro"] = "Clasificación asignada como 'Intento de Secuestro' debido a contexto de intento detectado."

    # Convertir el conjunto a una lista y seleccionar la justificación más significativa (primera ocurrencia)
    metodos_final = list(metodos_detectados)
    explicaciones_final = [explicacion[metodo] for metodo in metodos_final]

    return metodos_final, explicaciones_final

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

# --- FUNCIÓN PARA OBTENER LAS NOTICIAS CON 'Sí' EN RELACION_SPACY4 ---

def obtener_noticias():
    conexion = conectar_bd()
    try:
        with conexion.cursor() as cursor:
            sql = "SELECT id, noticia_corregida FROM extracciones WHERE relacion_spacy4 = 'Sí' LIMIT 50"
            cursor.execute(sql)
            resultados = cursor.fetchall()
            return resultados
    finally:
        conexion.close()

# --- PROCESAR Y ANALIZAR NOTICIAS ---

def procesar_noticias():
    noticias = obtener_noticias()
    for noticia in noticias:
        id_noticia = noticia['id']
        texto_noticia = noticia['noticia_corregida']
        print(f"\n--- Analizando noticia con ID: {id_noticia} ---")
        metodos_captura, explicacion_captura = detectar_metodo_captura(texto_noticia)

        # Imprimir la explicación
        for exp in explicacion_captura:
            print(f"- {exp}")

        # Imprimir los métodos de captura detectados
        if metodos_captura:
            print(f"Métodos de captura detectados: {', '.join(metodos_captura)}")
        else:
            print("Método de captura: No detectado")

# --- EJECUCIÓN DEL PROGRAMA ---
if __name__ == "__main__":
    procesar_noticias()
