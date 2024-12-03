import pandas as pd
import mysql.connector

# Configuración de la conexión a la base de datos
db_config = {
    'user': 'root',
    'password': 'Soccer.8a',
    'host': '127.0.0.1',
    'database': 'noticias_respaldo'
}

# Cargar datos
conn = mysql.connector.connect(**db_config)
query = "SELECT id, noticia FROM extracciones WHERE noticia LIKE '%Únete a nuestro canal%' OR noticia LIKE '%desde tu dispositivo móvil%'"
df = pd.read_sql(query, conn)

conn.close()

print(df)
