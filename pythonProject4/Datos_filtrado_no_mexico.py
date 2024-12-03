# Importar las librerías necesarias
import pandas as pd
from sqlalchemy import create_engine

# Crear una conexión a la base de datos
# Reemplaza 'usuario', 'contraseña', 'host' y 'puerto' con tus credenciales reales
engine = create_engine('mysql+pymysql://root:Soccer.8a@localhost:3306/noticias')

# Definir la consulta SQL para extraer los datos que NO son de México
query_no_mexico = """
SELECT
    id,
    pais,
    estado,
    liberacion,
    tipo_liberacion,
    mes_secuestro,
    año_secuestro,
    captor,
    lugar,
    captura,
    tipo_secuestro
FROM extracciones
WHERE relacion_spacy4 = 'Sí'
  AND (noticias_repetidas IS NULL OR noticias_repetidas <> 1)
  AND año_secuestro > '2015'
  AND pais <> 'México'  -- Filtro para excluir el país México
"""

# Leer los datos que NO son de México desde la base de datos
df_no_mexico = pd.read_sql(query_no_mexico, engine)

# Definir los campos requeridos para el análisis
campos_requeridos = [
    'pais', 'estado', 'liberacion', 'tipo_liberacion',
    'mes_secuestro', 'año_secuestro', 'captor', 'lugar', 'captura', 'tipo_secuestro'
]

# Filtrar los registros que no tienen valores nulos o vacíos en los campos requeridos
df_no_mexico_filtered = df_no_mexico.dropna(subset=campos_requeridos)
df_no_mexico_filtered = df_no_mexico_filtered[(df_no_mexico_filtered[campos_requeridos] != '').all(axis=1)]

# Opcional: Resetear el índice si es necesario
df_no_mexico_filtered.reset_index(drop=True, inplace=True)

# Crear una nueva tabla en la base de datos con los datos filtrados fuera de México
# El nombre de la tabla será 'extracciones_filtradas_no_mexico'
df_no_mexico_filtered.to_sql('extracciones_filtradas_no_mexico', con=engine, if_exists='replace', index=False)

# Cerrar la conexión a la base de datos
engine.dispose()

