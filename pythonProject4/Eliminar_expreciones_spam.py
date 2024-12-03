import pymysql
import re

conexion = pymysql.connect(
    host='localhost',
    user='root',
    password='Soccer.8a',
    database='noticias'
)

try:
    with conexion.cursor() as cursor:
        # Verificar si la columna 'noticia_corregida' ya existe
        cursor.execute("SHOW COLUMNS FROM extracciones LIKE 'noticia_corregida';")
        resultado = cursor.fetchone()

        # Si la columna no existe, la creamos
        if not resultado:
            cursor.execute("ALTER TABLE extracciones ADD COLUMN noticia_corregida TEXT;")

        # Selecciona los id y las noticias originales
        consulta_seleccion = "SELECT id, noticia FROM extracciones"
        cursor.execute(consulta_seleccion)
        resultados = cursor.fetchall()

        # Expresiones regulares para limpiar el texto
        exreg_lee_tambien = re.compile(
            r'([Ll]ee también|[Ll]eer también|[Ll]ea también|[Ll]ee más|[Tt]ambién lee|[Tt]ambien lee).*?(\n|$)',
            re.IGNORECASE)

        exreg_foto = re.compile(
            r'Foto:.*?(\n|$)', re.IGNORECASE)

        exreg_dispositivo = re.compile(
            r',\s*desde tu dispositivo móvil entérate de las noticias más relevantes del día, artículos de opinión, entretenimiento, tendencias y más\..*?(\n|$)',
            re.IGNORECASE)

        exreg_ultima_parte = re.compile(
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

        # Procesa cada fila
        for fila in resultados:
            id_noticia = fila[0]
            texto_noticia = fila[1]

            if texto_noticia is not None:

                # Aplica las correcciones al texto
                texto_noticia_limpio = re.sub(exreg_lee_tambien, '', texto_noticia)
                texto_noticia_limpio = re.sub(exreg_foto, '', texto_noticia_limpio)
                texto_noticia_limpio = re.sub(exreg_dispositivo, '', texto_noticia_limpio)
                texto_noticia_limpio = re.sub(exreg_ultima_parte, '', texto_noticia_limpio)

                # Si hay cambios o no, copia el resultado en 'noticia_corregida'
                if texto_noticia != texto_noticia_limpio:
                    ids_modificados.append(id_noticia)

                # Guardar el texto corregido o original en 'noticia_corregida'
                consulta_actualizacion = "UPDATE extracciones SET noticia_corregida = %s WHERE id = %s"
                cursor.execute(consulta_actualizacion, (texto_noticia_limpio, id_noticia))

        conexion.commit()

finally:
    conexion.close()

print("Noticias procesadas con los siguientes IDs:")
print(ids_modificados)
