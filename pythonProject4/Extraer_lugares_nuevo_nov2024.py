import pymysql
import time
import requests
import re
import spacy
from transformers import pipeline

# Cargar el modelo de spaCy en español
nlp = spacy.load('es_core_news_md')

# Usar el modelo NER de Hugging Face para BART
ner_model = pipeline("ner", model="dccuchile/bert-base-spanish-wwm-cased", aggregation_strategy="simple")

# Diccionario de municipios/localidades asociadas con sus estados y países


# Aquí pones tu nombre de usuario de GeoNames
usuario_geonames = "bryanhernandez"  # Reemplaza con tu nombre de usuario de GeoNames

# Lista de palabras comunes que no deben ser validadas como lugares
PALABRAS_IRRELEVANTES = [
    "El", "Los", "La", "Las", "Un", "Una", "De", "Del", "En", "Sin", "Con", "No", "Ven", "Al",
    "Centro", "Ciudad", "Norte", "Sur", "Este", "Oeste", "Ortega", "Felipe", "Cruz", "San", "General", "Todo",
    "Lo", "Nacional", "Por", "Durante", "Anaya", "Fuentes", "Instituto", "Han", "He", "Has", "Tu", "Progreso",
    "Internacional", "Fue", "Ocho", "Manuel", "Eduardo", "Como", "Gabriel", "Pero", "Para", "Rafael", "Juan", "Luis", "Tres",
    "Alto", "Uno", "Dos", "Tres", "Cuatro", "Cinco", "Carlos", "Gustavo", "Genaro", "Francisco", "Miguel", "Estado", "Jorge",
    "Nacional", "Casas", "Mata", "Santa", "China", "Agua", "Nuevo", "Valle", "Castillo", "Camargo", "Guadalupe", "Santiago", "Tierra"
    "Benito", "Nuevo", "Pedro", "Isidro", "José", "María", "Vicente", "Nicolas", "Emiliano", "Pueblo", "Casa", "Santa", "Padilla"
    "Marcos", "Soto", "Benito", "Ruiz", "Salvador", "Reforma", "Carrillo", "Martinez", "Gonzalez"
]

# Lista base de palabras clave relacionadas con incidentes
PALABRAS_CLAVE_BASE = [
    "secuestro", "hecho", "incidente", "caso", "ubicado", "encontrado", "rescatado"
]

# Raíces verbales para generar conjugaciones
VERBOS_CLAVE = [
    "ocurrir", "suceder", "realizar", "encontrar", "rescatar"
]

# Generar conjugaciones de verbos clave usando spaCy
def generar_conjugaciones(verbos_clave):
    conjugaciones = set()
    for verbo in verbos_clave:
        doc = nlp(verbo)
        for token in doc:
            if token.pos_ == "VERB":
                conjugaciones.add(token.lemma_)  # Agregar la raíz
                conjugaciones.add(token.text)  # Forma base
                # Ejemplos de formas comunes
                conjugaciones.update([
                    f"{token.lemma_}á",  # Futuro
                    f"{token.lemma_}á",  # Futuro perfecto
                    f"{token.lemma_}ía",  # Condicional
                    f"{token.lemma_}ó",  # Pasado perfecto
                    f"ha {token.lemma_}",  # Presente perfecto
                    f"había {token.lemma_}",  # Pasado perfecto
                    f"habrá {token.lemma_}",  # Futuro perfecto
                    f"haya {token.lemma_}",  # Subjuntivo perfecto
                    f"hubiera {token.lemma_}",  # Subjuntivo pluscuamperfecto
                ])
    return conjugaciones

# Validar si un lugar está relacionado semánticamente con los hechos reportados
def validar_relacion_hechos(texto, lugares):
    doc = nlp(texto)
    relevancia = {}

    # Generar conjugaciones de los verbos clave
    conjugaciones = generar_conjugaciones(VERBOS_CLAVE)

    # Agregar las palabras clave base y sus derivaciones
    palabras_clave = set(PALABRAS_CLAVE_BASE).union(conjugaciones)

    for lugar in lugares:
        relevancia[lugar] = 0
        for token in doc:
            # Verificar si el lugar está relacionado con palabras clave o verbos relevantes
            if lugar.lower() in token.text.lower():
                for palabra in palabras_clave:
                    if palabra in [w.text.lower() for w in token.head.subtree]:
                        relevancia[lugar] += 1

    lugar_mas_relevante = max(relevancia, key=relevancia.get) if relevancia else None
    return lugar_mas_relevante

def agregar_campos():
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='Soccer.8a',
            db='noticias'
        )
        cursor = connection.cursor()

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

        connection.commit()

    except Exception as e:
        print(f"Error al agregar campos: {e}")

    finally:
        connection.close()

