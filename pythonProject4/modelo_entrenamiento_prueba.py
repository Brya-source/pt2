import pymysql
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, classification_report
import spacy
from spacy.training.example import Example

# Cargar el modelo de lenguaje en español
nlp = spacy.blank('es')
ner = nlp.add_pipe('ner')

# Definir etiquetas adicionales
labels = [
    'FECHA_SECUESTRO', 'LUGAR', 'TIPO_SECUESTRO', 'RESCATE',
    'NACIONALIDAD', 'USO_FUERZA', 'NUM_SECUESTRADORES', 'DETENCION',
    'MOD_OPERACION', 'LUGAR_EXACTO', 'RELACION_VICTIMA', 'TIEMPO_CAUTIVERIO',
    'DEMANDA_RES', 'ESTADO_VICTIMA', 'MOTIVO_SECUESTRO', 'MEDIADOR'
]
for label in labels:
    ner.add_label(label)

# Inicializar el pipeline antes de usarlo
nlp.initialize()

# Lista de palabras clave para filtrar noticias
palabras_clave = [
    'secuestro', 'secuestrado', 'secuestradores', 'rescatar', 'cautiverio',
    'liberación', 'rehén', 'rescate', 'víctima', 'detención'
]

# Filtrar noticias que no están relacionadas con secuestros
def contiene_palabra_clave(texto):
    texto_lower = texto.lower()
    for palabra in palabras_clave:
        if palabra in texto_lower:
            return True
    return False

# Función para preprocesar texto
def preprocess_text(text):
    doc = nlp(text)
    tokens = [token.lemma_ for token in doc if not token.is_stop and not token.is_punct]
    return ' '.join(tokens)

# Cargar datos de la base de datos
def load_data():
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='Soccer.8a',
        database='noticias_prueba'
    )
    query = "SELECT id, titulo, descripcion, noticia FROM extracciones"
    df = pd.read_sql(query, connection)
    return df

# Filtrar las noticias relacionadas con secuestros (título y descripción)
def filtrar_noticias(df):
    df_filtrado = df.loc[
        df.apply(lambda x: contiene_palabra_clave(x['titulo']) or contiene_palabra_clave(x['descripcion']), axis=1)
    ]
    return df_filtrado

# Entrenar un modelo de clasificación para verificar si la noticia está relacionada con secuestros

# Predecir si una noticia está relacionada con secuestros usando el clasificador
# Entrenar un modelo de clasificación para verificar si la noticia está relacionada con secuestros
def entrenar_clasificador(df):
    # Preparamos los datos
    df = df.copy()  # Asegurarse de trabajar sobre una copia del DataFrame
    df['texto_completo'] = df['titulo'] + ' ' + df['descripcion']

    # Etiquetas manuales (1 para secuestros, 0 para otros)
    df['es_secuestro'] = df.apply(
        lambda x: 1 if contiene_palabra_clave(x['titulo']) or contiene_palabra_clave(x['descripcion']) else 0, axis=1)

    # Dividir los datos en entrenamiento y prueba
    X_train, X_test, y_train, y_test = train_test_split(df['texto_completo'], df['es_secuestro'], test_size=0.3,
                                                        random_state=42)

    # Vectorización TF-IDF para convertir texto en datos numéricos
    vectorizer = TfidfVectorizer()
    X_train_tfidf = vectorizer.fit_transform(X_train)
    X_test_tfidf = vectorizer.transform(X_test)

    # Entrenar un clasificador Naive Bayes
    clf = MultinomialNB()
    clf.fit(X_train_tfidf, y_train)

    # Evaluar el modelo
    y_pred = clf.predict(X_test_tfidf)
    print("Accuracy:", accuracy_score(y_test, y_pred))
    print(classification_report(y_test, y_pred))

    return clf, vectorizer

# Predecir si una noticia está relacionada con secuestros usando el clasificador
def predecir_secuestros(clf, vectorizer, df):
    df = df.copy()  # Asegurarse de trabajar sobre una copia del DataFrame
    df['texto_completo'] = df['titulo'] + ' ' + df['descripcion']
    X_tfidf = vectorizer.transform(df['texto_completo'])
    df.loc[:, 'prediccion_secuestro'] = clf.predict(X_tfidf)  # Usar .loc[] para evitar SettingWithCopyWarning
    df_filtrado = df.loc[df['prediccion_secuestro'] == 1]  # Solo seleccionamos noticias relacionadas con secuestros
    return df_filtrado


