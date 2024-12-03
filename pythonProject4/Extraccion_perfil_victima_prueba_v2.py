import pymysql
import spacy
import re
import unicodedata

# Cargamos el modelo de spaCy
nlp = spacy.load('es_core_news_lg')

# --- FUNCIÓN PARA NORMALIZAR TEXTO ---
def normalizar_texto(texto):
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    return texto.lower()

# --- FUNCIÓN PARA EXTRAER EL PERFIL DE LA VÍCTIMA ---

def extraer_perfil_victima(texto):
    doc = nlp(texto)
    perfiles_detectados = []
    victimas_unicas = set()

    # Patrones contextuales y verbos de secuestro
    verbos_secuestro = ["secuestro", "secuestrar", "raptar", "privar", "plagiar", "desaparecer", "sustraer"]

    for sent in doc.sents:
        for token in sent:
            if normalizar_texto(token.lemma_) in verbos_secuestro and token.pos_ == "VERB":
                # Detectar objetos directos, sujetos y complementos que son víctimas
                victimas = []
                if token.dep_ in ("ROOT", "conj"):
                    for child in token.children:
                        if child.dep_ in ("obj", "dobj", "obl", "nsubj:pass", "iobj", "nsubj_pass", "nsubjpass"):
                            victimas.extend(obtener_victimas_desde_token(child))
                for victima in victimas:
                    identidad_victima = f"{victima.text}_{victima.i}"
                    if identidad_victima not in victimas_unicas:
                        victimas_unicas.add(identidad_victima)
                        perfil = analizar_victima(victima, sent)
                        if perfil:
                            perfiles_detectados.append(perfil)

    # Marcar si hay múltiples víctimas
    multiples_victimas = 'Sí' if len(perfiles_detectados) > 1 else 'No'

    # Consolidar los perfiles en un único resultado
    perfil_consolidado = consolidar_perfiles(perfiles_detectados)
    perfil_consolidado['multiples_victimas'] = multiples_victimas

    return perfil_consolidado

def obtener_victimas_desde_token(token):
    victimas = []
    if token.pos_ in ("NOUN", "PROPN"):
        victimas.append(token)
    for child in token.children:
        victimas.extend(obtener_victimas_desde_token(child))
    return victimas

# --- FUNCIÓN PARA ANALIZAR LA VÍCTIMA ---

def analizar_victima(victima_token, sent):
    perfil = {}

    # --- Menor de edad ---
    es_menor, _ = determinar_menor_de_edad(victima_token, sent)
    if es_menor is not None:
        perfil['menor_de_edad'] = 'Sí' if es_menor else 'No'

    # --- Edad ---
    edad, _ = extraer_edad(victima_token, sent)
    if edad:
        perfil['edad'] = edad
        if int(edad) < 18:
            perfil['menor_de_edad'] = 'Sí'

    # --- Género ---
    genero, _ = determinar_genero(victima_token, sent)
    if genero:
        perfil['genero_victima'] = genero

    # --- Ocupación ---
    ocupacion, _ = extraer_ocupacion(victima_token, sent)
    if ocupacion:
        perfil['ocupacion_victima'] = ocupacion

    # --- Nacionalidad ---
    nacionalidad, _ = extraer_nacionalidad(victima_token, sent)
    if nacionalidad:
        perfil['nacionalidad_victima'] = nacionalidad

    return perfil if perfil else None

def consolidar_perfiles(perfiles):
    perfil_final = {}
    for perfil in perfiles:
        for clave, valor in perfil.items():
            if clave not in perfil_final or not perfil_final[clave]:
                perfil_final[clave] = valor
    return perfil_final

# --- FUNCIÓN PARA DETERMINAR SI ES MENOR DE EDAD ---

def determinar_menor_de_edad(token_victima, sent):
    palabras_menor = ['niño', 'niña', 'menor', 'adolescente', 'infante', 'bebé', 'chico', 'chica', 'nieto', 'hijo', 'hija', 'menores']
    texto = sent.text.lower()
    for palabra in palabras_menor:
        if palabra in texto:
            return True, f"Palabra clave encontrada: '{palabra}' en texto: '{sent.text.strip()}'"
    return None, None

# --- FUNCIÓN PARA EXTRAER LA EDAD ---

def extraer_edad(token_victima, sent):
    texto = sent.text
    patrones_edad = [
        rf"{re.escape(token_victima.text)} de (\d{{1,3}}) años\b",
        rf"{re.escape(token_victima.text)} de (\d{{1,3}}) años de edad\b",
        r"\b(\d{1,2}) años\b",
        r"(\d{1,3}) años de edad"
    ]
    for patron in patrones_edad:
        coincidencias = re.findall(patron, texto, re.IGNORECASE)
        if coincidencias:
            return coincidencias[0], f"Patrón encontrado: '{patron}' en texto: '{texto.strip()}'"
    return None, None

# --- FUNCIÓN PARA DETERMINAR EL GÉNERO ---

