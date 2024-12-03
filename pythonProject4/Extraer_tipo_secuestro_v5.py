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
        database='noticias',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    return conexion

# --- FUNCIÓN PARA VERIFICAR Y AGREGAR EL CAMPO 'tipo_secuestro' ---
def verificar_y_agregar_campos():
    conexion = conectar_bd()
    try:
        with conexion.cursor() as cursor:
            # Verificar y agregar el campo 'tipo_secuestro'
            cursor.execute("SHOW COLUMNS FROM extracciones LIKE 'tipo_secuestro'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE extracciones ADD COLUMN tipo_secuestro VARCHAR(255)")
                print("Campo 'tipo_secuestro' agregado.")

            conexion.commit()
    finally:
        conexion.close()

# --- FUNCIÓN PARA EXTRAER EL TIPO DE SECUESTRO CON ANÁLISIS CONTEXTUAL ---
def extraer_tipo_secuestro(texto):
    doc = nlp(texto)
    categorias_identificadas = set()
    justificaciones = []

    # Listas de palabras clave y patrones para diferentes tipos de secuestro
    patrones = {
        'Secuestro exprés': {
            'frases_directas': ['secuestro exprés', 'secuestro express', 'secuestro rápido', 'plagio exprés'],
            'indicadores': ['corto tiempo', 'rápido', 'obtener beneficio', 'secuestro breve']
        },
        'Secuestro virtual': {
            'frases_directas': ['secuestro virtual', 'extorsión telefónica', 'secuestro simulado', 'secuestro falso'],
            'indicadores': ['contactar a un pariente', 'pagar un rescate', 'secuestro no se cristaliza', 'extorsión']
        },
        'Secuestro extorsivo': {
            'indicadores': [
                'exigieron rescate', 'exigieron dinero', 'exigió pago', 'demandaron rescate',
                'pidieron rescate', 'exigencia económica', 'exigió dinero', 'pedir una suma monetaria',
                'pedir un beneficio', 'empresario', 'comerciante', 'banquero', 'industrial', 'empresaria',
                'secuestrado', 'plagiado', 'privado de su libertad'
            ],
        },
        'Secuestro político': {
            'roles': [
                'alcalde', 'senador', 'diputado', 'gobernador', 'presidente', 'suplente',
                'ministro', 'regidor', 'funcionario', 'político', 'activista', 'candidato'
            ],
            'indicadores': [
                'crear un entorno inseguro', 'conseguir publicidad', 'gran influencia en las decisiones',
                'decisiones del estado', 'decisiones de otras entidades'
            ],
        },
        'Secuestro por delincuencia organizada': {
            'grupos_criminales': [
                'cártel', 'cartel', 'banda', 'grupo delictivo', 'grupo criminal',
                'delincuencia organizada', 'grupos armados', 'criminales'
            ],
            'acciones': ['secuestró', 'secuestraron', 'plagiaron', 'privaron de la libertad'],
        },
        'Secuestro de migrantes': {
            'victimas': [
                'migrantes', 'inmigrantes', 'centroamericanos', 'migrantes mexicanos', 'migrantes extranjeros'
            ],
            'acciones': ['secuestrados', 'plagiados', 'privados de su libertad'],
        },
        'Secuestro familiar': {
            'relaciones_familiares': [
                'padre', 'madre', 'hijo', 'hija', 'hermano', 'hermana', 'esposo', 'esposa',
                'tío', 'tía', 'abuelo', 'abuela', 'sobrino', 'sobrina', 'primo', 'prima',
                'familiar', 'pariente'
            ],
            'verbos_relacionados': ['secuestrar', 'privar', 'raptar', 'plagiar'],
        },
        'Secuestro de menores': {
            'victimas': [
                'niño', 'niña', 'menor', 'adolescente', 'bebé', 'infante'
            ],
            'verbos_relacionados': ['secuestro', 'secuestrar', 'plagiar', 'raptar', 'privar'],
        },
        'Secuestro simulado': {
            'indicadores': [
                'víctima planeó el secuestro', 'auto-secuestro', 'secuestro falso',
                'simular secuestro', 'secuestro simulado', 'secuestro fingido',
                'la víctima planea el secuestro'
            ],
        },
        'Secuestro con fines de explotación sexual': {
            'indicadores': [
                'dañar su integridad sexual', 'explotación sexual', 'abuso sexual',
                'trata de personas', 'violación', 'prostitución forzada', 'esclavitud sexual'
            ],
            'verbos_relacionados': ['secuestro', 'secuestrar', 'privar', 'plagiar', 'raptar'],
        },
    }

    texto_normalizado = normalizar_texto(texto)

    # Detección de tipos de secuestro mencionados directamente
    for tipo, detalles in patrones.items():
        if 'frases_directas' in detalles:
            for frase in detalles['frases_directas']:
                if frase in texto_normalizado:
                    categorias_identificadas.add(tipo)
                    justificaciones.append(f"Detectada frase directa '{frase}' para '{tipo}'.")
                    return tipo, '; '.join(justificaciones)  # Solo asignamos el primer tipo encontrado

    # Análisis de oraciones
    for sent in doc.sents:
        sent_text = sent.text.lower()
        sent_doc = nlp(sent.text)

        # Si ya se detectó un tipo de secuestro, dejamos de analizar
        if categorias_identificadas:
            break

        # Secuestro con fines de explotación sexual
        if 'Secuestro con fines de explotación sexual' not in categorias_identificadas:
            if any(indicador in sent_text for indicador in patrones['Secuestro con fines de explotación sexual']['indicadores']):
                categorias_identificadas.add('Secuestro con fines de explotación sexual')
                justificaciones.append(f"Detectado indicador de explotación sexual en: '{sent.text.strip()}'.")
                return 'Secuestro con fines de explotación sexual', '; '.join(justificaciones)

        # Secuestro simulado
        if 'Secuestro simulado' not in categorias_identificadas:
            if any(indicador in sent_text for indicador in patrones['Secuestro simulado']['indicadores']):
                categorias_identificadas.add('Secuestro simulado')
                justificaciones.append(f"Detectado indicador de secuestro simulado en: '{sent.text.strip()}'.")
                return 'Secuestro simulado', '; '.join(justificaciones)

        # Secuestro de menores
        if 'Secuestro de menores' not in categorias_identificadas:
            for token in sent_doc:
                if token.lemma_ in patrones['Secuestro de menores']['verbos_relacionados'] and token.pos_ == 'VERB':
                    objeto = None
                    # Obtener el objeto directo del verbo
                    for child in token.children:
                        if child.dep_ in ('dobj', 'obj'):
                            objeto = child
                            break
                    if objeto:
                        objeto_text = objeto.text.lower()
                        # Verificar si el objeto es un menor
                        if any(victima in objeto_text for victima in patrones['Secuestro de menores']['victimas']):
                            categorias_identificadas.add('Secuestro de menores')
                            justificaciones.append(f"Detectado menor como víctima en: '{sent.text.strip()}'.")
                            return 'Secuestro de menores', '; '.join(justificaciones)

        # Secuestro político
        if 'Secuestro político' not in categorias_identificadas:
            for ent in sent_doc.ents:
                if ent.label_ == 'PER' and any(role in ent.text.lower() for role in patrones['Secuestro político']['roles']):
                    if any(verb.lemma_ in ['secuestro', 'privar', 'plagiar', 'raptar'] for verb in sent_doc if verb.pos_ == 'VERB'):
                        categorias_identificadas.add('Secuestro político')
                        justificaciones.append(f"Detectado verbo de secuestro relacionado con persona política '{ent.text}'.")
                        return 'Secuestro político', '; '.join(justificaciones)
            if any(indicador in sent_text for indicador in patrones['Secuestro político'].get('indicadores', [])):
                categorias_identificadas.add('Secuestro político')
                justificaciones.append(f"Detectado indicador político en: '{sent.text.strip()}'.")
                return 'Secuestro político', '; '.join(justificaciones)

        # Secuestro por delincuencia organizada
        if 'Secuestro por delincuencia organizada' not in categorias_identificadas:
            if any(grupo in sent_text for grupo in patrones['Secuestro por delincuencia organizada']['grupos_criminales']) and any(action in sent_text for action in patrones['Secuestro por delincuencia organizada']['acciones']):
                categorias_identificadas.add('Secuestro por delincuencia organizada')
                justificaciones.append(f"Detectado grupo criminal y acción de secuestro en: '{sent.text.strip()}'.")
                return 'Secuestro por delincuencia organizada', '; '.join(justificaciones)

        # Secuestro extorsivo (combinado)
        if 'Secuestro extorsivo' not in categorias_identificadas:
            if any(indicador in sent_text for indicador in patrones['Secuestro extorsivo']['indicadores']):
                categorias_identificadas.add('Secuestro extorsivo')
                justificaciones.append(f"Detectado indicador de secuestro extorsivo en: '{sent.text.strip()}'.")
                return 'Secuestro extorsivo', '; '.join(justificaciones)

        # Secuestro familiar
        if 'Secuestro familiar' not in categorias_identificadas:
            for token in sent_doc:
                if token.lemma_ in patrones['Secuestro familiar']['verbos_relacionados'] and token.pos_ == 'VERB':
                    sujeto = None
                    objeto = None
                    # Obtener el sujeto y el objeto del verbo
                    for child in token.children:
                        if child.dep_ in ('nsubj', 'nsubj:pass'):
                            sujeto = child
                        elif child.dep_ in ('dobj', 'obj'):
                            objeto = child
                    if sujeto and any(rel in sujeto.text.lower() for rel in patrones['Secuestro familiar']['relaciones_familiares']):
                        categorias_identificadas.add('Secuestro familiar')
                        justificaciones.append(f"Detectado familiar '{sujeto.text}' como perpetrador en: '{sent.text.strip()}'.")
                        return 'Secuestro familiar', '; '.join(justificaciones)
                    # En caso de voz pasiva, buscar el agente
                    for child in token.children:
                        if child.dep_ == 'agent':
                            agente = child.text.lower()
                            if any(rel in agente for rel in patrones['Secuestro familiar']['relaciones_familiares']):
                                categorias_identificadas.add('Secuestro familiar')
                                justificaciones.append(f"Detectado familiar '{child.text}' como perpetrador en voz pasiva en: '{sent.text.strip()}'.")
                                return 'Secuestro familiar', '; '.join(justificaciones)

    # Si no se encontró ningún tipo específico, pero se menciona alguna conjugación de los verbos relacionados, se asigna "Secuestro general"
    if not categorias_identificadas:
        verbos_secuestro = {'secuestro', 'secuestrar', 'privar', 'plagiar', 'raptar', 'plagio', 'rapto', 'privado', 'privada'}
        lemmas_en_texto = [token.lemma_.lower() for token in doc]
        if any(lemma in verbos_secuestro for lemma in lemmas_en_texto):
            categorias_identificadas.add('Secuestro general')
            justificaciones.append("No se detectó un tipo específico, pero se mencionó 'secuestro' o 'privar' en alguna de sus formas.")
        else:
            justificaciones.append("No se detectó 'secuestro' o 'privar' en el texto.")

    # Retornar el primer tipo de secuestro identificado o 'Secuestro general' si no se encontró ninguno específico
    tipo_secuestro = next(iter(categorias_identificadas)) if categorias_identificadas else ''
    return tipo_secuestro, '; '.join(justificaciones)

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
    # Verificar y agregar los campos si no existen
    verificar_y_agregar_campos()

    # Obtener y procesar noticias
    noticias = obtener_noticias()
    for noticia in noticias:
        id_noticia = noticia['id']
        texto_noticia = noticia['noticia_corregida']

        # Extraer el tipo de secuestro y la justificación
        tipo_secuestro, justificacion = extraer_tipo_secuestro(texto_noticia)

        # Mostrar resultados del análisis
        print(f"\n--- Analizando noticia con ID: {id_noticia} ---")
        print(f"Tipo de secuestro detectado: {tipo_secuestro}")
        print(f"Justificación: {justificacion}")

        # Actualizar la base de datos con el tipo de secuestro
        actualizar_tipo_secuestro(id_noticia, tipo_secuestro)

# --- EJECUCIÓN DEL PROGRAMA ---
if __name__ == "__main__":
    procesar_noticias()

