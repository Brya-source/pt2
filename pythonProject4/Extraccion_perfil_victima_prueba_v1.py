import pymysql
import spacy
import re

# Cargamos el modelo de spaCy
nlp = spacy.load('es_core_news_lg')

# --- FUNCIÓN PARA EXTRAER LOS PERFILES DE LAS VÍCTIMAS ---

def extraer_perfiles_victimas(texto):
    doc = nlp(texto)

    perfiles_detectados = []
    victimas_unicas = set()

    # Lista de verbos relacionados con el secuestro
    verbos_secuestro = ["secuestro", "secuestrar", "raptar", "privar", "plagiar", "desaparecer", "sustraer", "plagiaron", "plagiado", "plagio"]

    for sent in doc.sents:
        for token in sent:
            if token.lemma_ in verbos_secuestro and token.pos_ == "VERB":
                # Buscamos objetos directos y sujetos pasivos
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

    # Determinamos si hay más de una víctima
    multiple_victimas = len(perfiles_detectados) > 1

    return perfiles_detectados, multiple_victimas

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

    # Identificador único de la víctima
    perfil['identificador_unico'] = f"{victima_token.text}_{victima_token.i}"

    # --- Determinar si es menor de edad ---
    es_menor, justificacion_menor = determinar_menor_de_edad(victima_token)
    if es_menor is not None:
        perfil['menor_de_edad'] = 'Sí' if es_menor else 'No'
        perfil['justificacion_menor_de_edad'] = justificacion_menor

    # --- Extracción de la edad ---
    edad, justificacion_edad = extraer_edad(victima_token, sent)
    if edad:
        perfil['edad'] = edad
        perfil['justificacion_edad'] = justificacion_edad
        if int(edad) < 18:
            perfil['menor_de_edad'] = 'Sí'
            perfil['justificacion_menor_de_edad'] = f"Edad extraída: {edad}"

    # --- Determinar el género ---
    genero, justificacion_genero = determinar_genero(victima_token)
    if genero:
        perfil['genero'] = genero
        perfil['justificacion_genero'] = justificacion_genero

    # --- Extracción de la ocupación ---
    ocupacion, justificacion_ocupacion = extraer_ocupacion(victima_token, sent)
    if ocupacion:
        perfil['ocupacion'] = ocupacion
        perfil['justificacion_ocupacion'] = justificacion_ocupacion

    # --- Extracción de la nacionalidad ---
    nacionalidad, justificacion_nacionalidad = extraer_nacionalidad(victima_token, sent)
    if nacionalidad:
        perfil['nacionalidad'] = nacionalidad
        perfil['justificacion_nacionalidad'] = justificacion_nacionalidad

    if any(key in perfil for key in ['edad', 'menor_de_edad', 'genero', 'ocupacion', 'nacionalidad']):
        return perfil
    else:
        return None

# --- FUNCIÓN PARA DETERMINAR SI ES MENOR DE EDAD ---

def determinar_menor_de_edad(token_victima):
    palabras_menor = ['niño', 'niña', 'menor', 'adolescente', 'infante', 'bebé', 'chico', 'chica', 'nieto', 'hijo', 'hija']
    if token_victima.lemma_ in palabras_menor:
        return True, f"Palabra clave encontrada: '{token_victima.text}'"
    return None, None

# --- FUNCIÓN PARA EXTRAER LA EDAD ---

def extraer_edad(token_victima, sent):
    texto = sent.text
    patrones_edad = [
        rf"{re.escape(token_victima.text)} de (\d{{1,3}}) años\b",
        rf"{re.escape(token_victima.text)} de (\d{{1,3}}) años de edad\b",
        rf"{re.escape(token_victima.text)}\s*\(?(\d{{1,3}})\)?\s*años\b",
        rf"{re.escape(token_victima.text)}\s*,\s*(\d{{1,3}})\s*años\b",
        rf"(\d{{1,3}})\s*años\s*de\s*edad\s*{re.escape(token_victima.text)}\b",
    ]
    for patron in patrones_edad:
        coincidencias = re.findall(patron, texto, re.IGNORECASE)
        if coincidencias:
            return coincidencias[0], f"Patrón encontrado: '{patron}' en texto: '{texto.strip()}'"
    return None, None

# --- FUNCIÓN PARA DETERMINAR EL GÉNERO ---

def determinar_genero(token_victima):
    palabras_masculinas = ['hombre', 'varón', 'niño', 'adolescente', 'joven', 'estudiante',
                           'profesor', 'doctor', 'ingeniero', 'secuestrado', 'activista', 'alcalde', 'maestro', 'nieto', 'hijo']
    palabras_femeninas = ['mujer', 'fémina', 'niña', 'adolescente', 'joven', 'estudiante',
                          'profesora', 'doctora', 'ingeniera', 'secuestrada', 'hija', 'madre', 'activista', 'nieta']

    if token_victima.lemma_ in palabras_masculinas:
        return 'Masculino', f"Palabra clave encontrada: '{token_victima.text}'"
    elif token_victima.lemma_ in palabras_femeninas:
        return 'Femenino', f"Palabra clave encontrada: '{token_victima.text}'"
    elif token_victima.morph.get("Gender"):
        genero = token_victima.morph.get("Gender")[0]
        genero_texto = 'Masculino' if genero == 'Masc' else 'Femenino' if genero == 'Fem' else None
        if genero_texto:
            return genero_texto, f"Género determinado por morfología: '{genero_texto}'"
    return None, None

