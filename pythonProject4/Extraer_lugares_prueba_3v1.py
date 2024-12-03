import spacy
import pymysql
from transformers import pipeline
import time
import requests
import re
# Cargar el modelo de spaCy en español
nlp = spacy.load('es_core_news_md')

# Usar otro modelo NER de Hugging Face
ner_model = pipeline("ner", model="dccuchile/bert-base-spanish-wwm-cased", aggregation_strategy="simple")

# Diccionario de municipios/localidades asociadas con sus estados y países
localidades = {
    "Cuautitlán Izcalli": {"estado": "Estado de México", "pais": "México", "tipo": "municipio"},
    "Ecatepec": {"estado": "Estado de México", "pais": "México", "tipo": "municipio"},
    "Tlalnepantla": {"estado": "Estado de México", "pais": "México", "tipo": "municipio"},
    "Nezahualcóyotl": {"estado": "Estado de México", "pais": "México", "tipo": "municipio"},
    "Ciudad de México": {"estado": "Ciudad de México", "pais": "México", "tipo": "alcaldía"},
    "Monterrey": {"estado": "Nuevo León", "pais": "México", "tipo": "ciudad"},
    "Guadalajara": {"estado": "Jalisco", "pais": "México", "tipo": "ciudad"},
    "Tijuana": {"estado": "Baja California", "pais": "México", "tipo": "ciudad"},
    "Cancún": {"estado": "Quintana Roo", "pais": "México", "tipo": "ciudad"}
}

# Aquí pones tu nombre de usuario de GeoNames
usuario_geonames = "bryanhernandez"  # Reemplaza con tu nombre de usuario de GeoNames


def agregar_campos():
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='Soccer.8a',
            db='noticias_prueba'
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

# Función para extraer lugares usando BERT (NER)
def extraer_lugares_bert(texto):
    texto_truncado = truncar_texto(texto)  # Truncar antes de pasar a BERT
    entidades = ner_model(texto_truncado)
    lugares = [entidad['word'] for entidad in entidades if entidad['entity_group'] == 'LOC']
    return lugares

# Función para extraer lugares usando spaCy (NER)
def extraer_lugares_spacy(texto):
    doc = nlp(texto)
    # Extraer entidades de tipo GPE (Geopolitical Entities)
    lugares = [ent.text for ent in doc.ents if ent.label_ == "GPE"]
    return lugares

# Función para extraer lugares usando expresiones regulares mejoradas
def extraer_lugares_regex(texto):
    # Expresión regular para identificar posibles lugares (ciudades y países)
    regex = r'\b([A-Z][a-z]+(?: [A-Z][a-z]+)*)\b,?\s*([A-Z][a-z]+)'
    lugares = re.findall(regex, texto)
    # Unir las coincidencias para obtener lugares completos
    lugares_completos = [', '.join(lugar) for lugar in lugares]
    return lugares_completos

# Función para truncar el texto a un límite de 512 tokens (límite de BERT)
def truncar_texto(texto, max_len=512):
    palabras = texto.split()
    if len(palabras) > max_len:
        return ' '.join(palabras[:max_len])
    else:
        return texto

# Función para validar lugares con GeoNames API con mensajes de depuración
def validar_lugar_via_geonames(lugar, usuario):
    url = f"http://api.geonames.org/searchJSON?q={lugar}&maxRows=1&username={usuario}"
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
                return pais, admin1, "ciudad"  # Asumimos que la API devuelve "ciudades"
            else:
                print(f"No se encontraron resultados para '{lugar}' en GeoNames.")
                return None, None, None
        else:
            print(f"Error en la solicitud a GeoNames: {response.status_code}")
            return None, None, None
    except Exception as e:
        print(f"Error al conectar con GeoNames API: {e}")
        return None, None, None

# Función que combina ambas técnicas para extraer y validar lugares
def extraer_lugares(texto):
    lugares_bert = extraer_lugares_bert(texto)
    lugares_spacy = extraer_lugares_spacy(texto)
    lugares_regex = extraer_lugares_regex(texto)

    # Unir resultados de ambos métodos, evitando duplicados
    lugares_combinados = list(set(lugares_bert + lugares_spacy + lugares_regex))

    # Validar lugares y clasificarlos
    pais = None
    estado = None
    municipio = None
    ciudad = None
    tipo_localidad = None
    justificacion = []

    for lugar in lugares_combinados:
        # Primero verificamos si el lugar está en nuestro diccionario local
        if lugar in localidades:
            pais = localidades[lugar]["pais"]
            estado = localidades[lugar]["estado"]
            tipo_localidad = localidades[lugar]["tipo"]

            # Decidimos si es un municipio o una ciudad
            if tipo_localidad == "municipio":
                municipio = lugar
            else:
                ciudad = lugar

            justificacion.append(f"'{lugar}' fue validado desde la base local: {estado}, {pais}, {tipo_localidad}")
        else:
            # Si no está en el diccionario, utilizamos GeoNames
            pais_extraido, estado_extraido, tipo = validar_lugar_via_geonames(lugar, usuario_geonames)
            if pais_extraido and estado_extraido:
                pais = pais_extraido
                estado = estado_extraido
                tipo_localidad = tipo

                # Decidimos si es un municipio o una ciudad
                if tipo_localidad == "ciudad":
                    ciudad = lugar
                else:
                    municipio = lugar

                justificacion.append(f"'{lugar}' fue clasificado como {tipo_localidad} en {pais_extraido}, {estado_extraido}.")
            else:
                justificacion.append(f"'{lugar}' no fue validado como país o ciudad.")

    return pais, estado, municipio, ciudad, tipo_localidad, justificacion

# Función para actualizar la base de datos con los lugares extraídos
def actualizar_base_datos(pais, estado, municipio, ciudad, tipo_localidad, noticia_id):
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='Soccer.8a',
            db='noticias_prueba'
        )
        cursor = connection.cursor()

        # Consulta para actualizar la noticia con el país, el estado, municipio, ciudad y tipo de localidad
        sql = "UPDATE extracciones SET pais=%s, estado=%s, municipio=%s, ciudad=%s, tipo_localidad=%s WHERE id=%s"
        cursor.execute(sql, (pais, estado, municipio, ciudad, tipo_localidad, noticia_id))
        connection.commit()

        print(f"Noticia {noticia_id} actualizada con País: {pais}, Estado: {estado}, Municipio: {municipio}, Ciudad: {ciudad}, Tipo de Localidad: {tipo_localidad}")

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
            db='noticias_prueba'
        )
        cursor = connection.cursor()

        # Consulta para obtener noticias con "Sí" en relacion_spacy4
        sql = "SELECT id, noticia_corregida, pais, estado, municipio, ciudad FROM extracciones WHERE relacion_bart3='Sí'"
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
            pais, estado, municipio, ciudad, tipo_localidad, justificacion = extraer_lugares(texto_noticia)

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
            print(f"Tipo de Localidad extraída: {tipo_localidad}")
            print(f"Tiempo de procesamiento: {tiempo_procesamiento:.2f} segundos")

            # Si se encontraron un país, estado, municipio o ciudad, actualizar la base de datos
            if pais or estado or municipio or ciudad:
                actualizar_base_datos(pais, estado, municipio, ciudad, tipo_localidad, noticia_id)

    except Exception as e:
        print(f"Error al procesar noticias: {e}")

    finally:
        connection.close()

# Ejecutar el procesamiento de noticias
if __name__ == "__main__":
    agregar_campos()  # Agregar los campos pais, estado, municipio, ciudad y tipo_localidad si no existen
    procesar_noticias()  # Luego procesar las noticias
