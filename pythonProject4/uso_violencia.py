import spacy

# Cargamos el modelo de spaCy
nlp = spacy.load('es_core_news_md')


# --- FUNCIONES PARA DETECTAR TIPO DE VIOLENCIA ---

# Función para detectar violencia y determinar el tipo de violencia
def detectar_tipo_violencia(texto):
    doc = nlp(texto.lower())

    # Definir los tipos de violencia y sus palabras clave
    tipos_de_violencia = {
        "armas de fuego": ["pistola", "rifle", "revolver", "escopeta", "bala", "fusil", "arma de fuego"],
        "objetos punzocortantes": ["navaja", "cuchillo", "punzocortantes", "cortar", "herida", "filo"],
        "violencia física": ["golpear", "golpeado", "puñetazo", "puño", "patada", "golpe"]
    }

    # Lista de palabras de negación
    palabras_negacion = ["no", "nunca", "jamás", "sin", "ninguna", "ningún"]

    explicacion = []  # Para almacenar las explicaciones de por qué se detectó o no violencia
    fragmentos_violencia = []  # Para almacenar fragmentos de texto relevantes
    tipos_detectados = []  # Para almacenar los tipos de violencia detectados
    hubo_violencia = False  # Variable para determinar si hubo violencia

    # Recorremos el texto en busca de palabras clave para cada tipo de violencia
    for sent in doc.sents:
        for token in sent:
            for tipo, palabras_clave in tipos_de_violencia.items():
                if token.text in palabras_clave:
                    negacion_encontrada = False
                    # Revisar si hay una negación cercana
                    for i in range(1, 4):
                        if token.i - i >= 0 and doc[token.i - i].text in palabras_negacion:
                            negacion_encontrada = True
                            explicacion.append(f"Negación detectada: '{doc[token.i - i].text}' antes de '{token.text}'")
                            break

                    # Si no hay negación, se detecta violencia y se identifica el tipo
                    if not negacion_encontrada:
                        violencia_contexto = " ".join([tok.text for tok in token.sent])  # Extraer la oración completa
                        fragmentos_violencia.append(violencia_contexto)
                        tipos_detectados.append(tipo)
                        hubo_violencia = True
                        explicacion.append(
                            f"Tipo de violencia detectado: '{tipo}' en el fragmento '{violencia_contexto}'")

    # Si no se detectó violencia, se agrega una explicación
    if not hubo_violencia:
        explicacion.append("No se detectó violencia en el texto.")

    return hubo_violencia, tipos_detectados, explicacion, fragmentos_violencia


# --- FUNCIÓN PRINCIPAL DE ANÁLISIS DE NOTICIA ---

def analizar_noticia(texto):
    # Crear un diccionario para almacenar los resultados de las funciones
    resultados = {}

    # Ejecutar la función de detección de tipo de violencia
    resultados["violencia"], tipos_detectados, explicacion_violencia, fragmentos_violencia = detectar_tipo_violencia(
        texto)

    # Imprimir la explicación de la detección de violencia
    print("Explicación sobre violencia:")
    for exp in explicacion_violencia:
        print(f"- {exp}")

    print("Tipos de violencia detectados:")
    for tipo in tipos_detectados:
        print(f"- {tipo}")

    print("Fragmentos donde se detectó violencia:")
    for frag in fragmentos_violencia:
        print(f"- {frag}")

    # Retornar los resultados
    return resultados


# --- EJECUCIÓN DEL PROGRAMA ---

# Ejemplo de noticia
texto_noticia_1 = """
El secuestro se llevó a cabo en las primeras horas del día cuando un grupo de hombres armados interceptó un camión de transporte de carga en una autopista cercana a la ciudad. Aunque los delincuentes portaban armas visibles, no las utilizaron en ningún momento contra el conductor, quien fue obligado a detener el vehículo bajo amenaza verbal. El conductor fue amarrado y dejado en el interior del camión, pero no fue golpeado, según informes de la policía.

Horas más tarde, el secuestrado fue liberado en las afueras de la ciudad sin mayor incidente, y se reporta que no hubo ningún pago de rescate. Las autoridades continúan buscando a los responsables, quienes aparentemente solo querían intimidar sin recurrir a la violencia física. No se registraron heridos ni fallecidos en el incidente.
"""

texto_noticia_2 = """
La situación comenzó como un secuestro virtual, en el cual los delincuentes llamaron por teléfono a las víctimas, haciéndolas creer que un familiar había sido raptado. A través de amenazas, lograron que la familia realizara una transferencia bancaria de una importante suma de dinero. A pesar del estrés causado, no hubo ningún contacto físico ni uso de armas en este incidente, ya que las víctimas nunca estuvieron en peligro real.

Al descubrir que habían sido engañados, las víctimas acudieron a las autoridades, quienes determinaron que todo fue un montaje. No hubo liberación física ni violencia directa involucrada, pero las secuelas psicológicas fueron graves.
"""

texto_noticia_3 = """
Un grupo de migrantes fue secuestrado mientras cruzaba una zona controlada por grupos criminales. Según los informes, los migrantes fueron mantenidos cautivos durante varios días sin acceso a comida ni agua. Aunque no se reportó el uso de violencia física severa, algunos de los secuestrados mostraban signos de deshidratación y agotamiento extremo.

Los captores exigieron un rescate, pero las autoridades no han confirmado si se pagó. Los migrantes fueron liberados posteriormente tras la intervención de un grupo de rescate especializado. No se reportaron fallecidos, aunque las condiciones deplorables en las que fueron mantenidos los migrantes han generado preocupación.
"""

# Analizamos cada noticia
print("\n--- Noticia 1 ---")
resultado_1 = analizar_noticia(texto_noticia_1)

print("\n--- Noticia 2 ---")
resultado_2 = analizar_noticia(texto_noticia_2)

print("\n--- Noticia 3 ---")
resultado_3 = analizar_noticia(texto_noticia_3)

texto_noticia_larga = """
El secuestro ocurrió en una carretera desolada al norte de la ciudad. Los delincuentes, que portaban armas de alto calibre, bloquearon el paso del vehículo de las víctimas, obligándolas a bajar a punta de pistola. Durante el acto, las víctimas fueron golpeadas y amenazadas con ser asesinadas si no cooperaban.

Sin embargo, a pesar de portar armas, los secuestradores nunca realizaron disparos y, según fuentes policiales, no hubo uso de fuerza letal. No obstante, el abuso físico fue evidente, con signos de violencia en los rostros y cuerpos de las víctimas.
"""

# Detectamos si hubo uso de violencia y el tipo en el texto
hubo_violencia, tipos_detectados, explicacion_violencia, fragmentos_violencia = detectar_tipo_violencia(
    texto_noticia_larga)

# Mostrar resultados
print("\n--- Noticia Larga ---")
print("¿Hubo uso de violencia?:", hubo_violencia)
print("Tipos de violencia detectados:")
for tipo in tipos_detectados:
    print(f"- {tipo}")

print("Explicaciones:")
for exp in explicacion_violencia:
    print(f"- {exp}")

print("Fragmentos donde se detectó violencia:")
for frag in fragmentos_violencia:
    print(f"- {frag}")
