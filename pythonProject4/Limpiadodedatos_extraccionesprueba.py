import pymysql
import re


connection = pymysql.connect(
    host='localhost',
    user='root',
    password='Soccer.8a',
    database='noticias_prueba'
)

try:
    with connection.cursor() as cursor:

        select_query = "SELECT id, noticia FROM extracciones"
        cursor.execute(select_query)
        results = cursor.fetchall()


        regex_lee_tambien = re.compile(
            r'([Ll]ee también|[Ll]eer también|[Ll]ea también|[Ll]ee más|[Tt]ambién lee|[Tt]ambien lee).*?(\n|$)', re.IGNORECASE)


        regex_foto = re.compile(
            r'Foto:.*?(\n|$)', re.IGNORECASE)


        regex_dispositivo = re.compile(
            r',\s*desde tu dispositivo móvil entérate de las noticias más relevantes del día, artículos de opinión, entretenimiento, tendencias y más\..*?(\n|$)', re.IGNORECASE)


        regex_ultima_parte = re.compile(
            r'(\*?\s*El Grupo de Diarios América \(GDA\), al cual pertenece EL UNIVERSAL.*|'
            r'Ahora puedes recibir notificaciones de BBC Mundo.*|'
            r'Recuerda que puedes recibir notificaciones de BBC Mundo.*|'
            r'Suscríbete aquí.*|'
            r'Recibe todos los viernes Hello Weekend.*|'
            r'Recuerda que puedes recibir notificaciones de BBC News Mundo.*|'
            r'Únete a nuestro canal.*|'
            r'Ahora puedes recibir notificaciones de BBC News Mundo.*|'
            r'¿Ya conoces nuestro canal de YouTube\? ¡Suscríbete!.*|'
            r'para recibir directo en tu correo nuestras newsletters sobre noticias del día, opinión, (planes para el fin de semana, )?Qatar 2022 y muchas opciones más\..*)',
            re.IGNORECASE | re.DOTALL)

        ids_modificados = []

        for row in results:
            noticia_id = row[0]
            noticia_texto = row[1]


            if noticia_texto is not None:

                noticia_texto_limpia = re.sub(regex_lee_tambien, '', noticia_texto)


                noticia_texto_limpia = re.sub(regex_foto, '', noticia_texto_limpia)


                noticia_texto_limpia = re.sub(regex_dispositivo, '', noticia_texto_limpia)


                noticia_texto_limpia = re.sub(regex_ultima_parte, '', noticia_texto_limpia)


                if noticia_texto != noticia_texto_limpia:
                    ids_modificados.append(noticia_id)

                    update_query = "UPDATE extracciones SET noticia = %s WHERE id = %s"
                    cursor.execute(update_query, (noticia_texto_limpia, noticia_id))


        connection.commit()

finally:
    connection.close()

# Imprimir los ids de las noticias modificadas
print("Noticias modificadas con los siguientes IDs:")
print(ids_modificados)

