import pymysql
from transformers import pipeline
import time

# --- CONFIGURACIÓN DEL MODELO BART ---

# Cargamos un modelo de clasificación zero-shot con BART
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")


# --- FUNCIÓN PARA DETECTAR SI LA NOTICIA ESTÁ RELACIONADA CON SECUESTROS Y DESCARTAR "El Mayo Zambada" ---

def es_noticia_de_secuestro_bart(titulo, descripcion):
    # Concatenar solo el título y la descripción para analizarlos
    texto_completo = f"{titulo} {descripcion}"

    # Descartamos la noticia si menciona a "El Mayo Zambada"
    if "El Mayo Zambada" in texto_completo:
        return False, "Noticia descartada por mencionar a El Mayo Zambada."

    # Definimos etiquetas para el análisis, incluyendo la nueva etiqueta "Robo a menores"
    etiquetas = ["Secuestro", "Película de secuestro", "Secuestro ficticio", "Simulacro", "Series de televisión", "Robo a menores",]

    # Utilizamos BART para clasificar si la noticia está relacionada con secuestro o no
    resultado = classifier(texto_completo, candidate_labels=etiquetas, hypothesis_template="Este texto trata sobre {}.")

    # Extraemos la etiqueta más probable y su puntuación
    etiqueta = resultado['labels'][0]
    puntuacion = resultado['scores'][0]

    # Si la etiqueta más probable es "Secuestro" o "Robo a menores" y la puntuación es suficientemente alta (> 0.45)
    es_secuestro = (etiqueta == "Secuestro" or etiqueta == "Robo a menores") and puntuacion > 0.45

    # Justificación del resultado
    justificacion = f"Etiqueta predicha: {etiqueta} con una puntuación de {puntuacion:.2f}"

    return es_secuestro, justificacion


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


# --- FUNCIÓN PARA OBTENER LOS REGISTROS DE TÍTULO Y DESCRIPCIÓN ---

def obtener_noticias():
    conexion = conectar_bd()
    try:
        with conexion.cursor() as cursor:
            # Consulta para seleccionar noticias con posibles menciones a secuestros o robo a menores, excluyendo ciertas palabras clave
            sql = """
            SELECT id, titulo, descripcion 
            FROM extracciones 
            WHERE (titulo NOT LIKE '%El Mayo Zambada%' 
            AND descripcion NOT LIKE '%El Mayo Zambada%' 
            AND titulo NOT LIKE '%El Mayo%' 
            AND descripcion NOT LIKE '%El Mayo%' 
            AND titulo NOT LIKE '%Israel%' 
            AND descripcion NOT LIKE '%Israel%')
            AND (titulo NOT LIKE '%Ovidio Guzman%' 
            AND descripcion NOT LIKE '%Ovidio Guzman%'
            AND titulo NOT LIKE '%Chapo Guzman%' 
            AND descripcion NOT LIKE '%Chapo Guzman%'
            AND titulo NOT LIKE '%Joaquin Guzman%' 
            AND descripcion NOT LIKE '%Joaquin Guzman%');
            """
            cursor.execute(sql)
            resultados = cursor.fetchall()
            return resultados
    finally:
        conexion.close()


# --- PROCESAR Y CLASIFICAR NOTICIAS ---

def procesar_noticias():
    noticias = obtener_noticias()
    conexion = conectar_bd()
    try:
        with conexion.cursor() as cursor:
            # Verificar si la columna 'relacion_bart' ya existe, si no, crearla
            cursor.execute("SHOW COLUMNS FROM extracciones LIKE 'relacion_bart3';")
            resultado = cursor.fetchone()

            if not resultado:
                cursor.execute("ALTER TABLE extracciones ADD COLUMN relacion_bart3 VARCHAR(3) DEFAULT '';")

            # Procesar cada noticia y analizar si está relacionada con secuestros o robo a menores
            for idx, noticia in enumerate(noticias):
                id_noticia = noticia['id']
                titulo = noticia['titulo']
                descripcion = noticia['descripcion']

                # Evitar análisis si menciona Ovidio, El Chapo, o Joaquín Guzmán
                if any(nombre in titulo or nombre in descripcion for nombre in ['Ovidio Guzman', 'Chapo Guzman', 'Joaquin Guzman']):
                    print(f"Noticia con ID {id_noticia} omitida por mencionar a Ovidio Guzmán, El Chapo Guzmán, o Joaquín Guzmán.")
                    cursor.execute("UPDATE extracciones SET relacion_bart3 = 'omitido' WHERE id = %s", (id_noticia,))
                    continue

                # Verificar si la noticia ya ha sido analizada
                cursor.execute("SELECT relacion_bart3 FROM extracciones WHERE id = %s", (id_noticia,))
                relacion_bart = cursor.fetchone()['relacion_bart3']

                # Si ya se ha analizado, saltamos esta noticia
                if relacion_bart is not None and relacion_bart != '':
                    print(f"\n--- La noticia con ID {id_noticia} ya ha sido analizada. Saltando... ---")
                    continue

                # Imprimimos un mensaje para indicar que estamos procesando la noticia
                print(f"\n--- Analizando noticia {idx + 1} con ID: {id_noticia} ---")
                start_time = time.time()  # Marcamos el tiempo de inicio

                # Verificar si la noticia está relacionada con un secuestro o robo a menores utilizando BART
                relacionada_con_secuestro, justificacion = es_noticia_de_secuestro_bart(titulo, descripcion)

                # Actualizar el campo 'relacion_bart' basado en el resultado del análisis
                if relacionada_con_secuestro:
                    print(f"La noticia con ID {id_noticia} está relacionada con secuestro.")
                    cursor.execute("UPDATE extracciones SET relacion_bart3 = 'sí' WHERE id = %s", (id_noticia,))
                else:
                    print(f"La noticia con ID {id_noticia} NO está relacionada con secuestro.")
                    cursor.execute("UPDATE extracciones SET relacion_bart3 = 'no' WHERE id = %s", (id_noticia,))

                # Imprimir la justificación
                print(f"Justificación: {justificacion}")

                # Mostrar el tiempo que tomó procesar la noticia
                end_time = time.time()
                print(f"Tiempo de procesamiento para la noticia {idx + 1}: {end_time - start_time:.2f} segundos")

                # Guardar los cambios en la base de datos inmediatamente después de procesar la noticia
                conexion.commit()

    finally:
        conexion.close()


# --- EJECUCIÓN DEL PROGRAMA ---
if __name__ == "__main__":
    procesar_noticias()
