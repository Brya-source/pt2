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

# --- FUNCIÓN PARA VERIFICAR Y AGREGAR LOS CAMPOS 'tipo_secuestro' Y 'justificacion_tipo_secuestro' ---
def verificar_y_agregar_campos():
    conexion = conectar_bd()
    try:
        with conexion.cursor() as cursor:
            # Verificar y agregar el campo 'tipo_secuestro'
            cursor.execute("SHOW COLUMNS FROM extracciones LIKE 'tipo_secuestro'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE extracciones ADD COLUMN tipo_secuestro VARCHAR(255)")
                print("Campo 'tipo_secuestro' agregado.")

            # Verificar y agregar el campo 'justificacion_tipo_secuestro'
            cursor.execute("SHOW COLUMNS FROM extracciones LIKE 'justificacion_tipo_secuestro'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE extracciones ADD COLUMN justificacion_tipo_secuestro TEXT")
                print("Campo 'justificacion_tipo_secuestro' agregado.")

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
            'acciones': ['secuestrar', 'privar', 'plagiar', 'raptar'],
        },
        'Secuestro virtual': {
            'frases_directas': ['secuestro virtual', 'extorsión telefónica', 'secuestro simulado', 'secuestro falso'],
        },
        'Secuestro con fines de extorsión': {
            'indicadores': ['exigieron rescate', 'exigieron dinero', 'exigió pago', 'demandaron rescate', 'pidieron rescate', 'exigencia económica', 'exigió dinero'],
        },
        'Secuestro económico': {
            'victimas': ['empresario', 'comerciante', 'banquero', 'industrial', 'empresaria'],
            'acciones': ['secuestrado', 'plagiado', 'privado de su libertad'],
        },
        'Secuestro político': {
            'roles': ['alcalde', 'senador', 'diputado', 'gobernador', 'presidente', 'suplente', 'ministro', 'regidor', 'funcionario', 'político', 'activista', 'candidato'],
        },
        'Desaparición forzada': {
            'agentes': ['policía', 'autoridad', 'militar', 'fuerzas de seguridad', 'agentes'],
            'acciones': ['detuvieron', 'detenido', 'arrestaron', 'arrestado'],
            'indicadores': ['desde entonces no se sabe', 'no se sabe nada de'],
        },
        'Secuestro por delincuencia organizada': {
            'grupos_criminales': ['cártel', 'cartel', 'banda', 'grupo delictivo', 'grupo criminal', 'delincuencia organizada', 'grupos armados', 'criminales'],
            'acciones': ['secuestró', 'secuestraron', 'plagiaron', 'privaron de la libertad'],
        },
        'Secuestro de migrantes': {
            'victimas': ['migrantes', 'inmigrantes', 'centroamericanos', 'migrantes mexicanos', 'migrantes extranjeros'],
            'acciones': ['secuestrados', 'plagiados', 'privados de su libertad'],
        },
        'Secuestro familiar': {
            'relaciones_familiares': ['padre', 'madre', 'hijo', 'hija', 'hermano', 'hermana', 'esposo', 'esposa', 'tío', 'tía', 'abuelo', 'abuela', 'sobrino', 'sobrina', 'primo', 'prima', 'familiar', 'pariente'],
            'verbos_relacionados': ['secuestrar', 'privar', 'raptar', 'plagiar'],
        },
        'Secuestro de menores': {
            'victimas': ['niño', 'niña', 'menor', 'adolescente', 'bebé', 'infante'],
            'acciones': ['secuestrado', 'plagiado', 'raptado'],
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
                    break  # Evita duplicados

    # Análisis de oraciones
    for sent in doc.sents:
        sent_text = sent.text.lower()
        sent_doc = nlp(sent.text)

        # Si ya se detectó el tipo por frase directa, podemos omitir análisis adicionales para ese tipo
        tipos_analizar = set(patrones.keys()) - categorias_identificadas

        # Secuestro político
        if 'Secuestro político' in tipos_analizar:
            for ent in sent_doc.ents:
                if ent.label_ == 'PER' and any(role in ent.text.lower() for role in patrones['Secuestro político']['roles']):
                    if any(verb.lemma_ in ['secuestro', 'privar', 'plagiar', 'raptar'] for verb in sent_doc if verb.pos_ == 'VERB'):
                        categorias_identificadas.add('Secuestro político')
                        justificaciones.append(f"Detectado verbo de secuestro relacionado con persona política '{ent.text}'.")
                        break

        # Desaparición forzada
        if 'Desaparición forzada' in tipos_analizar:
            if any(agent in sent_text for agent in patrones['Desaparición forzada']['agentes']) and any(action in sent_text for action in patrones['Desaparición forzada']['acciones']):
                categorias_identificadas.add('Desaparición forzada')
                justificaciones.append(f"Detectado agente de autoridad y acción de detención en: '{sent.text.strip()}'.")
            elif any(indicador in sent_text for indicador in patrones['Desaparición forzada']['indicadores']):
                categorias_identificadas.add('Desaparición forzada')
                justificaciones.append(f"Detectado indicador de desaparición forzada en: '{sent.text.strip()}'.")

        # Secuestro por delincuencia organizada
        if 'Secuestro por delincuencia organizada' in tipos_analizar:
            if any(grupo in sent_text for grupo in patrones['Secuestro por delincuencia organizada']['grupos_criminales']) and any(action in sent_text for action in patrones['Secuestro por delincuencia organizada']['acciones']):
                categorias_identificadas.add('Secuestro por delincuencia organizada')
                justificaciones.append(f"Detectado grupo criminal y acción de secuestro en: '{sent.text.strip()}'.")

        # Secuestro de migrantes
        if 'Secuestro de migrantes' in tipos_analizar:
            if any(victima in sent_text for victima in patrones['Secuestro de migrantes']['victimas']) and any(action in sent_text for action in patrones['Secuestro de migrantes']['acciones']):
                categorias_identificadas.add('Secuestro de migrantes')
                justificaciones.append(f"Detectado migrantes y acción de secuestro en: '{sent.text.strip()}'.")

        # Secuestro familiar
        if 'Secuestro familiar' in tipos_analizar:
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
                    # Si encontramos sujeto y objeto
                    if sujeto and objeto:
                        # Verificar si el sujeto es un familiar
                        if any(rel in sujeto.text.lower() for rel in patrones['Secuestro familiar']['relaciones_familiares']):
                            categorias_identificadas.add('Secuestro familiar')
                            justificaciones.append(f"Detectado familiar '{sujeto.text}' como perpetrador en: '{sent.text.strip()}'.")
                            break
                    # En caso de voz pasiva, buscar el agente
                    for child in token.children:
                        if child.dep_ == 'agent':
                            agente = child.text.lower()
                            if any(rel in agente for rel in patrones['Secuestro familiar']['relaciones_familiares']):
                                categorias_identificadas.add('Secuestro familiar')
                                justificaciones.append(f"Detectado familiar '{child.text}' como perpetrador en voz pasiva en: '{sent.text.strip()}'.")
                                break

        # Secuestro de menores
        if 'Secuestro de menores' in tipos_analizar:
            if any(victima in sent_text for victima in patrones['Secuestro de menores']['victimas']) and any(action in sent_text for action in patrones['Secuestro de menores']['acciones']):
                categorias_identificadas.add('Secuestro de menores')
                justificaciones.append(f"Detectado menor y acción de secuestro en: '{sent.text.strip()}'.")

        # Secuestro económico
        if 'Secuestro económico' in tipos_analizar:
            if any(victima in sent_text for victima in patrones['Secuestro económico']['victimas']) and any(action in sent_text for action in patrones['Secuestro económico']['acciones']):
                categorias_identificadas.add('Secuestro económico')
                justificaciones.append(f"Detectado secuestro económico en: '{sent.text.strip()}'.")

        # Secuestro con fines de extorsión
        if 'Secuestro con fines de extorsión' in tipos_analizar:
            if any(indicador in sent_text for indicador in patrones['Secuestro con fines de extorsión']['indicadores']):
                categorias_identificadas.add('Secuestro con fines de extorsión')
                justificaciones.append(f"Detectado indicador de extorsión en: '{sent.text.strip()}'.")

    # Si no se encontró ningún tipo específico, pero se menciona "secuestro", se asigna "Secuestro general"
    if not categorias_identificadas and 'secuestro' in texto_normalizado:
        categorias_identificadas.add('Secuestro general')
        justificaciones.append("No se detectó un tipo específico, pero se mencionó 'secuestro'.")

    return ', '.join(categorias_identificadas), '; '.join(justificaciones)

# --- FUNCIÓN PARA ACTUALIZAR EL TIPO DE SECUESTRO EN LA BASE DE DATOS ---
def actualizar_tipo_secuestro(id_noticia, tipo_secuestro, justificacion):
    conexion = conectar_bd()
    try:
        with conexion.cursor() as cursor:
            sql = "UPDATE extracciones SET tipo_secuestro = %s, justificacion_tipo_secuestro = %s WHERE id = %s"
            cursor.execute(sql, (tipo_secuestro, justificacion, id_noticia))
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

        # Actualizar la base de datos con el tipo de secuestro y la justificación
        actualizar_tipo_secuestro(id_noticia, tipo_secuestro, justificacion)

# --- EJECUCIÓN DEL PROGRAMA ---
if __name__ == "__main__":
    procesar_noticias()
