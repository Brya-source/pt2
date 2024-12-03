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

# Validar si un lugar está en la base de datos local de estados/municipios
def validar_lugar_bd_local(lugar):
    connection = conectar_bd_local()
    if not connection:
        return None, None, None  # No se pudo conectar a la base de datos

    try:
        cursor = connection.cursor()

        # Utilizar LIKE para permitir coincidencias parciales
        sql_municipio = """
        SELECT municipios.nombre, estados.nombre, 'México'
        FROM municipios
        INNER JOIN estados ON municipios.estado = estados.id
        WHERE municipios.nombre LIKE %s
        """
        cursor.execute(sql_municipio, (f"%{lugar}%",))
        resultado_municipio = cursor.fetchone()

        if resultado_municipio:
            municipio, estado, pais = resultado_municipio
            print(f"Lugar encontrado en BD: Municipio: {municipio}, Estado: {estado}, País: {pais}")
            return "México", estado, municipio  # Retornar información completa

        # Verificar si el lugar es un estado con coincidencia parcial
        sql_estado = "SELECT nombre, 'México' FROM estados WHERE nombre LIKE %s"
        cursor.execute(sql_estado, (f"%{lugar}%",))
        resultado_estado = cursor.fetchone()

        if resultado_estado:
            estado, pais = resultado_estado
            print(f"Lugar encontrado en BD: Estado: {estado}, País: {pais}")
            return "México", estado, None  # No hay municipio, pero hay estado y país

        return None, None, None  # No se encontró en la base de datos local

    except Exception as e:
        print(f"Error al validar lugar en la base de datos local: {e}")
        return None, None, None

    finally:
        connection.close()

# Validar lugares usando GeoNames si no están en la base de datos local
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
# Función para actualizar la base de datos con los lugares extraídos
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