# Mapeo de abreviaturas de estados a nombres completos
# Mapeo de abreviaturas de estados a nombres completos en México
ABREVIATURAS_ESTADOS = {
    "Ags.": "Aguascalientes",
    "BC.": "Baja California",
    "BCS.": "Baja California Sur",
    "Camp.": "Campeche",
    "Chis.": "Chiapas",
    "Chih.": "Chihuahua",
    "CDMX.": "Ciudad de México",
    "Coah.": "Coahuila",
    "Col.": "Colima",
    "Dgo.": "Durango",
    "Edomex.": "Estado de México",
    "Gto.": "Guanajuato",
    "Gro.": "Guerrero",
    "Hgo.": "Hidalgo",
    "Jal.": "Jalisco",
    "Mich.": "Michoacán",
    "Mor.": "Morelos",
    "Nay.": "Nayarit",
    "NL.": "Nuevo León",
    "Oax.": "Oaxaca",
    "Pue.": "Puebla",
    "Qro.": "Querétaro",
    "QR.": "Quintana Roo",
    "SLP.": "San Luis Potosí",
    "Sin.": "Sinaloa",
    "Son.": "Sonora",
    "Tab.": "Tabasco",
    "Tamps.": "Tamaulipas",
    "Tlax.": "Tlaxcala",
    "Ver.": "Veracruz",
    "Yuc.": "Yucatán",
    "Zac.": "Zacatecas"
}

def extraer_primer_lugar(texto):
    # Expresión regular para capturar lugar y estado abreviado
    regex_inicio = r"^(?P<lugar>[A-ZÁÉÍÓÚÑa-záéíóúñ\s]+),?\s?(?P<estado_abrev>[A-Z][a-z]+\.)\s?[-—\.]"
    coincidencia = re.match(regex_inicio, texto)

    if coincidencia:
        lugar = coincidencia.group("lugar").strip()
        estado_abrev = coincidencia.group("estado_abrev").strip()

        # Convertir abreviatura del estado al nombre completo si existe
        estado_completo = ABREVIATURAS_ESTADOS.get(estado_abrev, estado_abrev)

        # Combinar lugar y estado completo para validación
        lugar_completo = f"{lugar}, {estado_completo}"

        print(f"Lugar detectado al inicio: {lugar_completo}")
        return lugar_completo
    return None

ALIAS_LUGARES = {
    "Tuxtla": "Tuxtla Gutiérrez",
    "Distrito Federal": "Ciudad de México",
    "Victoria": "Ciudad Victoria"
    # Puedes agregar más alias si es necesario
}

# Función para extraer lugares usando expresiones regulares mejoradas
def extraer_lugares_regex(texto):
    # Expresión regular combinada para identificar ubicaciones (ciudades, municipios, etc.)
    regex = r"(?:^|\.\s|\-\s|\b)([A-Z][a-z]+(?: [A-Z][a-z]+)*)[\.\-]?\b"
    lugares = re.findall(regex, texto)
    # Unir las coincidencias para obtener lugares completos (si aplica)
    lugares_completos = [lugar for lugar in lugares]
    return lugares_completos

# Conectar a la base de datos de municipios/estados
def conectar_bd_local():
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='Soccer.8a',
            db='noticias'
        )
        return connection
    except Exception as e:
        print(f"Error al conectar con la base de datos: {e}")
        return None