# Función para entrenar el modelo NER
def train_ner_model(nlp, train_data):
    optimizer = nlp.begin_training()

    # Entrenar el modelo de NER
    for itn in range(10):  # Número de iteraciones
        losses = {}
        for text, annotations in train_data:
            doc = nlp.make_doc(text)
            example = Example.from_dict(doc, annotations)
            nlp.update([example], drop=0.5, losses=losses, sgd=optimizer)
        print(f"Iteración {itn} - Pérdidas: {losses}")

# Extraer entidades con el modelo entrenado
def extract_entities(nlp_secuestrador, df):
    results = []
    for i, row in df.iterrows():
        doc = nlp_secuestrador(row['noticia_preprocesada'])
        entities = {}
        for ent in doc.ents:
            entities[ent.label_] = ent.text
        results.append((row['id'], entities))
    return results

# Guardar los resultados en la base de datos
def save_results(connection, results):
    cursor = connection.cursor()
    for result in results:
        id_noticia, data = result
        # Extraer las entidades relevantes
        fecha_secuestro = data.get('FECHA_SECUESTRO', None)
        lugar = data.get('LUGAR', None)
        tipo_secuestro = data.get('TIPO_SECUESTRO', None)
        rescate = data.get('RESCATE', None)
        nacionalidad = data.get('NACIONALIDAD', None)
        uso_fuerza = data.get('USO_FUERZA', None)
        num_secuestradores = data.get('NUM_SECUESTRADORES', None)
        detencion = data.get('DETENCION', None)
        mod_operacion = data.get('MOD_OPERACION', None)
        lugar_exacto = data.get('LUGAR_EXACTO', None)
        relacion_victima = data.get('RELACION_VICTIMA', None)
        tiempo_cautiverio = data.get('TIEMPO_CAUTIVERIO', None)
        demanda_res = data.get('DEMANDA_RES', None)
        estado_victima = data.get('ESTADO_VICTIMA', None)
        motivo_secuestro = data.get('MOTIVO_SECUESTRO', None)
        mediador = data.get('MEDIADOR', None)

        # Guardar los resultados en la base de datos
        query = """UPDATE extracciones 
                   SET fecha_secuestro = %s, lugar = %s, tipo_secuestro = %s, rescate = %s,
                       nacionalidad = %s, uso_fuerza = %s, num_secuestradores = %s, detencion = %s,
                       mod_operacion = %s, lugar_exacto = %s, relacion_victima = %s, tiempo_cautiverio = %s,
                       demanda_res = %s, estado_victima = %s, motivo_secuestro = %s, mediador = %s
                   WHERE id = %s"""
        cursor.execute(query, (fecha_secuestro, lugar, tipo_secuestro, rescate,
                               nacionalidad, uso_fuerza, num_secuestradores, detencion,
                               mod_operacion, lugar_exacto, relacion_victima, tiempo_cautiverio,
                               demanda_res, estado_victima, motivo_secuestro, mediador, id_noticia))
    connection.commit()