# --- FUNCIÓN PARA EXTRAER LA OCUPACIÓN ---

def extraer_ocupacion(token_victima, sent):
    ocupaciones = ['estudiante', 'empresario', 'comerciante', 'profesor', 'ingeniero',
                   'doctor', 'abogado', 'agricultor', 'periodista', 'policía', 'militar',
                   'artista', 'deportista', 'taxista', 'chofer', 'médico', 'enfermero',
                   'arquitecto', 'piloto', 'trabajador', 'empleado', 'desempleado', 'campesino',
                   'ingeniera', 'doctora', 'profesora', 'enfermera', 'activista', 'alcalde', 'maestro', 'restaurantero']

    # Buscamos ocupaciones en tokens adyacentes o en aposición
    for token in sent:
        if token.text.lower() in ocupaciones and (token.head == token_victima or token_victima.head == token):
            return token.text.capitalize(), f"Ocupación encontrada: '{token.text}' en texto: '{sent.text.strip()}'"
    return None, None

# --- FUNCIÓN PARA EXTRAER LA NACIONALIDAD ---

def extraer_nacionalidad(token_victima, sent):
    nacionalidades = ['mexicano', 'mexicana', 'estadounidense', 'canadiense', 'español',
                      'española', 'colombiano', 'colombiana', 'argentino', 'argentina',
                      'venezolano', 'venezolana', 'peruano', 'peruana', 'chileno', 'chilena',
                      'brasileño', 'brasileña', 'uruguayo', 'uruguaya', 'paraguayo', 'paraguaya',
                      'hondureño', 'hondureña', 'guatemalteco', 'guatemalteca', 'salvadoreño', 'salvadoreña']

    for token in sent:
        if token.text.lower() in nacionalidades and (token.head == token_victima or token_victima.head == token):
            return token.text.capitalize(), f"Nacionalidad encontrada: '{token.text}' en texto: '{sent.text.strip()}'"
    return None, None

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

# --- FUNCIÓN PARA VERIFICAR Y AGREGAR TABLA DE VÍCTIMAS ---

def crear_tabla_victimas():
    conexion = conectar_bd()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS victimas (
                id INT AUTO_INCREMENT PRIMARY KEY,
                id_noticia INT,
                edad_victima VARCHAR(255),
                menor_de_edad VARCHAR(10),
                genero_victima VARCHAR(50),
                ocupacion_victima VARCHAR(255),
                nacionalidad_victima VARCHAR(255),
                FOREIGN KEY (id_noticia) REFERENCES extracciones(id)
            )
            """)
            conexion.commit()
    finally:
        conexion.close()

# --- FUNCIÓN PARA ACTUALIZAR LA TABLA DE VÍCTIMAS ---

def actualizar_tabla_victimas(id_noticia, perfiles):
    conexion = conectar_bd()
    try:
        with conexion.cursor() as cursor:
            # Eliminamos registros anteriores de víctimas para esta noticia
            cursor.execute("DELETE FROM victimas WHERE id_noticia = %s", (id_noticia,))
            # Insertamos los nuevos perfiles de víctimas
            for perfil in perfiles:
                sql = """
                INSERT INTO victimas (id_noticia, edad_victima, menor_de_edad, genero_victima,
                ocupacion_victima, nacionalidad_victima)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    id_noticia,
                    perfil.get('edad', ''),
                    perfil.get('menor_de_edad', ''),
                    perfil.get('genero', ''),
                    perfil.get('ocupacion', ''),
                    perfil.get('nacionalidad', '')
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
    # Creamos la tabla de víctimas si no existe
    crear_tabla_victimas()

    # Obtener y procesar noticias
    noticias = obtener_noticias()
    for noticia in noticias:
        id_noticia = noticia['id']
        texto_noticia = noticia['noticia_corregida']

        # Analizar los perfiles de las víctimas
        perfiles_victimas, multiple_victimas = extraer_perfiles_victimas(texto_noticia)

        # Mostrar resultados del análisis
        print(f"\n--- Analizando noticia con ID: {id_noticia} ---")
        if perfiles_victimas:
            print(f"Se detectaron {len(perfiles_victimas)} víctima(s) en la noticia.")
            for idx, perfil in enumerate(perfiles_victimas, 1):
                print(f"\nPerfil de la víctima {idx}:")
                for clave, valor in perfil.items():
                    if not clave.startswith('justificacion_') and clave not in ['identificador_unico']:
                        justificacion = perfil.get(f'justificacion_{clave}', '')
                        print(f"- {clave.capitalize().replace('_', ' ')}: {valor}")
                        if justificacion:
                            print(f"  Justificación: {justificacion}")
        else:
            print("No se encontró información sobre el perfil de la víctima.")

        # Actualizar la tabla de víctimas con el resultado
        actualizar_tabla_victimas(id_noticia, perfiles_victimas)

# --- EJECUCIÓN DEL PROGRAMA ---
if __name__ == "__main__":
    procesar_noticias()
