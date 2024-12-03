import pymysql
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, classification_report

# Función para conectar a la base de datos
def conectar_base_datos():
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='Soccer.8a',  # Ajusta con tu contraseña
        database='noticias_prueba'
    )
    return connection

# Consulta para obtener noticias de secuestro (anotar como 1)
def obtener_noticias_secuestro(connection):
    consulta_secuestro = """
    SELECT titulo, descripcion 
    FROM extracciones 
    WHERE (descripcion LIKE '%secuestro%' 
    OR descripcion LIKE '%secuestr%' 
    OR titulo LIKE '%secuestro%' 
    OR titulo LIKE '%secuestr%')
    AND (noticia IS NOT NULL AND noticia != '')
    LIMIT 3000;
    """
    with connection.cursor() as cursor:
        cursor.execute(consulta_secuestro)
        noticias_secuestro = cursor.fetchall()
    return noticias_secuestro

# Consulta para obtener noticias no relacionadas con secuestro (anotar como 0)
def obtener_noticias_no_secuestro(connection):
    consulta_no_secuestro = """
    SELECT titulo, descripcion 
    FROM extracciones 
    WHERE (descripcion NOT LIKE '%secuestro%' 
    AND descripcion NOT LIKE '%secuestr%' 
    AND titulo NOT LIKE '%secuestro%' 
    AND titulo NOT LIKE '%secuestr%')
    AND (noticia IS NOT NULL AND noticia != '')
    LIMIT 3000;
    """
    with connection.cursor() as cursor:
        cursor.execute(consulta_no_secuestro)
        noticias_no_secuestro = cursor.fetchall()
    return noticias_no_secuestro

# Función para crear el dataset de entrenamiento
def crear_dataset(connection):
    # Obtener noticias relacionadas con secuestro (anotadas como 1)
    noticias_secuestro = obtener_noticias_secuestro(connection)
    datos_secuestro = [(titulo, descripcion, 1) for titulo, descripcion in noticias_secuestro]

    # Obtener noticias no relacionadas con secuestro (anotadas como 0)
    noticias_no_secuestro = obtener_noticias_no_secuestro(connection)
    datos_no_secuestro = [(titulo, descripcion, 0) for titulo, descripcion in noticias_no_secuestro]

    # Unir ambas listas
    dataset = datos_secuestro + datos_no_secuestro

    # Convertir a DataFrame de pandas
    df = pd.DataFrame(dataset, columns=['titulo', 'descripcion', 'es_secuestro'])
    return df

# Entrenamiento del modelo
def entrenar_modelo(df):
    # Combinar el título y la descripción en una única columna de texto para el entrenamiento
    df['texto_completo'] = df['titulo'] + " " + df['descripcion']

    # Preprocesamiento: vectorización TF-IDF
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(df['texto_completo'])  # Convertir los textos a vectores TF-IDF
    y = df['es_secuestro']  # Etiquetas (1 o 0)

    # Dividir en conjuntos de entrenamiento y prueba
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

    # Entrenar el clasificador Naive Bayes
    clf = MultinomialNB()
    clf.fit(X_train, y_train)

    # Evaluación del modelo
    y_pred = clf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, target_names=['No secuestro', 'Secuestro'], output_dict=True)

    # Mostrar los resultados en español
    print(f"Exactitud (Accuracy): {accuracy:.3f}")
    print("\nMétricas por clase:\n")
    for clase, valores in report.items():
        if clase in ['No secuestro', 'Secuestro']:
            print(f"Clase: {clase}")
            print(f"  Precisión (Precision): {valores['precision']:.2f}")
            print(f"  Sensibilidad (Recall): {valores['recall']:.2f}")
            print(f"  Equilibrio entre precisión y sensibilidad (F1-Score): {valores['f1-score']:.2f}")
            print(f"  Soporte (Número de ejemplos): {int(valores['support'])}\n")

    return clf, vectorizer

# Función para predecir si una noticia está relacionada con secuestros
def predecir_secuestro(titulo, descripcion, clf, vectorizer):
    texto_completo = titulo + " " + descripcion
    texto_vect = vectorizer.transform([texto_completo])
    prediccion = clf.predict(texto_vect)
    return prediccion[0]  # 1 si es secuestro, 0 si no lo es

# Función para probar varios ejemplos
def probar_ejemplos(clf, vectorizer):
    ejemplos = [
        # Ejemplos sin relación con secuestro
        ("El mercado de valores alcanza un nuevo récord histórico", "Los analistas predicen un crecimiento económico sostenido para el próximo trimestre."),
        ("México celebra el Día de la Independencia con desfiles", "Las calles se llenan de color en la capital del país mientras los ciudadanos celebran la independencia."),
        ("El equipo nacional de fútbol gana el campeonato", "Una victoria espectacular en los últimos minutos aseguró el campeonato para el equipo local."),

        # Ejemplos donde el título está relacionado pero la descripción no
        ("Secuestro en la Ciudad de México sacude a la comunidad", "Los residentes locales han expresado preocupación por la seguridad en la zona."),
        ("El nuevo alcalde toma posesión del cargo en Monterrey", "Durante su discurso, mencionó la liberación reciente de una víctima de secuestro en la región."),
        ("Secuestradores exigen rescate en Monterrey", "El gobierno local se prepara para nuevas elecciones el próximo mes."),

        # Ejemplos donde ambos están relacionados
        ("Rescate de víctima de secuestro en Guadalajara", "La víctima fue liberada después de tres días de cautiverio y la intervención de las autoridades locales."),
        ("Secuestro en una zona residencial causa pánico", "Un grupo armado irrumpió en una casa y privó de su libertad a tres personas."),
        ("Secuestradores capturados por la policía en Ciudad Juárez", "Las autoridades lograron arrestar a los responsables después de una persecución de varias horas.")
    ]

    for titulo, descripcion in ejemplos:
        resultado = predecir_secuestro(titulo, descripcion, clf, vectorizer)
        print(f"Título: {titulo}\nDescripción: {descripcion}\nPredicción: {'Secuestro' if resultado == 1 else 'No secuestro'}\n")

# Función principal
def main():
    # Conectar a la base de datos
    connection = conectar_base_datos()

    try:
        # Crear el dataset con las consultas a la base de datos
        df = crear_dataset(connection)

        # Entrenar el modelo con los datos obtenidos
        clf, vectorizer = entrenar_modelo(df)

        # Probar ejemplos de predicción
        probar_ejemplos(clf, vectorizer)

    finally:
        connection.close()  # Cerrar la conexión a la base de datos

if __name__ == '__main__':
    main()
