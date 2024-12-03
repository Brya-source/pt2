# Instalar paquetes si es necesario
 install.packages(c("DBI", "RMySQL", "dplyr", "ggplot2", "lubridate"))

# Cargar librerías
library(DBI)
library(RMySQL)
library(dplyr)
library(ggplot2)
library(lubridate)

 # Establecer conexión a la base de datos
 con <- dbConnect(RMySQL::MySQL(),
                  dbname = "noticias",
                  host = "localhost",
                  port = 3306,
                  user = "root",
                  password = "Soccer.8a")
 
 # Cargar datos de la tabla 'extracciones_filtradas'
 data <- dbGetQuery(con, "SELECT * FROM extracciones_filtradas")
 
 # Verificar valores faltantes
 colSums(is.na(data))
 
 # Opcional: Eliminar filas con valores faltantes en variables clave
 data_clean <- data %>%
   filter(!is.na(estado), !is.na(año_secuestro), !is.na(mes_secuestro))
 
 # Convertir 'año_secuestro' a numérico
 data_clean$año_secuestro <- as.numeric(data_clean$año_secuestro)
 
 # Convertir 'mes_secuestro' a número de mes
 data_clean$mes_secuestro_num <- match(tolower(data_clean$mes_secuestro),
                                       tolower(c("Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                                                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre")))
 
 # Crear una columna de fecha
 data_clean$fecha_secuestro <- as.Date(paste(data_clean$año_secuestro, data_clean$mes_secuestro_num, "01", sep = "-"))
 
 # Verificar la nueva columna de fecha
 head(data_clean$fecha_secuestro)
 
 # Conteo de secuestros por año
 secuestros_por_año <- data_clean %>%
   group_by(año_secuestro) %>%
   summarise(total_secuestros = n())
 
 # Visualización
 ggplot(secuestros_por_año, aes(x = año_secuestro, y = total_secuestros)) +
   geom_line(color = "blue") +
   geom_point(color = "red") +
   labs(title = "Número de Secuestros por Año en México", x = "Año", y = "Cantidad de Secuestros") +
   theme_minimal()
 
 