def determinar_genero(token_victima, sent):
    palabras_masculinas = ['hombre', 'varón', 'niño', 'adolescente', 'joven', 'profesor', 'doctor', 'ingeniero', 'activista', 'alcalde', 'maestro']
    palabras_femeninas = ['mujer', 'fémina', 'niña', 'adolescente', 'joven', 'profesora', 'doctora', 'ingeniera', 'activista', 'alcaldesa', 'maestra']
    texto = sent.text.lower()

    for palabra in palabras_masculinas:
        if palabra in texto:
            return 'Masculino', f"Palabra clave encontrada: '{palabra}' en texto: '{sent.text.strip()}'"
    for palabra in palabras_femeninas:
        if palabra in texto:
            return 'Femenino', f"Palabra clave encontrada: '{palabra}' en texto: '{sent.text.strip()}'"
    return None, None

# --- FUNCIÓN PARA EXTRAER LA OCUPACIÓN ---

def extraer_ocupacion(token_victima, sent):
    ocupaciones = [
        'alcalde', 'diputado', 'senador', 'gobernador', 'presidente', 'médico', 'doctor', 'enfermero', 'abogado', 'ingeniero',
        'estudiante', 'empresario', 'comerciante', 'profesor', 'periodista', 'policía', 'militar', 'taxista', 'chofer', 'trabajador', 'activista'
    ]
    texto = sent.text.lower()
    for ocupacion in ocupaciones:
        if re.search(rf"\b{ocupacion}\b", texto):
            return ocupacion.capitalize(), f"Ocupación encontrada: '{ocupacion}' en texto: '{sent.text.strip()}'"
    return None, None

# --- FUNCIÓN PARA EXTRAER LA NACIONALIDAD ---

def extraer_nacionalidad(token_victima, sent):
    nacionalidades = ['mexicano', 'mexicana', 'estadounidense', 'canadiense', 'español', 'colombiano', 'argentino', 'venezolano', 'peruano', 'chileno']
    texto = sent.text.lower()
    for nacionalidad in nacionalidades:
        if re.search(rf"\b{nacionalidad}\b", texto):
            return nacionalidad.capitalize(), f"Nacionalidad encontrada: '{nacionalidad}' en texto: '{sent.text.strip()}'"
    return None, None

# --- CONEXIÓN A LA BASE DE DATOS ---

def conectar_bd():
    conexion = pymysql.connect(
        host='localhost',
        user='root',
        password='Soccer.8a',  # Actualiza con tu contraseña
        database='noticias',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    return conexion

# --- FUNCIÓN PARA VERIFICAR Y AGREGAR CAMPOS DE PERFIL EN LA TABLA ---

def verificar_y_agregar_campos_perfil():
    conexion = conectar_bd()
    try:
        with conexion.cursor() as cursor:
            # Verificar y agregar campos si no existen
            campos = ['edad_victima', 'menor_de_edad', 'genero_victima', 'ocupacion_victima', 'nacionalidad_victima', 'multiples_victimas']
            for campo in campos:
                cursor.execute(f"SHOW COLUMNS FROM extracciones LIKE '{campo}'")
                if not cursor.fetchone():
                    cursor.execute(f"ALTER TABLE extracciones ADD COLUMN {campo} VARCHAR(255)")
                    print(f"Campo '{campo}' agregado.")
            conexion.commit()
    finally:
        conexion.close()

# --- FUNCIÓN PARA ACTUALIZAR EL PERFIL DE LA VÍCTIMA EN LA TABLA ---

def actualizar_perfil_noticia(id_noticia, perfil):
    conexion = conectar_bd()
    try:
        with conexion.cursor() as cursor:
            sql = """
            UPDATE extracciones SET edad_victima = %s, menor_de_edad = %s, genero_victima = %s, 
            ocupacion_victima = %s, nacionalidad_victima = %s, multiples_victimas = %s WHERE id = %s
            """
            cursor.execute(sql, (
                perfil.get('edad', ''),
                perfil.get('menor_de_edad', ''),
                perfil.get('genero_victima', ''),
                perfil.get('ocupacion_victima', ''),
                perfil.get('nacionalidad_victima', ''),
                perfil.get('multiples_victimas', 'No'),
                id_noticia
            ))
            conexion.commit()
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

# --- PROCESAR Y ANALIZAR NOTICIAS ---

def procesar_noticias():
    # Verificar y agregar los campos de perfil si no existen
    verificar_y_agregar_campos_perfil()

    # Obtener y procesar noticias
    noticias = obtener_noticias()
    for noticia in noticias:
        id_noticia = noticia['id']
        texto_noticia = noticia['noticia_corregida']

        # Analizar el perfil de la víctima
        perfil_victima = extraer_perfil_victima(texto_noticia)

        # Mostrar resultados del análisis
        print(f"\n--- Analizando noticia con ID: {id_noticia} ---")
        if perfil_victima:
            print("Perfil de la víctima:")
            for clave, valor in perfil_victima.items():
                print(f"- {clave.capitalize().replace('_', ' ')}: {valor}")
        else:
            print("No se encontró información sobre el perfil de la víctima.")

        # Actualizar la base de datos con el perfil de la víctima
        actualizar_perfil_noticia(id_noticia, perfil_victima)

# --- EJECUCIÓN DEL PROGRAMA ---
if __name__ == "__main__":
    procesar_noticias()
