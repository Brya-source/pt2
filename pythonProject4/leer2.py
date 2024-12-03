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
query_select = "SELECT id, noticia FROM extracciones WHERE noticia LIKE '%Lea también%'"
cursor.execute(query_select)
resultados = cursor.fetchall()

# Variable para contar cuántas noticias fueron modificadas
noticias_modificadas = 0

# Recorrer los resultados y buscar las palabras después de "Leer también"
for id_noticia, noticia in resultados:
    # Expresión regular para buscar "Leer también" y las siguientes 6 a 15 palabras
    patron = re.compile(r'Lea también\s+(?:\w+\s+){6,15}')
    noticia_modificada = re.sub(patron, '', noticia)

    # Si la noticia fue modificada, actualizarla en la base de datos
    if noticia_modificada != noticia:
        query_update = "UPDATE extracciones SET noticia = %s WHERE id = %s"
        cursor.execute(query_update, (noticia_modificada, id_noticia))
        conn.commit()
        noticias_modificadas += 1

# Cerrar la conexión
cursor.close()
conn.close()

print(f"Frases 'Lee también' eliminadas exitosamente de {noticias_modificadas} noticias.")