def validar_lugar_bd_local(lugar):
    connection = conectar_bd_local()
    if not connection:
        return None, None, None  # No se pudo conectar a la base de datos

    try:
        cursor = connection.cursor()

        # Verificar si el lugar está en los alias comunes
        if lugar in ALIAS_LUGARES:
            lugar_completo = ALIAS_LUGARES[lugar]
            print(f"Lugar '{lugar}' reconocido como alias de '{lugar_completo}'. Verificando en la BD...")
            lugar = lugar_completo

        # Verificar si el lugar es un estado (coincidencia exacta)
        sql_estado = "SELECT nombre, 'México' FROM estados WHERE nombre = %s"
        cursor.execute(sql_estado, (lugar,))
        resultado_estado = cursor.fetchone()

        if resultado_estado:
            estado, pais = resultado_estado
            print(f"Lugar encontrado en BD como Estado exacto: {estado}, País: {pais}.")
            return "México", estado, None  # Detener búsqueda aquí si es un estado completo

        # Verificar si el lugar es un municipio (coincidencia exacta)
        sql_municipio = """
        SELECT municipios.nombre, estados.nombre, 'México'
        FROM municipios
        INNER JOIN estados ON municipios.estado = estados.id
        WHERE municipios.nombre = %s
        """
        cursor.execute(sql_municipio, (lugar,))
        resultado_municipio = cursor.fetchone()

        if resultado_municipio:
            municipio, estado, pais = resultado_municipio
            print(f"Lugar encontrado en BD como Municipio exacto: Municipio: {municipio}, Estado: {estado}, País: {pais}.")
            return "México", estado, municipio  # Detener búsqueda aquí si es un municipio completo

        # Validar coincidencias parciales considerando palabras completas seguidas de espacio
        if " " not in lugar.strip():  # Solo palabras simples
            # Buscar coincidencias parciales para municipios
            sql_municipio_parcial = """
            SELECT municipios.nombre, estados.nombre, 'México'
            FROM municipios
            INNER JOIN estados ON municipios.estado = estados.id
            WHERE municipios.nombre LIKE %s
            """
            cursor.execute(sql_municipio_parcial, (f"{lugar} %",))
            resultado_municipio_parcial = cursor.fetchone()

            if resultado_municipio_parcial:
                municipio, estado, pais = resultado_municipio_parcial
                print(f"Lugar encontrado en BD como Municipio parcial: Municipio: {municipio}, Estado: {estado}, País: {pais}.")
                return "México", estado, municipio

            # Buscar coincidencias parciales para estados
            sql_estado_parcial = "SELECT nombre, 'México' FROM estados WHERE nombre LIKE %s"
            cursor.execute(sql_estado_parcial, (f"{lugar} %",))
            resultado_estado_parcial = cursor.fetchone()

            if resultado_estado_parcial:
                estado, pais = resultado_estado_parcial
                print(f"Lugar encontrado en BD como Estado parcial: {estado}, País: {pais}.")
                return "México", estado, None

        # Si no se encontró ningún lugar válido
        print(f"Lugar '{lugar}' no encontrado como lugar completo ni parcial válido en la BD.")
        return None, None, None

    except Exception as e:
        print(f"Error al validar lugar en la base de datos local: {e}")
        return None, None, None

    finally:
        connection.close()





def validar_lugar_via_geonames(lugar, usuario):
    # Ignorar palabras irrelevantes y lugares demasiado cortos
    if lugar in PALABRAS_IRRELEVANTES:
        print(f"Lugar '{lugar}' ignorado por estar en la lista de palabras irrelevantes.")
        return None, None, None

    if len(lugar) < 4:
        print(f"Lugar '{lugar}' ignorado por ser demasiado corto.")
        return None, None, None

    # Construir la URL para consultar GeoNames
    url = f"http://api.geonames.org/searchJSON?q={lugar}&maxRows=1&username={usuario}&countryBias=MX&continentCode=SA"
    try:
        response = requests.get(url)
        if response.status_code == 200:  # Verificar que la respuesta sea exitosa
            data = response.json()
            print(f"Respuesta de GeoNames para '{lugar}': {data}")  # Depuración

            if 'geonames' in data and len(data['geonames']) > 0:
                lugar_info = data['geonames'][0]

                # Extraer información del lugar
                pais = lugar_info.get('countryName', None)
                admin1 = lugar_info.get('adminName1', None)  # Estado o provincia
                municipio = lugar_info.get('name', None)  # Municipio o ciudad

                # Priorizar por país y estado
                if pais and admin1:
                    print(f"Lugar: {lugar}, País: {pais}, Estado: {admin1}.")
                    if pais == "México":
                        # Para México, devolver el estado y municipio (si están disponibles)
                        return pais, admin1, municipio
                    else:
                        # Para otros países, devolver solo país y estado
                        return pais, admin1, None

                # Si no hay estado, devolver solo el país
                if pais:
                    print(f"Lugar: {lugar}, País: {pais}. Estado no disponible.")
                    return pais, None, None

                print(f"Lugar: {lugar}, Información insuficiente en GeoNames.")
                return None, None, None
            else:
                print(f"No se encontraron resultados para '{lugar}' en GeoNames.")
                return None, None, None

        else:
            print(f"Error en la solicitud a GeoNames: {response.status_code}")
            return None, None, None

    except Exception as e:
        print(f"Error al conectar con GeoNames API: {e}")
        return None, None, None




# Analizar contexto para determinar el lugar más relevante
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


