import pymysql
import re
import spacy
import time
import requests
from transformers import pipeline
from spacy.matcher import Matcher
import dateparser
from datetime import datetime
import unicodedata


nlp = spacy.load('es_core_news_lg')


ner_model = pipeline("ner", model="dccuchile/bert-base-spanish-wwm-cased", aggregation_strategy="simple")


localidades = {
    "Cuautitlán Izcalli": {"estado": "Estado de México", "pais": "México"},
    "Ecatepec": {"estado": "Estado de México", "pais": "México"},
    "Tlalnepantla": {"estado": "Estado de México", "pais": "México"},
    "Nezahualcóyotl": {"estado": "Estado de México", "pais": "México"},
    "Ciudad de México": {"estado": "Ciudad de México", "pais": "México"},
    "Monterrey": {"estado": "Nuevo León", "pais": "México"},
    "Guadalajara": {"estado": "Jalisco", "pais": "México"},
    "Tijuana": {"estado": "Baja California", "pais": "México"},
    "Cancún": {"estado": "Quintana Roo", "pais": "México"}
}


usuario_geonames = "bryanhernandez"


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


def normalizar_texto(texto):
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    return texto.lower()

# --- FUNCIÓN PARA LIMPIAR LAS NOTICIAS Y CREAR 'noticia_corregida' ---
def limpiar_noticias():
    conexion = conectar_bd()
    try:
        with conexion.cursor() as cursor:
            # Verificar si la columna 'noticia_corregida' ya existe
            cursor.execute("SHOW COLUMNS FROM extracciones LIKE 'noticia_corregida';")
            resultado = cursor.fetchone()

            # Si la columna no existe, la creamos
            if not resultado:
                cursor.execute("ALTER TABLE extracciones ADD COLUMN noticia_corregida TEXT;")

            # Selecciona los id y las noticias originales
            consulta_seleccion = "SELECT id, noticia FROM extracciones"
            cursor.execute(consulta_seleccion)
            resultados = cursor.fetchall()

            # Expresiones regulares para limpiar el texto
            exreg_lee_tambien = re.compile(
                r'([Ll]ee también|[Ll]eer también|[Ll]ea también|[Ll]ee más|[Tt]ambién lee|[Tt]ambien lee).*?(\n|$)',
                re.IGNORECASE)

            exreg_foto = re.compile(
                r'Foto:.*?(\n|$)', re.IGNORECASE)

            exreg_dispositivo = re.compile(
                r',\s*desde tu dispositivo móvil entérate de las noticias más relevantes del día, artículos de opinión, entretenimiento, tendencias y más\..*?(\n|$)',
                re.IGNORECASE)

            exreg_ultima_parte = re.compile(
                r'(\*?\s*El Grupo de Diarios América \(GDA\), al cual pertenece EL UNIVERSAL.*|'
                r'Ahora puedes recibir notificaciones de BBC Mundo.*|'
                r'Recuerda que puedes recibir notificaciones de BBC Mundo.*|'
                r'Suscríbete aquí.*|'
                r'Recibe todos los viernes Hello Weekend.*|'
                r'Recuerda que puedes recibir notificaciones de BBC News Mundo.*|'
                r'Únete a nuestro canal.*|'
                r'Ahora puedes recibir notificaciones de BBC News Mundo.*|'
                r'¿Ya conoces nuestro canal de YouTube\? ¡Suscríbete!.*|'
                r'para recibir directo en tu correo nuestras newsletters sobre noticias del día, opinión, (planes para el fin de semana, )?Qatar 2022 y muchas opciones más\..*)',
                re.IGNORECASE | re.DOTALL)

            ids_modificados = []

            # Procesa cada fila
            for fila in resultados:
                id_noticia = fila['id']
                texto_noticia = fila['noticia']

                if texto_noticia is not None:
                    # Aplica las correcciones al texto
                    texto_noticia_limpio = re.sub(exreg_lee_tambien, '', texto_noticia)
                    texto_noticia_limpio = re.sub(exreg_foto, '', texto_noticia_limpio)
                    texto_noticia_limpio = re.sub(exreg_dispositivo, '', texto_noticia_limpio)
                    texto_noticia_limpio = re.sub(exreg_ultima_parte, '', texto_noticia_limpio)

                    # Si hay cambios, registrar el ID
                    if texto_noticia != texto_noticia_limpio:
                        ids_modificados.append(id_noticia)

                    # Guardar el texto corregido o original en 'noticia_corregida'
                    consulta_actualizacion = "UPDATE extracciones SET noticia_corregida = %s WHERE id = %s"
                    cursor.execute(consulta_actualizacion, (texto_noticia_limpio, id_noticia))
                else:
                    # Si 'noticia' es None, guardar una cadena vacía en 'noticia_corregida'
                    consulta_actualizacion = "UPDATE extracciones SET noticia_corregida = '' WHERE id = %s"
                    cursor.execute(consulta_actualizacion, (id_noticia,))

            conexion.commit()

    finally:
        conexion.close()

    print("Noticias procesadas con los siguientes IDs:")
    print(ids_modificados)

