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

    # Patrones para identificar diferentes métodos de captura
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
        [{"TEXT": {"REGEX": "arresto|intervención de"}}, {"OP": "+"}]
    ]

    # Añadimos los patrones al matcher
    matcher.add("Captura_Engaño", [patrones_metodo_captura[0], patrones_metodo_captura[1], patrones_metodo_captura[2]])
    matcher.add("Captura_Fuerza", [patrones_metodo_captura[3], patrones_metodo_captura[4], patrones_metodo_captura[5]])
    matcher.add("Captura_Emboscada", [patrones_metodo_captura[6], patrones_metodo_captura[7], patrones_metodo_captura[8]])
    matcher.add("Captura_Intimidación", [patrones_metodo_captura[9], patrones_metodo_captura[10], patrones_metodo_captura[11]])
    matcher.add("Captura_Confianza", [patrones_metodo_captura[12], patrones_metodo_captura[13], patrones_metodo_captura[14], patrones_metodo_captura[15]])
    matcher.add("Detencion_Autoridad", [patrones_metodo_captura[16], patrones_metodo_captura[17], patrones_metodo_captura[18], patrones_metodo_captura[19]])

    explicacion = []  # Para almacenar las explicaciones
    metodo_detectado = None  # Variable para determinar el método de captura
    fragmentos_captura = []  # Fragmentos de texto relevantes para la captura

    # Buscar coincidencias en el texto
    matches = matcher(doc)
    for match_id, start, end in matches:
        span = doc[start:end]
        oracion_completa = span.sent.text  # Extraer la oración completa para más contexto
        metodo = nlp.vocab.strings[match_id]

        # Verificar si "familia" está en un contexto delictivo
        if metodo == "Captura_Confianza" and "familia michoacana" in oracion_completa:
            explicacion.append("Palabra 'familia' detectada en contexto de grupo delictivo, no clasificado como confianza.")
            continue

        if metodo_detectado is None:  # Solo asignar el primer método detectado
            metodo_detectado = metodo
            fragmentos_captura.append(oracion_completa)
            explicacion.append(
                f"Método de captura detectado: '{metodo}'. Contexto completo: '{oracion_completa}'")

    # Si no se detectó un método de captura, agregar una explicación
    if metodo_detectado is None:
        explicacion.append("No se detectó un método de captura claro en el texto.")

    return metodo_detectado, explicacion

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
            sql = "SELECT id, noticia_corregida FROM extracciones WHERE relacion_spacy4 = 'Sí' LIMIT 10"
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
        metodo_captura, explicacion_captura = detectar_metodo_captura(texto_noticia)

        # Imprimir la explicación
        for exp in explicacion_captura:
            print(f"- {exp}")

        # Imprimir el método de captura detectado
        if metodo_captura:
            print(f"Método de captura detectado: {metodo_captura}")
        else:
            print("Método de captura: No detectado")

# --- EJECUCIÓN DEL PROGRAMA ---
if __name__ == "__main__":
    procesar_noticias()

