import pymysql


# Conexión a la base de datos
def conectar_base_datos():
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='Soccer.8a',  # Cambia la contraseña según tu configuración
        database='noticias_prueba'  # Asegúrate de usar el nombre correcto de la base de datos
    )
    return connection


# Realizar la consulta en la base de datos
def obtener_noticias_secuestro(connection):
    consulta = """
        SELECT id, titulo, descripcion, url 
FROM extracciones 
WHERE (descripcion LIKE '%secuestro%' 
or descripcion LIKE '%secuestr%' 
or titulo LIKE '%secuestro%' 
or titulo LIKE '%secuestr%')
AND (noticia IS NOT NULL AND noticia != '');
    """

    with connection.cursor() as cursor:
        cursor.execute(consulta)
        resultados = cursor.fetchall()  # Obtener todos los resultados de la consulta
    return resultados


# Guardar los resultados en un archivo de texto
def guardar_en_bloc(resultados, archivo_salida):
    with open(archivo_salida, 'w', encoding='utf-8') as archivo:
        for resultado in resultados:
            titulo = resultado[1]
            descripcion = resultado[2]
            # Formato [ título -- descripción ]
            archivo.write(f"[ {titulo} -- {descripcion} ]\n")


# Programa principal
def main():
    # Conectar a la base de datos
    connection = conectar_base_datos()

    try:
        # Obtener noticias relacionadas con secuestros
        noticias = obtener_noticias_secuestro(connection)

        # Guardar los resultados en un archivo de texto
        archivo_salida = "noticias_secuestro.txt"  # Nombre del archivo
        guardar_en_bloc(noticias, archivo_salida)

        print(f"Noticias guardadas correctamente en {archivo_salida}")

    finally:
        connection.close()  # Cerrar la conexión a la base de datos


if __name__ == '__main__':
    main()