# --- FUNCIONES PARA DETERMINAR SI LA NOTICIA ESTÁ RELACIONADA CON SECUESTROS ---
def es_noticia_de_secuestro(texto_completo):
    # Pasar el texto completo al modelo de spaCy
    doc = nlp(texto_completo)

    # Variables para determinar si es secuestro y justificar
    es_secuestro = False
    justificacion = ""

    # Análisis semántico profundo: buscamos relaciones entre el contexto y situaciones de secuestro
    for ent in doc.ents:
        contexto = ent.sent.text

        # Evitar catalogar como secuestro si se detecta simulacro, película o contexto no relacionado
        if any(term in contexto.lower() for term in ['simulacro', 'película', 'serie', 'ficticio', 'ficción']):
            es_secuestro = False
            justificacion = f"Contexto detectado relacionado con simulacros, películas o ficción: '{contexto}'"
            break

        # Análisis de entidades y contexto real de secuestro
        if ent.label_ in ['PER', 'ORG', 'MISC']:
            # Verificar contexto que implique secuestro real o privación de libertad
            if any(verb in contexto.lower() for verb in ['retenido', 'privado', 'capturado', 'detenido', 'secuestrado']):
                es_secuestro = True
                justificacion = f"Se encontró contexto de posible secuestro o privación de libertad en: '{contexto}'"
                break

        # Analizar relaciones entre víctimas y acciones asociadas con secuestro
        if "víctima" in ent.text.lower() and any(action in contexto.lower() for action in ['retenida', 'privada de libertad']):
            es_secuestro = True
            justificacion = f"Contexto de víctima privada de libertad en: '{ent.sent.text}'"
            break

    return es_secuestro, justificacion

# --- FUNCIÓN PARA OBTENER LAS NOTICIAS A ANALIZAR ---
def obtener_noticias():
    conexion = conectar_bd()
    try:
        with conexion.cursor() as cursor:
            # Seleccionar id, noticia_corregida, excluyendo ciertos términos en los campos título y descripción
            sql = """
            SELECT id, noticia_corregida, fecha
            FROM extracciones
            WHERE (titulo NOT LIKE '%El Mayo Zambada%' 
            AND descripcion NOT LIKE '%El Mayo Zambada%' 
            AND titulo NOT LIKE '%El Mayo%' 
            AND descripcion NOT LIKE '%El Mayo%' 
            AND titulo NOT LIKE '%Israel%' 
            AND descripcion NOT LIKE '%Israel%' 
            AND titulo NOT LIKE '%Gaza%' 
            AND descripcion NOT LIKE '%Gaza%' 
            AND titulo NOT LIKE '%Hamas%' 
            AND descripcion NOT LIKE '%Hamas%' 
            AND titulo NOT LIKE '%Netanyahu%' 
            AND descripcion NOT LIKE '%Netanyahu%'
            AND titulo NOT LIKE '%Chapo Guzmán%' 
            AND descripcion NOT LIKE '%Chapo Guzmán%' 
            AND titulo NOT LIKE '%Ovidio Guzmán%' 
            AND descripcion NOT LIKE '%Ovidio Guzmán%');
            """
            cursor.execute(sql)
            resultados = cursor.fetchall()
            return resultados
    finally:
        conexion.close()

# --- PROCESAR Y CLASIFICAR NOTICIAS ---
def procesar_noticias_relacion():
    noticias = obtener_noticias()
    conexion = conectar_bd()
    try:
        with conexion.cursor() as cursor:
            # Verificar si la columna 'relacion_spacy4' ya existe, si no, crearla
            cursor.execute("SHOW COLUMNS FROM extracciones LIKE 'relacion_spacy4';")
            resultado = cursor.fetchone()

            if not resultado:
                cursor.execute("ALTER TABLE extracciones ADD COLUMN relacion_spacy4 VARCHAR(3);")

            # Procesar cada noticia y analizar si está relacionada con secuestros usando solo el campo noticia_corregida
            for noticia in noticias:
                id_noticia = noticia['id']
                texto_completo = noticia['noticia_corregida'] or ""

                # Verificar que el texto no esté vacío
                if texto_completo.strip():
                    # Realizar el análisis semántico en el campo noticia_corregida
                    relacionada_con_secuestro, justificacion = es_noticia_de_secuestro(texto_completo)

                    # Actualizar el campo 'relacion_spacy4' en la base de datos
                    if relacionada_con_secuestro:
                        cursor.execute("UPDATE extracciones SET relacion_spacy4 = 'Sí' WHERE id = %s", (id_noticia,))
                        print(f"Noticia ID {id_noticia} relacionada con secuestro. Justificación: {justificacion}")
                    else:
                        cursor.execute("UPDATE extracciones SET relacion_spacy4 = 'No' WHERE id = %s", (id_noticia,))
                        print(f"Noticia ID {id_noticia} NO relacionada con secuestro. Justificación: {justificacion}")
                else:
                    # Si el texto está vacío, marcar como no relacionada
                    cursor.execute("UPDATE extracciones SET relacion_spacy4 = 'No' WHERE id = %s", (id_noticia,))
                    print(f"Noticia ID {id_noticia} NO relacionada con secuestro (texto vacío).")

                # Guardar los cambios inmediatamente después de procesar cada noticia
                conexion.commit()

    finally:
        conexion.close()

# --- FUNCIÓN PARA AGREGAR CAMPOS NECESARIOS ---
def agregar_campos_lugares():
    conexion = conectar_bd()
    try:
        with conexion.cursor() as cursor:
            # Verificar si los campos ya existen antes de intentar crearlos
            cursor.execute("SHOW COLUMNS FROM extracciones LIKE 'pais'")
            resultado_pais = cursor.fetchone()

            cursor.execute("SHOW COLUMNS FROM extracciones LIKE 'estado'")
            resultado_estado = cursor.fetchone()

            cursor.execute("SHOW COLUMNS FROM extracciones LIKE 'municipio'")
            resultado_municipio = cursor.fetchone()

            cursor.execute("SHOW COLUMNS FROM extracciones LIKE 'ciudad'")
            resultado_ciudad = cursor.fetchone()

            # Agregar los campos si no existen
            if not resultado_pais:
                cursor.execute("ALTER TABLE extracciones ADD COLUMN pais VARCHAR(255)")
                print("Campo 'pais' agregado.")

            if not resultado_estado:
                cursor.execute("ALTER TABLE extracciones ADD COLUMN estado VARCHAR(255)")
                print("Campo 'estado' agregado.")

            if not resultado_municipio:
                cursor.execute("ALTER TABLE extracciones ADD COLUMN municipio VARCHAR(255)")
                print("Campo 'municipio' agregado.")

            if not resultado_ciudad:
                cursor.execute("ALTER TABLE extracciones ADD COLUMN ciudad VARCHAR(255)")
                print("Campo 'ciudad' agregado.")

            conexion.commit()

    except Exception as e:
        print(f"Error al agregar campos: {e}")

    finally:
        conexion.close()

