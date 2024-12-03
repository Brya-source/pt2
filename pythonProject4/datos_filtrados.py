# Importar las librerías necesarias
import pandas as pd
from sqlalchemy import create_engine

# Crear una conexión a la base de datos
# Reemplaza 'usuario', 'contraseña', 'host' y 'puerto' con tus credenciales
engine = create_engine('mysql+pymysql://root:Soccer.8a@localhost:3306/noticias')

# Definir la consulta SQL para extraer los datos con los filtros iniciales
query = """
SELECT
    id,
    pais,
    estado,
    municipio,
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
  AND pais = 'México'  -- Filtro adicional para el país México
"""

# Leer los datos desde la base de datos
df = pd.read_sql(query, engine)

# Definir los campos requeridos para el análisis
campos_requeridos = [
    'pais', 'estado', 'municipio', 'liberacion', 'tipo_liberacion',
    'mes_secuestro', 'año_secuestro', 'captor', 'lugar', 'captura', 'tipo_secuestro'
]

# Filtrar los registros que no tienen valores nulos o vacíos en los campos requeridos
df_filtered = df.dropna(subset=campos_requeridos)
df_filtered = df_filtered[(df_filtered[campos_requeridos] != '').all(axis=1)]

# Opcional: Resetear el índice si es necesario
df_filtered.reset_index(drop=True, inplace=True)

# Crear una nueva tabla en la base de datos con los datos filtrados
# Puedes elegir el nombre de la nueva tabla, por ejemplo, 'extracciones_filtradas_mexico'
df_filtered.to_sql('extracciones_filtradas', con=engine, if_exists='replace', index=False)

# Cerrar la conexión
engine.dispose()