# Ejecución del pipeline completo
def main():
    # Paso 1: Cargar los datos
    df = load_data()

    # Paso 2: Filtrar las noticias que no estén relacionadas con secuestros
    df_filtrado_palabras_clave = filtrar_noticias(df)

    # Paso 3: Entrenar el clasificador supervisado para mejorar el filtrado
    clf, vectorizer = entrenar_clasificador(df)

    # Paso 4: Predecir noticias relacionadas con secuestros usando el clasificador
    df_filtrado_clasificador = predecir_secuestros(clf, vectorizer, df_filtrado_palabras_clave)

    # Paso 5: Preprocesar los textos filtrados
    df_filtrado_clasificador['noticia_preprocesada'] = df_filtrado_clasificador['noticia'].apply(preprocess_text)

    # Paso 6: Definir los ejemplos anotados manualmente
    train_data = [
        ('El 15 de marzo de 2023, un secuestro exprés ocurrió en Ciudad de México.',
         {'entities': [(3, 17, 'FECHA_SECUESTRO'), (45, 64, 'LUGAR'), (28, 42, 'TIPO_SECUESTRO')]}),
        ('Seis hombres armados secuestraron a una víctima en Guadalajara. La víctima fue rescatada ilesa.',
         {'entities': [(0, 4, 'NUM_SECUESTRADORES'), (5, 19, 'USO_FUERZA'), (20, 31, 'TIPO_SECUESTRO'),
                       (51, 61, 'LUGAR'), (67, 75, 'RESCATE'), (76, 81, 'ESTADO_VICTIMA')]}),
        (
            "Es un secuestro que tiene en alerta a las autoridades de México y Estados Unidos. El pasado 3 de marzo cuatro personas fueron atacadas y secuestradas en el noreste mexicano mientras viajaban por Matamoros, una ciudad del estado de Tamaulipas. La localidad está ubicada directamente al otro lado de la frontera con Brownsville, Texas. Los secuestrados no han sido identificadas, pero los gobiernos de ambos países aseguran que son ciudadanos estadounidenses y que fueron atacados antes de ser privados de su libertad. Personal de ambas naciones norteamericanas participan de las pesquisas. A continuación te contamos qué se sabe sobre este caso. El secuestro De acuerdo con las autoridades, las víctimas conducían una furgoneta blanca con placa de Carolina del Norte cuando un grupo de hombres armados no identificados les disparó. Luego los metieron en otro vehículo y se los llevaron. Estados Unidos no ha confirmado la declaración del presidente mexicano, Andrés Manuel López Obrador, de que los estadounidenses cruzaron la frontera para comprar medicamentos. 'Hubo un enfrentamiento entre grupos y fueron secuestrados', dijo López Obrador el lunes. Un funcionario mexicano le dijo a la agencia de noticias Reuters que los secuestrados eran tres hombres y una mujer. En el incidente murió un ciudadano mexicano, dijo el embajador de Estados Unidos en México, Ken Salazar, en un comunicado. 'No tenemos mayor prioridad que la seguridad de nuestros ciudadanos', sostuvo el embajador. 'Funcionarios de diversas fuerzas del orden de Estados Unidos están trabajando con las autoridades mexicanas en todos los niveles de gobierno para lograr el regreso seguro de nuestros compatriotas', continuó. Por su parte, el FBI informó que colabora con la pesquisa. Esta agencia busca la ayuda del público y ofrece una recompensa de $50.000 por información que conduzca a la liberación de las víctimas y el arresto de los involucrados.",
            {
                "entities": [
                    (83, 93, "FECHA"),  # "3 de marzo"
                    (122, 132, "NUM_SECUESTRADOS"),  # "cuatro personas"
                    (177, 187, "LUGAR"),  # "Matamoros"
                    (208, 218, "LUGAR"),  # "Tamaulipas"
                    (256, 274, "LUGAR"),  # "Brownsville, Texas"
                    (391, 414, "VICTIMAS"),  # "ciudadanos estadounidenses"
                    (436, 455, "AUTORIDAD"),  # "autoridades de México y Estados Unidos"
                    (734, 749, "LUGAR"),  # "Carolina del Norte"
                    (518, 528, "NUM_SECUESTRADOS"),  # "tres hombres y una mujer"
                    (2, 11, "TIPO_SECUESTRO"),  # "secuestro"
                    (955, 965, "AUTORIDAD"),  # "Ken Salazar"
                    (1246, 1249, "AUTORIDAD"),  # "FBI"
                    (1365, 1372, "RECOMPENSA"),  # "$50.000"
                ]
            }
        ),
        (
            "Una mujer extranjera involucrada con una banda de secuestradores fue la noticia que le dio vuelta al mundo y sacudió a México el 9 de diciembre de 2005, cuando en televisión nacional fueron aprehendidos la francesa Florence Cassez y el mexicano Israel Vallarta, el presunto líder de la organización criminal y su pareja, quien colaboraba con él. Tiempo después se descubrió que este episodio había sido un montaje mediático para plasmar la captura en vivo por parte de las autoridades del país a una banda que amenazaba el bienestar de la sociedad en una época en la que los secuestros eran una de las principales problemáticas. El escritor Jorge Volpi decidió contar esta historia en su libro Una novela criminal, que hoy es la base de la serie que expone la corrupción del sistema mexicano a partir de este caso. “Creí que lo que iba a hacer era llegar a la verdad sobre el caso analizando el expediente, entrevistando a todos los personajes, pero poco a poco se va convirtiendo en otra cosa, una novela y una investigación para darnos cuenta de por qué es imposible acceder a la verdad y por qué no funciona este sistema de justicia”, dice Volpi en entrevista. El autor y productor ejecutivo de El caso Cassez Vallarta: una novela criminal, que se estrena mañana en Netflix, busca que al plasmar esta información, primero en un libro y luego en una producción en pantalla, se dé al público un instrumento educativo, de justicia y de conciencia sobre “el desastre que es la justicia de México, donde no existen condiciones de estado de derecho”.",
            {
                "entities": [
                    (153, 172, "FECHA"),  # "9 de diciembre de 2005"
                    (144, 150, "LUGAR"),  # "México"
                    (237, 252, "VICTIMA"),  # "Florence Cassez"
                    (266, 280, "VICTIMA"),  # "Israel Vallarta"
                    (266, 280, "NUM_SECUESTRADORES"),  # "Israel Vallarta"
                    (72, 94, "NUM_SECUESTRADORES"),  # "banda de secuestradores"
                    (514, 523, "TIPO_SECUESTRO"),  # "secuestros"
                    (391, 413, "AUTORIDAD"),  # "las autoridades del país"
                    (434, 445, "FUENTE"),  # "Jorge Volpi"
                    (175, 193, "MEDIO"),  # "televisión nacional"
                    (877, 884, "MEDIO"),  # "Netflix"
                    (446, 467, "OBRA"),  # "Una novela criminal"
                    (583, 624, "OBRA")  # "El caso Cassez Vallarta: una novela criminal"
                ]
            }
        ),
        (
            "¿Te imaginas que de un momento a otro ya no tuvieras acceso a tu WhatsApp? Lamentamos decirte que esto es posible debido a un nuevo método que han encontrado los ciberdelincuentes para secuestrar tu cuenta. Los peor es que sólo necesitan crear un código QR (QRLJacking) con el que atrapan a sus víctimas. Aquí en Tech Bit te contamos cómo funciona y qué hacer para protegerte. Un Código QR podría ser la razón por la que tu WhatsApp sea hackeado. Foto: Freepik ¿Cómo se pueden robar tu cuenta de WhatsApp? En la actualidad, para conocer a una persona basta con echarle un ojo a sus redes sociales. Dentro de estos canales guardamos fotos, videos, claves, contraseñas, recuerdos con amigos y mucho más. Este tipo de información resulta por demás atractiva para los ciberdelincuentes. De ahí que busquen atacar a sus víctimas mediante actos de hackeo, robo de identidad o secuestro de cuentas y correos electrónicos. WhatsApp es una aplicación que se preocupa bastante por la seguridad y privacidad de sus usuarios. Razón por la que ha implementado medidas como el cifrado de extremo a extremo, el cual asegura que ningún mensaje sea visualizado fuera de nuestra cuenta. Sin embargo, lo anterior no impide que podamos caer en estafas o trucos engañosos que buscan conseguir nuestra información privada y uno de ellos es el QRLJacking. ¿Qué es el código QRLJacking? De acuerdo con McAfee, el QRLJacking 'es un ataque en el que los ciberdelincuentes aprovechan la confianza de los usuarios en los códigos QR para redirigirlos a sitios web maliciosos o para robar información personal'. Los especialistas señalan que dicha técnica se basa en la suplantación de identidad y puede tener graves consecuencias para los usuarios desprevenidos, por ejemplo: Pérdida de datos personales, que incluyen contraseñas, números de tarjetas de crédito y datos de identificación personal. Suplantación de identidad, es decir que los atacantes pueden hacerse pasar por sus víctimas y llevar a cabo actividades fraudulentas en su nombre. Robo de cuentas, utilizar la información obtenida a través del QRLJacking para acceder a las cuentas en línea de los usuarios y realizar transacciones no autorizadas. De esta forma tu cuenta de WhatsApp podría ser robada.",
            {
                "entities": [
                    (163, 180, "TIPO_CIBERCRIMEN"),  # "secuestro de cuentas"
                    (410, 420, "TIPO_CIBERCRIMEN"),  # "hackeo"
                    (302, 314, "TIPO_CIBERCRIMEN"),  # "QRLJacking"
                    (226, 235, "METODOLOGIA"),  # "código QR"
                    (302, 314, "METODOLOGIA"),  # "QRLJacking"
                    (708, 735, "CONSECUENCIA"),  # "Pérdida de datos personales"
                    (737, 761, "CONSECUENCIA"),  # "Suplantación de identidad"
                    (833, 847, "CONSECUENCIA"),  # "Robo de cuentas"
                    (395, 401, "APLICACION"),  # "WhatsApp"
                    (717, 723, "FUENTE"),  # "McAfee"
                    (236, 244, "FUENTE"),  # "Tech Bit"
                ]
            }
        ),
        (
            'Sabalan supuestamente se acercó a la niña en su vehículo y le exigió que subiera al decir: "Si no te subes al auto conmigo, te voy a lastimar", dijo la oficina en un comunicado. Temiendo por su seguridad, la menor subió. Durante dos días, Sabalan supuestamente llevó a la niña más de 19 horas desde Texas a California. Las autoridades dijeron que él la agredió sexualmente en numerosas ocasiones. El 9 de julio, Sabalan fue a una lavandería en Long Beach para lavar su ropa, según los fiscales federales. Mientras estaba dentro la niña escribió "¡Ayúdame!" en un pedazo de papel y lo sostuvo en alto. Un testigo vio el letrero y llamó a la policía, lo que llevó al rescate de la niña. El jefe de policía de Long Beach, Wally Hebeish, agradeció a la comunidad por ayudar a la niña. “Este incidente destaca el papel fundamental que desempeñan los miembros de la comunidad para mantener a las personas seguras”, dijo en un comunicado. “También me gustaría agradecer a nuestros oficiales por su rápida respuesta y acciones que llevaron a llevar a esta víctima a un lugar seguro”. La niña fue puesta al cuidado del Departamento de Servicios para Niños y Familias y desde entonces se ha reunido con su familia, dijo un portavoz de la Oficina del Fiscal Federal.',
            {
                "entities": [
                    (27, 34, "NUM_SECUESTRADORES"),  # "Sabalan"
                    (40, 47, "VICTIMA"),  # "la niña"
                    (114, 137, "USO_FUERZA"),  # "te voy a lastimar"
                    (153, 160, "VICTIMA"),  # "la menor"
                    (169, 184, "TIEMPO_SECUESTRO"),  # "Durante dos días"
                    (185, 192, "NUM_SECUESTRADORES"),  # "Sabalan"
                    (193, 239, "MOD_OPERACION"),  # "Sabalan supuestamente llevó a la niña más de 19 horas"
                    (240, 245, "LUGAR"),  # "Texas"
                    (248, 258, "LUGAR"),  # "California"
                    (297, 333, "MOD_OPERACION"),  # "mientras estaba dentro la niña escribió '¡Ayúdame!'"
                    (342, 351, "LUGAR"),  # "Long Beach"
                    (363, 372, "FECHA_RES"),  # "9 de julio"
                    (373, 391, "NUM_SECUESTRADORES"),  # "Sabalan"
                    (409, 428, "AUTORIDAD"),  # "fiscales federales"
                    (487, 519, "AUTORIDAD"),  # "jefe de policía de Long Beach"
                    (657, 689, "AUTORIDAD"),  # "Departamento de Servicios para Niños y Familias"
                    (746, 771, "AUTORIDAD")  # "Oficina del Fiscal Federal"
                ]
            }
        ),
        (
            "Una niña de 13 años que fue secuestrada en Texas fue rescatada a más de mil millas (mil 609.34 kilómetros), en California, después de que un buen samaritano viera su '¡Ayúdame!' y contactara a las autoridades. La niña, que no fue identificada, fue secuestrada a punta de pistola cerca de una parada de autobús en San Antonio el 6 de julio, dijo la Oficina del Fiscal Federal para el Distrito Central de California. Steven Robert Sabalan, de 61 años, de Cleburne, Texas, fue arrestado el 9 de julio y encarcelado en la Cárcel de Long Beach City por cargos de secuestro, actos lascivos en contra de un menor y fugitivo de la justicia, dijo el Departamento de Policía de Long Beach en un comunicado.",
            {
                "entities": [
                    (0, 20, "VICTIMA"),  # "Una niña de 13 años"
                    (43, 48, "LUGAR"),  # "Texas"
                    (79, 89, "LUGAR"),  # "California"
                    (203, 214, "LUGAR"),  # "San Antonio"
                    (218, 228, "FECHA_SECUESTRO"),  # "6 de julio"
                    (314, 337, "AUTORIDAD"),  # "Oficina del Fiscal Federal para el Distrito Central de California"
                    (339, 361, "NUM_SECUESTRADORES"),  # "Steven Robert Sabalan"
                    (366, 377, "LUGAR"),  # "Cleburne, Texas"
                    (386, 395, "FECHA_DETENCION"),  # "9 de julio"
                    (427, 451, "LUGAR"),  # "Cárcel de Long Beach City"
                    (261, 278, "USO_FUERZA"),  # "a punta de pistola"
                    (159, 168, "TIPO_SECUESTRO"),  # "secuestro"
                    (470, 505, "AUTORIDAD")  # "Departamento de Policía de Long Beach"
                ]
            }
        ),
        (
            "Cuernavaca, Mor.- La Fiscalía General del Estado abrió una carpeta de investigación por el presunto secuestro exprés en contra del obispo de Chilpancingo, Guerrero, Salvador Rangel Mendoza, reportado como desaparecido por la Conferencia del Episcopado Mexicano (CEM) desde el sábado pasado, pero encontrado con vida esta tarde en el hospital José G. Parres de Cuernavaca. El fiscal Uriel Carmona arribó al nosocomio antes de las 18:40 horas para corroborar legalmente la identidad del obispo y acordar con el Episcopado los términos de la difusión, 'pero la buena noticia es que esta bien', adelantó el fiscal. A su salida informó que el jerarca católico habría sido víctima de un secuestro exprés en el que sus captores habrían extraído dinero de sus cuentas en cajeros automáticos.",
            {
                "entities": [
                    (0, 14, "LUGAR"),  # "Cuernavaca, Mor"
                    (102, 120, "TIPO_SECUESTRO"),  # "secuestro exprés"
                    (134, 155, "LUGAR"),  # "Chilpancingo, Guerrero"
                    (157, 178, "VICTIMA"),  # "Salvador Rangel Mendoza"
                    (259, 278, "FECHA"),  # "desde el sábado pasado"
                    (334, 372, "LUGAR"),  # "hospital José G. Parres de Cuernavaca"
                    (576, 628, "USO_FUERZA"),  # "extracción de dinero de sus cuentas en cajeros automáticos"
                    (17, 46, "AUTORIDAD"),  # "Fiscalía General del Estado"
                    (185, 223, "AUTORIDAD"),  # "Conferencia del Episcopado Mexicano (CEM)"
                    (382, 399, "AUTORIDAD")  # "fiscal Uriel Carmona"
                ]
            }
        ),
        (
            "Fue saliendo de La Noria, normal. Yo siempre salía sólo, mi familia se había ido tres o cuatro días antes a Argentina y de repente aparecieron. Se me aparecieron gente con armas largas, yo pensé que era un robo pero no, me bajaron de la camioneta, se les escaparon un par de tiros, me subieron a un auto y a los 15 o 20 minutos me subieron a la cajuela de otro auto. 20 minutos después estaba en una casa todo tapado de la cara 65 días' agregó el protagonista de una historia terrible, que quedó grabada en la memoria de todos los seguidores del futbol mexicano. 'La única vez que me bañé fue cuando pensé que me iban a soltar pero no, escuché los audios y me iban a vender a otra banda' concluyó.",
            {
                "entities": [
                    (17, 25, "LUGAR"),  # "La Noria"
                    (105, 114, "LUGAR"),  # "Argentina"
                    (172, 183, "USO_FUERZA"),  # "armas largas"
                    (258, 294, "MOD_OPERACION"),  # "me subieron a la cajuela de otro auto"
                    (242, 266, "USO_FUERZA"),  # "se les escaparon un par de tiros"
                    (400, 407, "TIEMPO_CAUTIVERIO"),  # "65 días"
                    (491, 521, "MOD_OPERACION"),  # "me iban a vender a otra banda"
                    (330, 339, "TIPO_SECUESTRO")  # "secuestro"
                ]
            }
        ),
    ]

    # Paso 7: Entrenar el modelo NER
    train_ner_model(nlp, train_data)

    # Paso 8: Extraer entidades con el modelo entrenado
    results = extract_entities(nlp, df_filtrado_clasificador)

    # Paso 9: Guardar los resultados en la base de datos
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='Soccer.8a',
        database='noticias_prueba'
    )
    save_results(connection, results)

    print("Proceso completado y resultados guardados en la base de datos.")

# Ejecutar el pipeline
if __name__ == '__main__':
    main()