# --- FUNCIONES RELACIONADAS CON LA EXTRACCIÓN DE LUGARES ---
def extraer_lugares_regex(texto):
    # Expresión regular combinada para identificar ubicaciones (ciudades, municipios, etc.)
    regex = r"(?:^|\.\s|\-\s|\b)([A-Z][a-z]+(?: [A-Z][a-z]+)*)[\.\-]?\b"
    lugares = re.findall(regex, texto)
    # Unir las coincidencias para obtener lugares completos (si aplica)
    lugares_completos = [lugar for lugar in lugares]
    return lugares_completos

def validar_lugar_bd_local(lugar):
    conexion = conectar_bd()
    if not conexion:
        return None, None, None  # No se pudo conectar a la base de datos

    try:
        with conexion.cursor() as cursor:
            # Utilizar LIKE para permitir coincidencias parciales
            sql_municipio = """
            SELECT municipios.nombre AS municipio_nombre, estados.nombre AS estado_nombre, 'México' AS pais_nombre
            FROM municipios
            INNER JOIN estados ON municipios.estado = estados.id
            WHERE municipios.nombre LIKE %s
            """
            cursor.execute(sql_municipio, (f"%{lugar}%",))
            resultado_municipio = cursor.fetchone()

            if resultado_municipio:
                municipio = resultado_municipio['municipio_nombre']
                estado = resultado_municipio['estado_nombre']
                pais = resultado_municipio['pais_nombre']
                print(f"Lugar encontrado en BD: Municipio: {municipio}, Estado: {estado}, País: {pais}")
                return "México", estado, municipio  # Retornar información completa

            # Verificar si el lugar es un estado con coincidencia parcial
            sql_estado = "SELECT nombre AS estado_nombre, 'México' AS pais_nombre FROM estados WHERE nombre LIKE %s"
            cursor.execute(sql_estado, (f"%{lugar}%",))
            resultado_estado = cursor.fetchone()

            if resultado_estado:
                estado = resultado_estado['estado_nombre']
                pais = resultado_estado['pais_nombre']
                print(f"Lugar encontrado en BD: Estado: {estado}, País: {pais}")
                return "México", estado, None  # No hay municipio, pero hay estado y país

            return None, None, None  # No se encontró en la base de datos local

    except Exception as e:
        print(f"Error al validar lugar en la base de datos local: {e}")
        return None, None, None

    finally:
        conexion.close()

def validar_lugar_via_geonames(lugar, usuario):
    url = f"http://api.geonames.org/searchJSON?q={lugar}&maxRows=1&username={usuario}&countryBias=MX&continentCode=SA"
    try:
        response = requests.get(url)
        if response.status_code == 200:  # Verificamos que la respuesta sea exitosa
            data = response.json()
            print(f"Respuesta de GeoNames para '{lugar}': {data}")  # Depuración: Imprimir la respuesta completa de GeoNames
            if 'geonames' in data and len(data['geonames']) > 0:
                lugar_info = data['geonames'][0]
                pais = lugar_info.get('countryName')
                admin1 = lugar_info.get('adminName1')  # Estado o provincia
                print(f"Lugar: {lugar}, País: {pais}, Estado: {admin1}")  # Imprimir el país y el estado obtenidos
                return pais, admin1, lugar  # Devuelve país, estado/provincia y el municipio/ciudad
            else:
                print(f"No se encontraron resultados para '{lugar}' en GeoNames.")
                return None, None, None
        else:
            print(f"Error en la solicitud a GeoNames: {response.status_code}")
            return None, None, None
    except Exception as e:
        print(f"Error al conectar con GeoNames API: {e}")
        return None, None, None

def analizar_contexto(texto, lugares):
    doc = nlp(texto)
    relevancia = {}

    for lugar in lugares:
        relevancia[lugar] = 0
        for ent in doc.ents:
            # Considerar entidades geográficas que coincidan con nuestros lugares validados
            if ent.text.lower() in lugar.lower() and ent.label_ in ["GPE", "LOC"]:
                relevancia[lugar] += 1  # Aumentar relevancia si coincide y es una entidad geográfica

    # Ordenar los lugares por relevancia
    lugar_mas_relevante = max(relevancia, key=relevancia.get) if relevancia else None
    return lugar_mas_relevante

