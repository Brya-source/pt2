import twint

# Configuración de Twint
c = twint.Config()
c.Search = "secuestro"
c.Limit = 1000
c.Lang = "es"
c.Near = "Mexico"
c.Since = "2022-01-01"
c.Until = "2024-01-01"

# Configuración para almacenar en MySQL
c.Database = "mysql"  # Indica que usará MySQL
c.DB_host = "localhost"
c.DB_user = "root"
c.DB_pass = "Soccer.8a"
c.DB_name = "twitter_data"
c.DB_table = "tweets"

# Ejecutar la búsqueda
twint.run.Search(c)
