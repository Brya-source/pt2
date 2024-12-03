import mysql.connector
import re

# Configuración de la conexión a la base de datos
db_config = {
    'user': 'root',
    'password': 'Soccer.8a',
    'host': '127.0.0.1',
    'database': 'noticias1'
}

# Frases a eliminar
frases_eliminar = [
    "artículos de opinión entretenimiento tendencias y más",
    "desde tu dispositivo móvil entérate de las noticias más relevantes del día",
    "artículos de opinión, entretenimiento, tendencias y más",
    "para el fin de semana, qatar 2022 y muchas opciones más",
    "para recibir directo en tu correo nuestras newsletters sobre noticias del día, opinión y",
    "para recibir directo en tu correo nuestras newsletters sobre noticias del día",
    "El Grupo de Diarios América (GDA), al cual pertenece EL UNIVERSAL, es una red de medios líderes fundada en 1991, que promueve los valores democráticos, la prensa independiente y la libertad de expresión en América Latina a través del periodismo de calidad para nuestras audiencias",
    "Recibe todos los viernes Hello Weekend, nuestro newsletter con lo último en gastronomía, viajes, tecnología, autos, moda y belleza. Suscríbete aquí: https://www.eluniversal.com.mx/newsletters",
    "Recuerda que puedes recibir notificaciones de BBC Mundo. Descarga la nueva versión de nuestra app y actívalas para no perderte nuestro mejor contenido.",
    "Descarga la nueva versión de nuestra app y actívalas para no perderte nuestro mejor contenido.",
    "Recuerda que puedes recibir notificaciones de BBC Mundo",
    "¿Ya conoces nuestro canal de YouTube? ¡Suscríbete!",
    "Recuerda que puedes recibir notificaciones de BBC News Mundo. Descarga la última versión de nuestra app y actívalas para no perderte nuestro mejor contenido",
    "Getty Images",
    "Únete a nuestro canal ¡EL UNIVERSAL ya está en Whatsapp!",
    "Publicidad"
]


# Función para limpiar texto de espacios adicionales y caracteres no visibles
def limpiar_texto(texto):
    # Reemplaza múltiples espacios por un solo espacio
    texto = re.sub(r'\s+', ' ', texto)
    # Elimina cualquier carácter no visible
    texto = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', texto)
    return texto.strip()


# Función para eliminar frases no deseadas usando expresiones regulares
def eliminar_frase(texto, frase):
    frase_limpia = limpiar_texto(frase)
    patron = re.compile(re.escape(frase_limpia), re.IGNORECASE)

    # Verificar si la frase se encuentra en el texto antes de eliminarla
    if patron.search(texto):
        print(f"Frase encontrada: '{frase}' en la noticia.")
        return patron.sub("", texto)
    return texto


# Conectar a la base de datos
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

# Consulta para seleccionar las noticias
cursor.execute("SELECT id, noticia FROM extracciones")
resultados = cursor.fetchall()

# Variable para contar cuántas noticias se modifican
contador_modificaciones = 0

# Recorrer los resultados y actualizar si se encuentra la frase
for id_noticia, noticia in resultados:
    noticia_limpia = limpiar_texto(noticia)  # Limpiar el texto antes de intentar eliminar frases

    noticia_original = noticia_limpia  # Guardar la noticia original para comparar después

    for frase in frases_eliminar:
        noticia_limpia = eliminar_frase(noticia_limpia, frase)

    if noticia_original != noticia_limpia:  # Solo actualizar si la noticia ha cambiado
        print(f"Actualizando noticia con ID: {id_noticia}")
        cursor.execute("UPDATE extracciones SET noticia = %s WHERE id = %s", (noticia_limpia, id_noticia))
        contador_modificaciones += 1

# Confirmar los cambios
conn.commit()

# Cerrar la conexión
cursor.close()
conn.close()

print(f"Frases eliminadas exitosamente de {contador_modificaciones} noticias.")