def extraer_lugares(texto):
    # Paso 1: Extracción inicial usando expresiones regulares
    lugares_regex = extraer_lugares_regex(texto)
    print(f"Paso 1 - Lugares extraídos por regex: {lugares_regex}")  # Depuración

    pais = None
    estado = None
    municipio = None
    justificacion = []
    lugares_validados = []

    # Paso 2: Validar con la base de datos local de municipios/estados
    for lugar in lugares_regex:
        # Primero, verificamos si el lugar está en nuestro diccionario de localidades
        if lugar in localidades:
            info = localidades[lugar]
            pais = info['pais']
            estado = info['estado']
            municipio = lugar
            lugares_validados.append((pais, estado, municipio))
            justificacion.append(f"'{lugar}' encontrado en el diccionario de localidades: {estado}, {pais}")
            continue  # Pasamos al siguiente lugar

        # Si no está en el diccionario, validamos contra la base de datos local
        pais_local, estado_local, municipio_local = validar_lugar_bd_local(lugar)
        if pais_local and estado_local:
            # Si encontramos información suficiente en la base de datos, guardamos y seguimos
            pais = pais_local
            estado = estado_local
            municipio = municipio_local
            lugares_validados.append((pais, estado, municipio))
            justificacion.append(f"'{lugar}' validado en la base de datos local: {estado}, {pais}")

    # Si hay múltiples lugares validados, proceder al análisis semántico
    if len(lugares_validados) > 1:
        lugares_nombres = [f"{municipio or ''}, {estado}" for _, estado, municipio in lugares_validados]
        lugar_relevante = analizar_contexto(texto, lugares_nombres)
        justificacion.append(f"Lugar más relevante según análisis semántico: {lugar_relevante}")

        # Extraer la información del lugar más relevante
        for pais_val, estado_val, municipio_val in lugares_validados:
            if lugar_relevante in f"{municipio_val or ''}, {estado_val}":
                pais, estado, municipio = pais_val, estado_val, municipio_val
                break

    # Paso 3: Si no se encontró información suficiente en la base de datos local, proceder a GeoNames
    if not pais or not estado:
        for lugar in lugares_regex:
            pais_geo, estado_geo, municipio_geo = validar_lugar_via_geonames(lugar, usuario_geonames)
            if pais_geo and estado_geo:
                pais = pais_geo
                estado = estado_geo
                municipio = municipio_geo
                justificacion.append(f"'{lugar}' clasificado en GeoNames: {estado_geo}, {pais_geo}")
                break  # Detenemos la búsqueda si encontramos suficiente información en GeoNames

    # Mensajes de depuración finales
    print(f"Resultado Final - País: {pais}, Estado: {estado}, Municipio: {municipio}")
    print(f"Justificación Final de lugares: {justificacion}")

    return pais, estado, municipio, None, justificacion

def actualizar_base_datos_lugares(pais, estado, municipio, ciudad, noticia_id):
    conexion = conectar_bd()
    try:
        with conexion.cursor() as cursor:
            # Consulta para actualizar la noticia con el país, el estado, municipio y ciudad
            sql = "UPDATE extracciones SET pais=%s, estado=%s, municipio=%s, ciudad=%s WHERE id=%s"
            cursor.execute(sql, (pais, estado, municipio, ciudad, noticia_id))
            conexion.commit()

            print(f"Noticia {noticia_id} actualizada con País: {pais}, Estado: {estado}, Municipio: {municipio}, Ciudad: {ciudad}")

    except Exception as e:
        print(f"Error al actualizar la base de datos: {e}")

    finally:
        conexion.close()

def procesar_noticias_lugares():
    conexion = conectar_bd()
    try:
        with conexion.cursor() as cursor:
            # Consulta para obtener noticias con "Sí" en relacion_spacy4
            sql = "SELECT id, noticia_corregida, pais, estado, municipio, ciudad FROM extracciones WHERE relacion_spacy4='Sí'"
            cursor.execute(sql)
            noticias = cursor.fetchall()

            # Procesar cada noticia
            for noticia in noticias:
                noticia_id = noticia['id']
                texto_noticia = noticia['noticia_corregida']
                pais_actual = noticia['pais']
                estado_actual = noticia['estado']
                municipio_actual = noticia['municipio']
                ciudad_actual = noticia['ciudad']

                # Saltar si cualquiera de los campos ya tiene un valor
                if pais_actual or estado_actual or municipio_actual or ciudad_actual:
                    print(f"Saltar análisis para noticia {noticia_id} (ya tiene campos llenos)")
                    continue

                # Marcar el inicio del procesamiento
                inicio = time.time()

                # Extraer y validar lugares del texto
                pais, estado, municipio, ciudad, justificacion = extraer_lugares(texto_noticia)

                # Marcar el final del procesamiento
                fin = time.time()
                tiempo_procesamiento = fin - inicio

                # Imprimir la justificación, los resultados y el tiempo de procesamiento
                print(f"\nNoticia ID: {noticia_id}")
                print(f"Justificación de lugares: {justificacion}")
                print(f"País extraído: {pais}")
                print(f"Estado extraído: {estado}")
                print(f"Municipio extraído: {municipio}")
                print(f"Ciudad extraída: {ciudad}")
                print(f"Tiempo de procesamiento: {tiempo_procesamiento:.2f} segundos")

                # Si se encontraron un país, estado, municipio o ciudad, actualizar la base de datos
                if pais or estado or municipio or ciudad:
                    actualizar_base_datos_lugares(pais, estado, municipio, ciudad, noticia_id)

    except Exception as e:
        print(f"Error al procesar noticias: {e}")

    finally:
        conexion.close()