# Función principal que combina las técnicas y realiza análisis semántico si es necesario
def extraer_lugares(texto):
    # Paso 1: Extraer el primer lugar del texto
    lugar_inicio = extraer_primer_lugar(texto)
    if lugar_inicio:
        print(f"Primer lugar detectado: {lugar_inicio}")

        # Validar si el lugar al inicio es un municipio o estado de México
        pais_local, estado_local, municipio_local = validar_lugar_bd_local(lugar_inicio)
        if pais_local and estado_local:
            print(f"Lugar al inicio validado localmente: {lugar_inicio} -> {estado_local}, {pais_local}")
            return pais_local, estado_local, municipio_local, None, [f"Lugar inicial '{lugar_inicio}' validado"]

    # Paso 2: Continuar con el análisis estándar si el lugar al inicio no es válido
    lugares_regex = extraer_lugares_regex(texto)
    print(f"Paso 2 - Lugares extraídos por regex: {lugares_regex}")

    pais = None
    estado = None
    municipio = None
    justificacion = []
    lugares_validados = []

    # Validar lugares extraídos con regex en la base de datos local
    for lugar in lugares_regex:
        if lugar in PALABRAS_IRRELEVANTES or len(lugar) < 4:  # Ignorar irrelevantes y cortos
            print(f"Ignorando lugar irrelevante o demasiado corto: {lugar}")
            continue

        pais_local, estado_local, municipio_local = validar_lugar_bd_local(lugar)
        if pais_local and estado_local:
            pais = pais_local
            estado = estado_local
            municipio = municipio_local
            lugares_validados.append((pais, estado, municipio))
            justificacion.append(f"'{lugar}' validado en la base de datos local: {estado}, {pais}")

    # Paso 3: Si hay múltiples lugares validados, analizar relevancia semántica
    if len(lugares_validados) > 1:
        lugares_nombres = [f"{municipio or ''}, {estado}" for _, estado, municipio in lugares_validados]
        lugar_relevante = validar_relacion_hechos(texto, lugares_nombres)
        justificacion.append(f"Lugar más relevante según análisis semántico: {lugar_relevante}")

        for pais_val, estado_val, municipio_val in lugares_validados:
            if lugar_relevante in f"{municipio_val or ''}, {estado_val}":
                pais, estado, municipio = pais_val, estado_val, municipio_val
                break

    # Paso 4: Si no se encontró información suficiente en la base de datos local, proceder a GeoNames
    if not pais or not estado:
        for lugar in lugares_regex:
            if lugar in PALABRAS_IRRELEVANTES or len(lugar) < 4:  # Ignorar irrelevantes y cortos
                print(f"Ignorando lugar irrelevante o demasiado corto: {lugar}")
                continue

            pais_geo, estado_geo, municipio_geo = validar_lugar_via_geonames(lugar, usuario_geonames)
            if pais_geo and estado_geo:
                pais = pais_geo
                estado = estado_geo
                municipio = municipio_geo
                justificacion.append(f"'{lugar}' clasificado en GeoNames: {estado_geo}, {pais_geo}")
                break

    print(f"Resultado Final - País: {pais}, Estado: {estado}, Municipio: {municipio}")
    print(f"Justificación Final de lugares: {justificacion}")

    return pais, estado, municipio, None, justificacion


def actualizar_base_datos(pais, estado, municipio, ciudad, noticia_id):
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='Soccer.8a',
            db='noticias'
        )
        cursor = connection.cursor()

        # Consulta para actualizar la noticia con el país, el estado, municipio y ciudad
        sql = "UPDATE extracciones SET pais=%s, estado=%s, municipio=%s, ciudad=%s WHERE id=%s"
        cursor.execute(sql, (pais, estado, municipio, ciudad, noticia_id))
        connection.commit()

        print(f"Noticia {noticia_id} actualizada con País: {pais}, Estado: {estado}, Municipio: {municipio}, Ciudad: {ciudad}")

    except Exception as e:
        print(f"Error al actualizar la base de datos: {e}")

    finally:
        connection.close()

# Función principal que procesa las noticias
def procesar_noticias():
    try:
        # Conectar a la base de datos
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='Soccer.8a',
            db='noticias'
        )
        cursor = connection.cursor()

        # Consulta para obtener noticias con "Sí" en relacion_spacy4
        sql = "SELECT id, noticia_corregida, pais, estado, municipio, ciudad FROM extracciones WHERE relacion_spacy4='Sí'"
        cursor.execute(sql)
        noticias = cursor.fetchall()

        # Procesar cada noticia
        for noticia in noticias:
            noticia_id = noticia[0]
            texto_noticia = noticia[1]
            pais_actual = noticia[2]
            estado_actual = noticia[3]
            municipio_actual = noticia[4]
            ciudad_actual = noticia[5]

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
                actualizar_base_datos(pais, estado, municipio, ciudad, noticia_id)

    except Exception as e:
        print(f"Error al procesar noticias: {e}")

    finally:
        connection.close()

# Ejecutar el procesamiento de noticias
if __name__ == "__main__":
    agregar_campos()  # Agregar los campos pais, estado, municipio, ciudad si no existen
    procesar_noticias()  # Luego procesar las noticias
