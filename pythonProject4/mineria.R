# Instalar y cargar paquetes necesarios
install.packages("RMySQL")
library(RMySQL)

# Conectar a la base de datos
con <- dbConnect(MySQL(),
                 user = 'root',
                 password = 'Soccer.8a',
                 host = 'localhost',
                 dbname = 'noticias')

# Cargar los datos de la tabla 'extracciones_filtradas'
datos <- dbGetQuery(con, "SELECT * FROM extracciones_filtradas")

library(dplyr)

# Contar el número de incidentes por municipio
incidentes_por_municipio <- datos %>%
  group_by(municipio) %>%
  summarise(num_incidentes = n()) %>%
  arrange(desc(num_incidentes))

# Seleccionar los 15 municipios con más incidentes
top_15_municipios <- incidentes_por_municipio %>%
  slice(1:15) %>%
  pull(municipio)

# Seleccionar los 5 municipios con menos incidentes (considerando municipios con al menos un incidente)
bottom_5_municipios <- incidentes_por_municipio %>%
  filter(num_incidentes > 0) %>%
  slice_tail(n = 5) %>%
  pull(municipio)

# Combinar los municipios seleccionados
municipios_seleccionados <- c(top_15_municipios, bottom_5_municipios)

# Filtrar los datos
datos_filtrados <- datos %>%
  filter(municipio %in% municipios_seleccionados)

# Verificar el número de registros
nrow(datos_filtrados)

datos_seleccionados <- datos_filtrados %>%
  select(estado, municipio, captor, lugar, tipo_secuestro)

# Convertir a factores
datos_seleccionados[] <- lapply(datos_seleccionados, as.factor)

library(fastDummies)

# Generar variables dummy
datos_codificados <- dummy_cols(datos_seleccionados, 
                                remove_selected_columns = TRUE)

# Escalar los datos
datos_escalados <- scale(datos_codificados)

# Calcular la matriz de distancias
distancias <- dist(datos_escalados, method = "euclidean")

# Aplicar clusterización jerárquica
cluster_jerarquico <- hclust(distancias, method = "complete")

# Visualizar el dendrograma sin etiquetas
plot(cluster_jerarquico, labels = FALSE, hang = -1, 
     main = "Dendrograma de Clusterización Jerárquica")

# Cortar el dendrograma en un número específico de clústeres
k <- 4  # Puedes ajustar este número
grupos <- cutree(cluster_jerarquico, k = k)

# Agregar los clústeres al conjunto de datos
datos_seleccionados$cluster <- grupos

# Resumir las características de cada clúster
resumen_clusters <- datos_seleccionados %>%
  group_by(cluster) %>%
  summarise(
    n = n(),
    estados = paste(unique(estado), collapse = ", "),
    municipios = paste(unique(municipio), collapse = ", "),
    captores = paste(unique(captor), collapse = ", "),
    lugares = paste(unique(lugar), collapse = ", "),
    tipos_secuestro = paste(unique(tipo_secuestro), collapse = ", ")
  )

# Ver el resumen
print(resumen_clusters)

# Obtener las alturas de los clusters
alturas <- cluster_jerarquico$height

# Definir un umbral alto de corte para identificar outliers
umbral_outlier <- quantile(alturas, 0.95)

# Identificar clusters que se formaron a una altura mayor al umbral
clusters_outliers <- which(alturas > umbral_outlier)

# Si hay clusters outliers, podemos revisar los casos asociados
if(length(clusters_outliers) > 0) {
  # Obtener los índices de los casos en estos clusters
  indices_outliers <- cluster_jerarquico$order[clusters_outliers]
  
  # Extraer los casos outliers
  datos_outliers <- datos_seleccionados[indices_outliers, ]
  
  # Ver los casos outliers
  print(datos_outliers)
} else {
  print("No se identificaron casos aislados significativos.")
}

if(exists("datos_outliers")) {
  # Función para generar recomendaciones para casos aislados
  generar_recomendacion_outlier <- function(estado, municipio, captor, lugar, tipo_secuestro) {
    paste0("En el municipio de ", municipio, " del estado de ", estado, 
           ", se ha identificado un caso particular de secuestro de tipo '", tipo_secuestro, 
           "', realizado por '", captor, 
           "' en el lugar '", lugar, 
           "'. Se recomienda investigar este caso en detalle y considerar medidas específicas.")
  }
  
  # Generar recomendaciones para los casos aislados
  datos_outliers <- datos_outliers %>%
    rowwise() %>%
    mutate(recomendacion = generar_recomendacion_outlier(estado, municipio, captor, lugar, tipo_secuestro))
  
  # Ver las recomendaciones
  print(datos_outliers[, c("estado", "municipio", "recomendacion")])
}