# --- FUNCIÓN PARA DETECTAR EL MÉTODO DE CAPTURA ---
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

        # Captura en Transporte (refinada)
        [
            {"LEMMA": {"IN": ["interceptar", "abordar", "secuestrar", "asaltar", "detener", "emboscar"]}},
            {"LOWER": {"IN": ["en", "mientras", "cuando"]}},
            {"LOWER": {"IN": ["viajaba", "conducía", "se", "trasladaba"]}, "OP": "?"},
            {"LOWER": {"IN": ["en"]}, "OP": "?"},
            {"LEMMA": {"IN": ["autobús", "camioneta", "coche", "vehículo", "taxi", "transporte", "metro", "tren", "camión"]}}
        ],

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
    matcher.add("Captura_Transporte", [patrones_metodo_captura[20]])
    matcher.add("Captura_Extorsion", [patrones_metodo_captura[21], patrones_metodo_captura[22]])
    matcher.add("Captura_Virtual", [patrones_metodo_captura[23], patrones_metodo_captura[24]])
    matcher.add("Captura_Complicidad", [patrones_metodo_captura[25], patrones_metodo_captura[26]])
    matcher.add("Captura_Cartel", [patrones_metodo_captura[27], patrones_metodo_captura[28]])
    matcher.add("Suplantacion_Identidad", [patrones_metodo_captura[29]])

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
    explicaciones_final = [explicacion[metodo] for metodo in metodos_final]

    return list(metodos_detectados), [explicacion[metodo] for metodo in metodos_detectados]

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

# --- PROCESAR Y ANALIZAR NOTICIAS PARA EL MÉTODO DE CAPTURA ---
def procesar_noticias_metodo_captura():
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

# --- FUNCIÓN PARA CLASIFICAR LIBERACIÓN ---
def clasificar_liberacion(texto):
    doc = nlp(texto.lower())
    matcher = Matcher(nlp.vocab)

    # Patrones específicos para clasificar liberación
    patrones_liberacion_general = [
        [{"LEMMA": {"IN": ["liberar", "rescatar"]}}, {"OP": "+"}],
        [{"TEXT": {"REGEX": "liberado|liberaron|rescatado|rescatados|apareció sano y salvo|retornó a su hogar"}}]
    ]

    patrones_operativo = [
        [{"LEMMA": {"IN": ["operativo", "rescatar", "encontrar"]}}, {"LOWER": "policiaco", "OP": "?"}],
        [{"TEXT": {"REGEX": "fueron rescatados|fueron liberados"}}]
    ]

    patrones_autoridad = [
        [{"LEMMA": {"IN": ["elemento", "ejército", "autoridad"]}}, {"LOWER": "mexicano", "OP": "?"},
         {"LOWER": "liberar", "OP": "+"}]
    ]

    patrones_retorno = [
        [{"LEMMA": {"IN": ["retornar", "regresar", "volver"]}}, {"TEXT": {"REGEX": "a su hogar|sano y salvo"}}]
    ]

    patrones_negociacion = [
        [{"LEMMA": {"IN": ["negociar", "acordar"]}},
         {"LOWER": {"IN": ["liberación", "rescate", "retorno"]}, "OP": "?"}],
        [{"TEXT": {"REGEX": "negociación para la liberación|acuerdo de liberación|liberación por acuerdo"}}]
    ]

    # Agregamos los patrones al matcher
    matcher.add("LiberacionGeneral", patrones_liberacion_general)
    matcher.add("Operativo", patrones_operativo)
    matcher.add("Autoridad", patrones_autoridad)
    matcher.add("Retorno", patrones_retorno)
    matcher.add("Negociacion", patrones_negociacion)

    # Inicializamos variables de clasificación y justificación
    tipo_liberacion = "No clasificado"
    hubo_liberacion = False

    # Aplicamos el matcher para buscar coincidencias
    matches = matcher(doc)

    for match_id, start, end in matches:
        span = doc[start:end]
        tipo = nlp.vocab.strings[match_id]

        # Clasificación basada en tipo de patrón detectado
        if tipo == "LiberacionGeneral":
            tipo_liberacion = "Liberación general"
            hubo_liberacion = True
            break
        elif tipo == "Operativo":
            tipo_liberacion = "Liberación en operativo"
            hubo_liberacion = True
        elif tipo == "Autoridad":
            tipo_liberacion = "Liberación por autoridad"
            hubo_liberacion = True
        elif tipo == "Retorno":
            tipo_liberacion = "Retorno sin detalles"
            hubo_liberacion = True
        elif tipo == "Negociacion":
            tipo_liberacion = "Liberación por negociación"
            hubo_liberacion = True

    return hubo_liberacion, tipo_liberacion

# --- FUNCIÓN PARA VERIFICAR Y AGREGAR CAMPOS SI NO EXISTEN ---
def verificar_y_agregar_campos_liberacion():
    conexion = conectar_bd()
    try:
        with conexion.cursor() as cursor:
            # Verificar si los campos existen en la tabla
            cursor.execute("SHOW COLUMNS FROM extracciones LIKE 'liberacion'")
            existe_liberacion = cursor.fetchone()

            cursor.execute("SHOW COLUMNS FROM extracciones LIKE 'tipo_liberacion'")
            existe_tipo_liberacion = cursor.fetchone()

            # Si no existe 'liberacion', lo agregamos
            if not existe_liberacion:
                cursor.execute("ALTER TABLE extracciones ADD COLUMN liberacion VARCHAR(3)")
                print("Campo 'liberacion' agregado.")

            # Si no existe 'tipo_liberacion', lo agregamos
            if not existe_tipo_liberacion:
                cursor.execute("ALTER TABLE extracciones ADD COLUMN tipo_liberacion VARCHAR(50)")
                print("Campo 'tipo_liberacion' agregado.")

            conexion.commit()
    finally:
        conexion.close()

