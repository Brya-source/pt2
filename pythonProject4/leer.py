import mysql.connector
import re

# Configuración de la conexión a la base de datos
db_config = {
    'user': 'root',
    'password': 'Soccer.8a',
    'host': '127.0.0.1',
    'database': 'noticias_respaldo'
}

# Conectar a la base de datos
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

# Consulta para seleccionar las noticias que contienen la frase "Leer también"
query = "SELECT id, noticia FROM extracciones WHERE noticia LIKE '%Leer también%'"
cursor.execute(query)
resultados = cursor.fetchall()

# Variable para almacenar las noticias que contienen la frase y sus palabras siguientes
frases_extraidas = []

# Recorrer los resultados y buscar las palabras después de "Leer también"
for id_noticia, noticia in resultados:
    # Buscar todas las ocurrencias de "Leer también" y las palabras siguientes
    patron = re.compile(r'Leer también\s+((?:\w+\s+){3,35})')
    coincidencias = patron.findall(noticia)

    for coincidencia in coincidencias:
        frases_extraidas.append((id_noticia, coincidencia.strip()))

# Cerrar la conexión
cursor.close()
conn.close()

# Mostrar las frases extraídas
print("Frases extraídas después de 'Leer también':")
for id_noticia, frase in frases_extraidas:
    print(f"ID Noticia: {id_noticia} - Frase: {frase}")
