import spacy
import re
import pymysql

# Cargar el modelo de spaCy en español
nlp = spacy.load('es_core_news_md')

# Función para agregar los campos pais y ciudad a la base de datos si no existen
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

        cursor.execute("SHOW COLUMNS FROM extracciones LIKE 'ciudad'")
        resultado_ciudad = cursor.fetchone()

        # Agregar los campos si no existen
        if not resultado_pais:
            cursor.execute("ALTER TABLE extracciones ADD COLUMN pais VARCHAR(255)")
            print("Campo 'pais' agregado.")

        if not resultado_ciudad:
            cursor.execute("ALTER TABLE extracciones ADD COLUMN ciudad VARCHAR(255)")
            print("Campo 'ciudad' agregado.")

        connection.commit()

    except Exception as e:
        print(f"Error al agregar campos: {e}")

    finally:
        connection.close()

# Función para extraer lugares usando spaCy (NER)
def extraer_lugares_spacy(texto):
    doc = nlp(texto)
    # Extraer entidades de tipo GPE (Geopolitical Entities)
    lugares = [ent.text for ent in doc.ents if ent.label_ == "GPE"]
    return lugares

# Función para extraer lugares usando expresiones regulares
def extraer_lugares_regex(texto):
    # Expresión regular para identificar posibles lugares (ciudades y estados)
    regex = r'\b([A-Z][a-z]+(?: [A-Z][a-z]+)*)\b,?\s*([A-Z][a-z]+)'
    lugares = re.findall(regex, texto)
    # Unir las coincidencias para obtener lugares completos
    lugares_completos = [', '.join(lugar) for lugar in lugares]
    return lugares_completos

# Función que combina ambas técnicas para extraer lugares
def extraer_lugares(texto):
    lugares_spacy = extraer_lugares_spacy(texto)
    lugares_regex = extraer_lugares_regex(texto)

    # Unir resultados de ambos métodos, evitando duplicados
    lugares_combinados = list(set(lugares_spacy + lugares_regex))
    return lugares_combinados

# Función para actualizar la base de datos con los lugares extraídos
def actualizar_base_datos(pais, ciudad, noticia_id):
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='Soccer.8a',
            db='noticias_prueba'
        )
        cursor = connection.cursor()

        # Consulta para actualizar la noticia con el país y la ciudad del secuestro
        sql = "UPDATE extracciones SET pais=%s, ciudad=%s WHERE id=%s"
        cursor.execute(sql, (pais, ciudad, noticia_id))
        connection.commit()

        print(f"Noticia {noticia_id} actualizada con País: {pais}, Ciudad: {ciudad}")

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
        sql = "SELECT id, noticia_corregida FROM extracciones WHERE relacion_spacy4='Sí'"
        cursor.execute(sql)
        noticias = cursor.fetchall()

        # Procesar cada noticia
        for noticia in noticias:
            noticia_id = noticia[0]
            texto_noticia = noticia[1]

            # Extraer lugares del texto
            lugares = extraer_lugares(texto_noticia)

            if lugares:
                # Lógica para decidir qué lugar corresponde a país y qué a ciudad
                pais = None
                ciudad = None

                for lugar in lugares:
                    if 'México' in lugar or lugar.endswith('país'):  # Ejemplo básico para país
                        pais = lugar
                    else:
                        ciudad = lugar  # Asignar lo que no es país como ciudad (puedes mejorar esta lógica)

                actualizar_base_datos(pais, ciudad, noticia_id)
            else:
                print(f"No se encontraron lugares en la noticia {noticia_id}")

    except Exception as e:
        print(f"Error al procesar noticias: {e}")

    finally:
        connection.close()

# Ejecutar el procesamiento de noticias
if __name__ == "__main__":
    # Primero agregamos los campos necesarios
    agregar_campos()

    # Luego procesamos las noticias
    procesar_noticias()