# --- FUNCIÓN PARA ACTUALIZAR LA BASE DE DATOS CON LOS RESULTADOS ---
def actualizar_noticia_liberacion(id_noticia, liberacion, tipo_liberacion):
    conexion = conectar_bd()
    try:
        with conexion.cursor() as cursor:
            sql = """
            UPDATE extracciones 
            SET liberacion = %s, tipo_liberacion = %s 
            WHERE id = %s
            """
            cursor.execute(sql, (liberacion, tipo_liberacion, id_noticia))
            conexion.commit()
    finally:
        conexion.close()

# --- PROCESAR Y ANALIZAR NOTICIAS PARA CLASIFICAR LIBERACIÓN ---
def procesar_noticias_liberacion():
    # Verificamos y agregamos los campos si no existen
    verificar_y_agregar_campos_liberacion()

    # Obtener y procesar noticias
    noticias = obtener_noticias()
    for noticia in noticias:
        id_noticia = noticia['id']
        texto_noticia = noticia['noticia_corregida']

        # Clasificación del tipo de liberación y justificación
        hubo_liberacion, tipo_liberacion = clasificar_liberacion(texto_noticia)

        # Mostrar resultados de la clasificación
        print(f"\n--- Analizando noticia con ID: {id_noticia} ---")
        print(f"¿Hubo liberación?: {'Sí' if hubo_liberacion else 'No'}")
        print(f"Tipo de liberación: {tipo_liberacion}")

        # Actualizar la base de datos con los resultados
        actualizar_noticia_liberacion(id_noticia, 'Sí' if hubo_liberacion else 'No', tipo_liberacion)

