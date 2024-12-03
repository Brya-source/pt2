import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, classification_report

# Paso 1: Aquí debes agregar el título y la descripción de las noticias junto con la anotación
# Si la noticia es sobre secuestro, anota 1; si no, anota 0
train_data = [
    # Formato: ("Título de la noticia", "Descripción de la noticia", Etiqueta)
    ("Secuestro en la Ciudad de México deja a una persona desaparecida", "La policía investiga un secuestro en la colonia Roma", 1),
    ("La economía crece un 3% en el primer trimestre", "México experimenta un crecimiento económico este año", 0),
    ("Secuestradores piden rescate por una víctima en Monterrey", "El secuestro ocurrió la noche del miércoles en una zona residencial", 1),
    ("Nuevo récord en el mercado de valores", "El mercado de valores en México alcanza un máximo histórico", 0),
    # Añade más ejemplos a continuación para entrenar el modelo
]

# Convertir el subconjunto de datos anotados a un DataFrame de pandas
df = pd.DataFrame(train_data, columns=['titulo', 'descripcion', 'es_secuestro'])

# Paso 2: Combinar el título y la descripción en una única columna de texto para el entrenamiento
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
print("Accuracy:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred))

# Función para predecir si una noticia está relacionada con secuestros
def predecir_secuestro(titulo, descripcion):
    texto_completo = titulo + " " + descripcion
    texto_vect = vectorizer.transform([texto_completo])
    prediccion = clf.predict(texto_vect)
    return prediccion[0]  # 1 si es secuestro, 0 si no lo es

# Ejemplo de predicción con una nueva noticia
titulo_ejemplo = "Los secuestradores pidieron rescate por la víctima"
descripcion_ejemplo = "El incidente ocurrió en Ciudad de México"
print(predecir_secuestro(titulo_ejemplo, descripcion_ejemplo))
