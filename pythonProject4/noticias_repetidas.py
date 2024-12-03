import mysql.connector
from mysql.connector import Error

def main():
    try:
        # Conexión a la base de datos
        connection = mysql.connector.connect(
            host='localhost',        # Reemplaza con tu host
            database='noticias',
            user='root',     # Reemplaza con tu usuario
            password='Soccer.8a'  # Reemplaza con tu contraseña
        )

        if connection.is_connected():
            print("Conexión exitosa a la base de datos")

            cursor = connection.cursor()

            # Verificar si el campo 'noticias_repetidas' existe; si no, añadirlo
            cursor.execute("""
                SHOW COLUMNS FROM extracciones LIKE 'noticias_repetidas';
            """)
            result = cursor.fetchone()
            if not result:
                cursor.execute("""
                    ALTER TABLE extracciones
                    ADD COLUMN noticias_repetidas TINYINT(1) DEFAULT 0;
                """)
                print("Campo 'noticias_repetidas' añadido a la tabla 'extracciones'.")

            # Obtener los datos necesarios de la tabla 'extracciones'
            cursor.execute("""
                SELECT 
                    id,
                    municipio,
                    estado,
                    pais,
                    mes_secuestro,
                    año_secuestro,
                    tipo_secuestro,
                    captor,
                    lugar,
                    captura
                FROM extracciones where relacion_spacy4 ='Sí';
            """)
            records = cursor.fetchall()

            # Crear una lista de diccionarios para facilitar el manejo
            columns = [desc[0] for desc in cursor.description]
            data = [dict(zip(columns, row)) for row in records]

            # Crear un diccionario para agrupar posibles duplicados
            potential_duplicates = {}
            for row in data:
                key = (
                    row['municipio'],
                    row['estado'],
                    row['pais'],
                    row['mes_secuestro'],
                    row['año_secuestro']
                )
                if key in potential_duplicates:
                    potential_duplicates[key].append(row)
                else:
                    potential_duplicates[key] = [row]

            # Identificar y marcar duplicados
            duplicates_to_mark = []
            for group in potential_duplicates.values():
                if len(group) > 1:
                    # Para cada grupo con los mismos campos clave
                    seen = {}
                    for entry in group:
                        # Crear una subclave con los campos adicionales
                        sub_key = (
                            entry['tipo_secuestro'],
                            entry['captor'],
                            entry['lugar'],
                            entry['captura']
                        )
                        if sub_key in seen:
                            # Si ya hemos visto esta combinación, es un duplicado
                            duplicates_to_mark.append(entry['id'])
                        else:
                            # Marcar esta combinación como vista
                            seen[sub_key] = entry['id']
            if duplicates_to_mark:
                # Marcar los duplicados en la base de datos
                format_strings = ','.join(['%s'] * len(duplicates_to_mark))
                cursor.execute(f"""
                    UPDATE extracciones
                    SET noticias_repetidas = 1
                    WHERE id IN ({format_strings});
                """, duplicates_to_mark)
                connection.commit()
                print(f"Noticias repetidas marcadas exitosamente. Total de noticias marcadas: {len(duplicates_to_mark)}")
            else:
                print("No se encontraron noticias repetidas para marcar.")

    except Error as e:
        print(f"Error: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("Conexión cerrada.")

if __name__ == '__main__':
    main()
