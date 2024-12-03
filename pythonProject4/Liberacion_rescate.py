import spacy
from spacy.matcher import Matcher

# Cargamos el modelo de spaCy
nlp = spacy.load('es_core_news_md')


# --- FUNCIONES MEJORADAS PARA DETECTAR SI HUBO LIBERACIÓN Y RESCATE ---

def detectar_liberacion_rescate(texto):
    doc = nlp(texto.lower())

    # Inicializamos el Matcher
    matcher = Matcher(nlp.vocab)

    # Patrones para detectar liberación con contexto
    patrones_liberacion = [
        [{"LEMMA": {"IN": ["liberar", "escapar", "huir", "fugarse"]}}, {"OP": "+"}],
        [{"TEXT": {"REGEX": "liberado|escapó|logró escapar|dejado en libertad"}}, {"OP": "+"}],
        [{"TEXT": {"REGEX": "se liberaron|se escaparon|huyeron"}}, {"OP": "+"}]
    ]

    # Patrones para detectar rescate con contexto
    patrones_rescate = [
        [{"LEMMA": {"IN": ["rescatar", "salvar", "liberar"]}}, {"OP": "+"}],
        [{"TEXT": {"REGEX": "rescatado|liberación tras|fue rescatado"}}, {"OP": "+"}]
    ]

    # Añadimos los patrones al matcher
    matcher.add("Liberacion", patrones_liberacion)
    matcher.add("Rescate", patrones_rescate)

    explicacion = []  # Para almacenar las explicaciones
    hubo_liberacion = False  # Variable para determinar si hubo liberación
    hubo_rescate = False  # Variable para determinar si hubo rescate
    fragmentos_liberacion = []  # Fragmentos de texto relevantes para la liberación
    fragmentos_rescate = []  # Fragmentos de texto relevantes para el rescate

    # Para controlar duplicados
    liberacion_detectada = False
    rescate_detectado = False

    # Buscar coincidencias de liberación y rescate
    matches = matcher(doc)
    for match_id, start, end in matches:
        span = doc[start:end]
        span_texto = span.text
        oracion_completa = span.sent.text  # Extraer la oración completa para más contexto

        # Verificamos si es liberación
        if nlp.vocab.strings[match_id] == "Liberacion" and not liberacion_detectada:
            hubo_liberacion = True
            fragmentos_liberacion.append(oracion_completa)
            explicacion.append(
                f"Liberación detectada en el fragmento: '{span_texto}'. Contexto completo: '{oracion_completa}'")
            liberacion_detectada = True  # Evitar duplicados

        # Verificamos si es rescate
        if nlp.vocab.strings[match_id] == "Rescate" and not rescate_detectado:
            hubo_rescate = True
            fragmentos_rescate.append(oracion_completa)
            explicacion.append(
                f"Rescate detectado en el fragmento: '{span_texto}'. Contexto completo: '{oracion_completa}'")
            rescate_detectado = True  # Evitar duplicados

    # Si no se detectó liberación, agregar una explicación
    if not hubo_liberacion:
        explicacion.append("No se detectó liberación en el texto.")

    # Si no se detectó rescate, agregar una explicación
    if not hubo_rescate:
        explicacion.append("No se detectó rescate en el texto.")

    return hubo_liberacion, hubo_rescate, explicacion, fragmentos_liberacion, fragmentos_rescate


# --- FUNCIÓN PRINCIPAL DE ANÁLISIS DE NOTICIA ---

def analizar_noticia_liberacion_rescate(texto):
    # Ejecutar la función de detección de liberación, rescate y circunstancias
    hubo_liberacion, hubo_rescate, explicacion_rescate, fragmentos_liberacion, fragmentos_rescate = detectar_liberacion_rescate(
        texto)

    # Imprimir la explicación de la detección de liberación y rescate
    print("Explicación sobre la liberación y el rescate:")
    for exp in explicacion_rescate:
        print(f"- {exp}")

    # Mostrar si hubo liberación y rescate
    if hubo_liberacion:
        print(f"¿Hubo liberación?: Sí")
    elif fragmentos_liberacion:
        print(f"¿Hubo liberación?: No se puede determinar, no hay información suficiente.")
    else:
        print(f"¿Hubo liberación?: No")

    if hubo_rescate:
        print(f"¿Hubo rescate?: Sí")
    elif fragmentos_rescate:
        print(f"¿Hubo rescate?: No se puede determinar, no hay información suficiente.")
    else:
        print(f"¿Hubo rescate?: No")

    # Mostrar los fragmentos donde se detectó liberación y rescate
    print("Fragmentos donde se detectó liberación:")
    for frag in fragmentos_liberacion:
        print(f"- {frag}")
    if hubo_rescate:
        print("Fragmentos donde se detectó rescate:")
        for frag in fragmentos_rescate:
            print(f"- {frag}")

    return hubo_liberacion, hubo_rescate


# --- EJECUCIÓN DEL PROGRAMA ---

# Ejemplo de noticia
texto_noticia_1 = """
Después de una larga negociación con los secuestradores, las víctimas fueron liberadas sin intervención de las autoridades. Los captores habían exigido una suma considerable de dinero, pero las víctimas lograron escapar antes de que se realizara cualquier pago.
"""

texto_noticia_2 = """
Las víctimas fueron rescatadas tras un operativo policial en el que participaron fuerzas especiales. No se pagó ningún rescate, y los secuestradores fueron arrestados en el lugar.
"""

texto_noticia_3 = """
No se reportó ningún rescate en el caso, ya que las víctimas lograron escapar por sus propios medios mientras los secuestradores dormían.
"""

# Analizamos cada noticia
print("\n--- Noticia 1 ---")
resultado_1 = analizar_noticia_liberacion_rescate(texto_noticia_1)

print("\n--- Noticia 2 ---")
resultado_2 = analizar_noticia_liberacion_rescate(texto_noticia_2)

print("\n--- Noticia 3 ---")
resultado_3 = analizar_noticia_liberacion_rescate(texto_noticia_3)