# --- FUNCIÓN PARA EXTRAER LA FECHA DEL SECUESTRO ---
def extraer_fecha_secuestro(texto, fecha_publicacion):
    doc = nlp(texto.lower())

    # Inicializamos el Matcher de spaCy
    matcher = Matcher(nlp.vocab)

    # Patrones para identificar oraciones relacionadas con el secuestro
    patrones_secuestro = [
        [{"LEMMA": {"IN": ["secuestro", "privar", "raptar", "levantar"]}}],
        [{"LOWER": {"IN": ["privado", "privada"]}}, {"LOWER": "de"}, {"LOWER": "su"}, {"LOWER": "libertad"}],
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

        # Ampliamos el texto a analizar para capturar fechas cercanas
        contexto_ampliado = obtener_contexto_ampliado(sent, doc)

        # Buscamos fechas en el contexto ampliado usando expresiones regulares
        fechas_en_contexto = extraer_fechas_en_texto(contexto_ampliado)
        if fechas_en_contexto:
            for fecha_texto in fechas_en_contexto:
                fechas_detectadas.append((fecha_texto, contexto_ampliado))
        else:
            # Si no se encuentra fecha en el contexto, buscamos en la oración anterior
            sentence_index = sentences.index(sent)
            if sentence_index > 0:
                oracion_anterior = sentences[sentence_index - 1]
                contexto_ampliado = obtener_contexto_ampliado(oracion_anterior, doc)
                fechas_en_contexto_anterior = extraer_fechas_en_texto(contexto_ampliado)
                if fechas_en_contexto_anterior:
                    for fecha_texto in fechas_en_contexto_anterior:
                        fechas_detectadas.append((fecha_texto, contexto_ampliado))

    # Extraemos la fecha de publicación para usarla como referencia
    dia_pub, mes_pub, año_pub = extraer_fecha_publicacion(fecha_publicacion)

    # Si no se detectó ninguna fecha en contextos relevantes, utilizamos la fecha de publicación
    if not fechas_detectadas:
        return "No se encontró fecha en el texto; se utiliza la fecha de publicación.", dia_pub, mes_pub, año_pub
    else:
        # Asumimos que la primera fecha detectada es la relevante
        fecha_texto, contexto = fechas_detectadas[0]
        dia, mes, año = obtener_componentes_fecha(fecha_texto, texto, dia_pub, mes_pub, año_pub)
        resultado = f"Fecha del secuestro: {fecha_texto}\nContexto: '{contexto.strip()}'"
        return resultado, dia, mes, año

# --- FUNCIÓN PARA OBTENER EL CONTEXTO AMPLIADO ---
def obtener_contexto_ampliado(sentencia, doc):
    # Incluimos la oración actual, la anterior y la siguiente para ampliar el contexto
    sentences = list(doc.sents)
    sentence_index = sentences.index(sentencia)
    contexto = sentencia.text

    if sentence_index > 0:
        contexto = sentences[sentence_index - 1].text + ' ' + contexto
    if sentence_index < len(sentences) - 1:
        contexto += ' ' + sentences[sentence_index + 1].text

    return contexto

# --- FUNCIÓN PARA EXTRAER FECHAS EN UN TEXTO USANDO EXPRESIONES REGULARES ---
def extraer_fechas_en_texto(texto):
    patrones_fecha = [
        r"\b(desde el \d{1,2} de (enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)( del? año \d{4}| de \d{4})?)\b",
        r"\b(\d{1,2} de (enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)( del? año \d{4}| de \d{4})?)\b",
        r"\b((desde el )?(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)( del? año \d{4}| de \d{4}))\b",
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
def obtener_componentes_fecha(fecha_texto, texto_completo, dia_pub, mes_pub, año_pub):
    # Convertimos la fecha de publicación en un objeto datetime
    try:
        fecha_base = datetime(int(año_pub), int(mes_pub), int(dia_pub))
    except ValueError:
        # Si la fecha de publicación no es válida, usamos la fecha actual
        fecha_base = datetime.now()

    # Ajustamos la fecha base si en el texto se menciona "el año pasado", etc.
    try:
        if 'el año pasado' in fecha_texto.lower():
            fecha_base = fecha_base.replace(year=fecha_base.year - 1)
        elif 'este año' in fecha_texto.lower():
            pass  # Usamos el año de la fecha base
        elif 'este mes' in fecha_texto.lower():
            pass  # Usamos el mes de la fecha base
        elif 'el mes pasado' in fecha_texto.lower():
            mes_anterior = fecha_base.month - 1 if fecha_base.month > 1 else 12
            año_ajustado = fecha_base.year if fecha_base.month > 1 else fecha_base.year - 1
            fecha_base = fecha_base.replace(month=mes_anterior, year=año_ajustado)
    except ValueError as e:
        print(f"Error al ajustar la fecha base: {e}")
        # Si ocurre un error al ajustar la fecha, continuamos sin modificar fecha_base
        pass

    # Eliminamos palabras como "desde el" del texto de la fecha para una mejor interpretación
    fecha_texto_limpio = re.sub(r'\bdesde el\b', '', fecha_texto, flags=re.IGNORECASE).strip()

    fecha_parseada = dateparser.parse(
        fecha_texto_limpio,
        languages=['es'],
        settings={'RELATIVE_BASE': fecha_base, 'PREFER_DATES_FROM': 'past'}
    )

    dia = ''
    mes = ''
    año = ''

    if fecha_parseada:
        dia = str(fecha_parseada.day)
        mes = str(fecha_parseada.month)
        año = str(fecha_parseada.year)

    # Si no se pudo obtener el año numérico, usamos el año de publicación
    if not año:
        año = año_pub

    # Si no se pudo obtener el mes numérico, usamos el mes de publicación
    if not mes:
        mes = mes_pub

    # --- Implementamos la lógica solicitada ---
    if mes and año:
        if mes_pub:  # Aseguramos que mes_pub no esté vacío
            if int(mes) > int(mes_pub):
                año = str(int(año) - 1)

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

# --- PROCESAR Y ANALIZAR NOTICIAS PARA EXTRAER LA FECHA DEL SECUESTRO ---
def procesar_noticias_fecha_secuestro():
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

# --- PROCESAR Y ANALIZAR NOTICIAS PARA EXTRAER EL PERFIL DE LA VÍCTIMA ---
def procesar_noticias_perfil_victima():
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

# --- NUEVO CÓDIGO: EXTRACCIÓN DEL TIPO DE SECUESTRO ---

# --- FUNCIÓN PARA VERIFICAR Y AGREGAR LOS CAMPOS 'tipo_secuestro' Y 'justificacion_tipo_secuestro' ---
def verificar_y_agregar_campos_tipo_secuestro():
    conexion = conectar_bd()
    try:
        with conexion.cursor() as cursor:
            # Verificar y agregar el campo 'tipo_secuestro'
            cursor.execute("SHOW COLUMNS FROM extracciones LIKE 'tipo_secuestro'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE extracciones ADD COLUMN tipo_secuestro VARCHAR(255)")
                print("Campo 'tipo_secuestro' agregado.")

            # Verificar y agregar el campo 'justificacion_tipo_secuestro'
            cursor.execute("SHOW COLUMNS FROM extracciones LIKE 'justificacion_tipo_secuestro'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE extracciones ADD COLUMN justificacion_tipo_secuestro TEXT")
                print("Campo 'justificacion_tipo_secuestro' agregado.")

            conexion.commit()
    finally:
        conexion.close()

# --- FUNCIÓN PARA EXTRAER EL TIPO DE SECUESTRO CON ANÁLISIS CONTEXTUAL ---
def extraer_tipo_secuestro(texto):
    doc = nlp(texto)
    categorias_identificadas = set()
    justificaciones = []

    # Listas de palabras clave y patrones para diferentes tipos de secuestro
    patrones = {
        'Secuestro exprés': {
            'frases_directas': ['secuestro exprés', 'secuestro express', 'secuestro rápido', 'plagio exprés'],
        },
        'Secuestro virtual': {
            'frases_directas': ['secuestro virtual', 'extorsión telefónica', 'secuestro simulado', 'secuestro falso'],
        },
        'Secuestro con fines de extorsión': {
            'indicadores': ['exigieron rescate', 'exigieron dinero', 'exigió pago', 'demandaron rescate', 'pidieron rescate', 'exigencia económica', 'exigió dinero'],
        },
        'Secuestro económico': {
            'victimas': ['empresario', 'comerciante', 'banquero', 'industrial', 'empresaria'],
            'acciones': ['secuestrado', 'plagiado', 'privado de su libertad'],
        },
        'Secuestro político': {
            'roles': ['alcalde', 'senador', 'diputado', 'gobernador', 'presidente', 'suplente', 'ministro', 'regidor', 'funcionario', 'político', 'activista', 'candidato'],
        },
        'Desaparición forzada': {
            'agentes': ['policía', 'autoridad', 'militar', 'fuerzas de seguridad', 'agentes'],
            'acciones': ['detuvieron', 'detenido', 'arrestaron', 'arrestado'],
            'indicadores': ['desde entonces no se sabe', 'no se sabe nada de'],
        },
        'Secuestro por delincuencia organizada': {
            'grupos_criminales': ['cártel', 'cartel', 'banda', 'grupo delictivo', 'grupo criminal', 'delincuencia organizada', 'grupos armados', 'criminales'],
            'acciones': ['secuestró', 'secuestraron', 'plagiaron', 'privaron de la libertad'],
        },
        'Secuestro de migrantes': {
            'victimas': ['migrantes', 'inmigrantes', 'centroamericanos', 'migrantes mexicanos', 'migrantes extranjeros'],
            'acciones': ['secuestrados', 'plagiados', 'privados de su libertad'],
        },
        'Secuestro familiar': {
            'relaciones_familiares': ['padre', 'madre', 'hijo', 'hija', 'hermano', 'hermana', 'esposo', 'esposa', 'tío', 'tía', 'abuelo', 'abuela', 'sobrino', 'sobrina', 'primo', 'prima', 'familiar', 'pariente'],
            'verbos_relacionados': ['secuestrar', 'privar', 'raptar', 'plagiar'],
        },
        'Secuestro de menores': {
            'victimas': ['niño', 'niña', 'menor', 'adolescente', 'bebé', 'infante'],
            'verbos_relacionados': ['secuestro', 'secuestrar', 'plagiar', 'raptar', 'privar'],
        },
    }

    texto_normalizado = normalizar_texto(texto)

    # Detección de tipos de secuestro mencionados directamente
    for tipo, detalles in patrones.items():
        if 'frases_directas' in detalles:
            for frase in detalles['frases_directas']:
                if frase in texto_normalizado:
                    categorias_identificadas.add(tipo)
                    justificaciones.append(f"Detectada frase directa '{frase}' para '{tipo}'.")
                    break  # Evita duplicados

    # Análisis de oraciones
    for sent in doc.sents:
        sent_text = sent.text.lower()
        sent_doc = nlp(sent.text)

        # Si ya se detectó el tipo por frase directa, podemos omitir análisis adicionales para ese tipo
        tipos_analizar = set(patrones.keys()) - categorias_identificadas

        # Secuestro de menores
        if 'Secuestro de menores' in tipos_analizar:
            for token in sent_doc:
                if token.lemma_ in patrones['Secuestro de menores']['verbos_relacionados'] and token.pos_ == 'VERB':
                    objeto = None
                    # Obtener el objeto directo del verbo
                    for child in token.children:
                        if child.dep_ in ('dobj', 'obj'):
                            objeto = child
                            break
                    if objeto:
                        objeto_text = objeto.text.lower()
                        # Verificar si el objeto es un menor
                        if any(victima in objeto_text for victima in patrones['Secuestro de menores']['victimas']):
                            categorias_identificadas.add('Secuestro de menores')
                            justificaciones.append(f"Detectado menor como víctima en: '{sent.text.strip()}'.")
                            break

        # Secuestro político
        if 'Secuestro político' in tipos_analizar:
            for ent in sent_doc.ents:
                if ent.label_ == 'PER' and any(role in ent.text.lower() for role in patrones['Secuestro político']['roles']):
                    if any(verb.lemma_ in ['secuestro', 'privar', 'plagiar', 'raptar'] for verb in sent_doc if verb.pos_ == 'VERB'):
                        categorias_identificadas.add('Secuestro político')
                        justificaciones.append(f"Detectado verbo de secuestro relacionado con persona política '{ent.text}'.")
                        break

        # (Continuar con otros tipos de secuestro según patrones)

    # Si no se encontró ningún tipo específico, pero se menciona "secuestro", se asigna "Secuestro general"
    if not categorias_identificadas and 'secuestro' in texto_normalizado:
        categorias_identificadas.add('Secuestro general')
        justificaciones.append("No se detectó un tipo específico, pero se mencionó 'secuestro'.")

    return ', '.join(categorias_identificadas), '; '.join(justificaciones)

# --- FUNCIÓN PARA ACTUALIZAR EL TIPO DE SECUESTRO EN LA BASE DE DATOS ---
def actualizar_tipo_secuestro(id_noticia, tipo_secuestro, justificacion):
    conexion = conectar_bd()
    try:
        with conexion.cursor() as cursor:
            sql = "UPDATE extracciones SET tipo_secuestro = %s, justificacion_tipo_secuestro = %s WHERE id = %s"
            cursor.execute(sql, (tipo_secuestro, justificacion, id_noticia))
            conexion.commit()
    finally:
        conexion.close()

# --- PROCESAR Y ANALIZAR NOTICIAS PARA EXTRAER EL TIPO DE SECUESTRO ---
def procesar_noticias_tipo_secuestro():
    # Verificar y agregar los campos si no existen
    verificar_y_agregar_campos_tipo_secuestro()

    # Obtener y procesar noticias
    noticias = obtener_noticias()
    for noticia in noticias:
        id_noticia = noticia['id']
        texto_noticia = noticia['noticia_corregida']

        # Extraer el tipo de secuestro y la justificación
        tipo_secuestro, justificacion = extraer_tipo_secuestro(texto_noticia)

        # Mostrar resultados del análisis
        print(f"\n--- Analizando noticia con ID: {id_noticia} ---")
        print(f"Tipo de secuestro detectado: {tipo_secuestro}")
        print(f"Justificación: {justificacion}")

        # Actualizar la base de datos con el tipo de secuestro y la justificación
        actualizar_tipo_secuestro(id_noticia, tipo_secuestro, justificacion)

# --- EJECUCIÓN DEL PROGRAMA ---
if __name__ == "__main__":

    limpiar_noticias()                      # Limpiamos las noticias y creamos 'noticia_corregida'
    procesar_noticias_relacion()            # Clasificamos si están relacionadas con secuestros
    agregar_campos_lugares()                # Agregamos los campos de lugares si no existen
    procesar_noticias_lugares()             # Extraemos lugares
    procesar_noticias_metodo_captura()      # Detectamos el método de captura
    procesar_noticias_liberacion()          # Clasificamos la liberación
    procesar_noticias_fecha_secuestro()     # Extraemos la fecha del secuestro
    procesar_noticias_perfil_victima()      # Extraemos el perfil de la víctima
    procesar_noticias_tipo_secuestro()      # Extraemos el tipo de secuestro
