import pymysql
import spacy
import re
import unicodedata

# Cargar el modelo de spaCy para español
nlp = spacy.load('es_core_news_lg')

# --- FUNCIÓN PARA NORMALIZAR TEXTO ---
def normalizar_texto(texto):
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    return texto.lower()

# --- FUNCIÓN PARA CONECTARSE A LA BASE DE DATOS ---
def conectar_bd():
    conexion = pymysql.connect(
        host='localhost',
        user='root',
        password='Soccer.8a',  # Reemplaza con tu contraseña
        database='noticias_prueba',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    return conexion

# --- FUNCIÓN PARA VERIFICAR Y AGREGAR EL CAMPO 'tipo_secuestro' ---
def verificar_y_agregar_campo_tipo_secuestro():
    conexion = conectar_bd()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SHOW COLUMNS FROM extracciones LIKE 'tipo_secuestro'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE extracciones ADD COLUMN tipo_secuestro VARCHAR(255)")
                print("Campo 'tipo_secuestro' agregado.")
            conexion.commit()
    finally:
        conexion.close()

# --- FUNCIÓN PARA EXTRAER EL TIPO DE SECUESTRO ---
def extraer_tipo_secuestro(texto):
    doc = nlp(texto)
    tipos_secuestro_detectados = set()

    # Diccionario de tipos de secuestro y sus palabras clave asociadas
    tipos_secuestro = {
        'Secuestro político': [
            'secuestro político', 'secuestro ideológico', 'motivos políticos', 'razones políticas',
            'activista secuestrado', 'político secuestrado', 'candidato secuestrado', 'funcionario secuestrado',
            'alcalde', 'senador', 'diputado', 'gobernador', 'presidente', 'suplente', 'líder', 'activista',
            'político desaparecido', 'funcionario desaparecido'
        ],
        'Desaparición forzada': [
            'policías detuvieron', 'autoridades detuvieron', 'desaparecido por fuerzas de seguridad',
            'desaparición forzada', 'detenido desaparecido', 'desde entonces no se sabe', 'no se sabe nada de ellos',
            'detenidos y desaparecidos'
        ],
        'Secuestro por delincuencia organizada': [
            'cártel', 'cartel', 'grupo delictivo', 'delincuencia organizada', 'grupo criminal', 'banda',
            'grupos armados', 'grupos criminales', 'grupos delictivos', 'organización criminal'
        ],
        'Secuestro de migrantes': [
            'migrantes secuestrados', 'secuestro de migrantes', 'plagio de migrantes',
            'migrantes privados de su libertad', 'inmigrantes secuestrados', 'migrantes centroamericanos',
            'grupo de migrantes', 'migrantes desaparecidos'
        ],
        'Secuestro familiar': [
            'padre de', 'madre de', 'hijo de', 'familiar de', 'pariente de',
            'secuestro de familiar', 'familiar secuestrado'
        ],
        'Secuestro de menores': [
            'secuestro de menor', 'niño secuestrado', 'niña secuestrada', 'menor secuestrado',
            'adolescente secuestrado', 'secuestro infantil', 'plagio de menor', 'menor de edad'
        ],
        'Secuestro general': [
            'secuestro', 'privado de su libertad', 'plagio', 'rapto', 'desaparecido'
        ],
    }

    # Crear un set para almacenar las categorías identificadas
    categorias_identificadas = set()

    texto_normalizado = normalizar_texto(texto)

    for tipo, palabras_clave in tipos_secuestro.items():
        for palabra in palabras_clave:
            if palabra in texto_normalizado:
                # Regla especial para 'Secuestro familiar' y 'Secuestro político'
                if tipo == 'Secuestro familiar' and ('suplente' in texto_normalizado or 'senador' in texto_normalizado or 'diputado' in texto_normalizado or 'gobernador' in texto_normalizado or 'presidente' in texto_normalizado):
                    categorias_identificadas.add('Secuestro político')
                else:
                    categorias_identificadas.add(tipo)
                break  # Si encuentra una palabra clave, pasa al siguiente tipo

    # Si no se encontró ningún tipo específico, pero se menciona "secuestro", se asigna "Secuestro general"
    if not categorias_identificadas and 'secuestro' in texto_normalizado:
        categorias_identificadas.add('Secuestro general')

    return ', '.join(categorias_identificadas)

# --- FUNCIÓN PARA ACTUALIZAR EL TIPO DE SECUESTRO EN LA BASE DE DATOS ---
def actualizar_tipo_secuestro(id_noticia, tipo_secuestro):
    conexion = conectar_bd()
    try:
        with conexion.cursor() as cursor:
            sql = "UPDATE extracciones SET tipo_secuestro = %s WHERE id = %s"
            cursor.execute(sql, (tipo_secuestro, id_noticia))
            conexion.commit()
    finally:
        conexion.close()

# --- FUNCIÓN PARA OBTENER LAS NOTICIAS A PROCESAR ---
def obtener_noticias():
    conexion = conectar_bd()
    try:
        with conexion.cursor() as cursor:
            # Seleccionar solo las noticias donde relacion_spacy4 = 'Sí'
            sql = "SELECT id, noticia_corregida FROM extracciones WHERE relacion_spacy4 = 'Sí'"
            cursor.execute(sql)
            resultados = cursor.fetchall()
            return resultados
    finally:
        conexion.close()

# --- PROCESAR Y ANALIZAR NOTICIAS ---
def procesar_noticias():
    # Verificar y agregar el campo 'tipo_secuestro' si no existe
    verificar_y_agregar_campo_tipo_secuestro()

    # Obtener y procesar noticias
    noticias = obtener_noticias()
    for noticia in noticias:
        id_noticia = noticia['id']
        texto_noticia = noticia['noticia_corregida']

        # Extraer el tipo de secuestro
        tipo_secuestro = extraer_tipo_secuestro(texto_noticia)

        # Mostrar resultados del análisis
        print(f"\n--- Analizando noticia con ID: {id_noticia} ---")
        print(f"Tipo de secuestro detectado: {tipo_secuestro}")

        # Actualizar la base de datos con el tipo de secuestro
        actualizar_tipo_secuestro(id_noticia, tipo_secuestro)

# --- EJECUCIÓN DEL PROGRAMA ---
if __name__ == "__main__":
    procesar_noticias()
