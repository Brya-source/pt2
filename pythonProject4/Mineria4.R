# Añadir las librerías necesarias
# install.packages("FactoMineR")  # Comenta esta línea si ya tienes instalado FactoMineR

library(RMySQL)
library(dplyr)
library(fastDummies)
library(dendextend)
library(factoextra)
library(FactoMineR)  # Para realizar MCA

# Conexión a la base de datos
con <- dbConnect(MySQL(),
                 user = 'root',
                 password = 'Soccer.8a',
                 host = 'localhost',
                 dbname = 'noticias')

# Cargar los datos de la tabla 'extracciones_filtradas'
datos <- dbGetQuery(con, "SELECT * FROM extracciones_filtradas")

# Filtrar los registros donde 'captura' es diferente de 'no especifico'
datos_filtrados <- datos %>%
  filter(captura != 'no especifico')

# Paso 1: Seleccionar los Municipios Relevantes

# Contar el número de incidentes por municipio
incidentes_por_municipio <- datos_filtrados %>%
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

# Filtrar los datos para incluir solo los municipios seleccionados
datos_filtrados <- datos_filtrados %>%
  filter(municipio %in% municipios_seleccionados)

# Verificar el número de registros
print(paste("Número de registros seleccionados:", nrow(datos_filtrados)))

# Paso 2: Preparar los Datos para la Clusterización con MCA

# Seleccionar variables categóricas relevantes, incluyendo 'captura'
datos_categoricos <- datos_filtrados %>%
  select(estado, municipio, captor, lugar, tipo_secuestro, captura)

# Convertir variables categóricas a factores
datos_categoricos[] <- lapply(datos_categoricos, as.factor)

# Realizar el MCA
resultado_mca <- MCA(datos_categoricos, graph = FALSE)

# Visualizar la varianza explicada por los componentes
fviz_screeplot(resultado_mca, addlabels = TRUE, ylim = c(0, 50))

# Decidir cuántas dimensiones retener (por ejemplo, las primeras 5)
num_dimensiones <- 3
datos_reducidos <- resultado_mca$ind$coord[, 1:num_dimensiones]

# Paso 3: Realizar la Clusterización Jerárquica con Datos Reducidos

# Calcular la matriz de distancias
distancias <- dist(datos_reducidos, method = "euclidean")

# Aplicar clusterización jerárquica
cluster_jerarquico <- hclust(distancias, method = "complete")

# Crear etiquetas para el dendrograma
datos_categoricos$etiqueta <- paste(datos_categoricos$estado, datos_categoricos$municipio, sep = "-")

# Asignar las etiquetas al objeto de clusterización
cluster_jerarquico$labels <- datos_categoricos$etiqueta

# Convertir a un objeto dendrograma
dendro <- as.dendrogram(cluster_jerarquico)

# Colorear las ramas según los clústeres
k <- 4  # Ajusta este número según el resultado de la validación
dendro_coloreado <- color_branches(dendro, k = k)

# Eliminar las etiquetas del dendrograma coloreado
dendro_coloreado <- dendro_coloreado %>% set("labels", NULL)

# Graficar el dendrograma coloreado sin etiquetas
plot(dendro_coloreado, main = "Dendrograma de Clusterización Jerárquica con MCA",
     ylab = "Distancia", cex.lab = 0.8, cex.axis = 0.8)

# Paso 4: Validar el Número de Clústeres

# Validar el número de clústeres usando el método del codo
fviz_nbclust(datos_reducidos, FUN = hcut, method = "wss", k.max = 10) +
  labs(title = "Determinación del Número Óptimo de Clústeres (Método del Codo)")

# Validar el número de clústeres usando el índice de silueta
fviz_nbclust(datos_reducidos, FUN = hcut, method = "silhouette", k.max = 10) +
  labs(title = "Determinación del Número Óptimo de Clústeres (Índice de Silueta)")

# Definir el número de clústeres según la validación (ya definido arriba)
# k <- 4  # Ajusta este número según el resultado de la validación

# Cortar el dendrograma para formar los clústeres
grupos <- cutree(cluster_jerarquico, k = k)

# Agregar los clústeres al conjunto de datos
datos_categoricos$cluster <- grupos

# Paso 5: Analizar e Interpretar los Clústeres

# Resumir las características de cada clúster con los valores más frecuentes, incluyendo 'captura'
resumen_clusters <- datos_categoricos %>%
  group_by(cluster) %>%
  summarise(
    n = n(),
    estado = names(sort(table(estado), decreasing = TRUE))[1],
    municipio = names(sort(table(municipio), decreasing = TRUE))[1],
    captor_principal = names(sort(table(captor), decreasing = TRUE))[1],
    lugar_principal = names(sort(table(lugar), decreasing = TRUE))[1],
    tipo_secuestro_principal = names(sort(table(tipo_secuestro), decreasing = TRUE))[1],
    captura_principal = names(sort(table(captura), decreasing = TRUE))[1]
  )

# Ver el resumen
print(resumen_clusters)

# Paso 6: Generar Recomendaciones Generales

# Función para generar recomendaciones para el estado (sin 'captura_principal')
generar_recomendacion_estado <- function(estado, municipio, captor_principal, lugar_principal, tipo_secuestro_principal) {
  paste0("En el municipio de ", municipio,
         " del estado ", estado,
         ", se observa una alta incidencia de secuestros del tipo '", tipo_secuestro_principal,
         "', frecuentemente perpetrados por '", captor_principal,
         "'. Se recomienda al estado implementar medidas de seguridad enfocadas en '", lugar_principal,
         "'.")
}

# Función para generar recomendaciones para la población (incluyendo 'captura_principal' y 'lugar_principal')
generar_recomendacion_poblacion <- function(estado, municipio, captura_principal, lugar_principal) {
  paste0("Se recomienda a la población del municipio de ", municipio,
         " en el estado ", estado,
         ", tener precaución ante posibles secuestros realizados mediante '", captura_principal,
         "' en '", lugar_principal,
         "'. Manténgase alerta y tome medidas preventivas.")
}

# Generar recomendaciones para cada clúster
resumen_clusters <- resumen_clusters %>%
  rowwise() %>%
  mutate(
    recomendacion_estado = generar_recomendacion_estado(estado, municipio, captor_principal, lugar_principal, tipo_secuestro_principal),
    recomendacion_poblacion = generar_recomendacion_poblacion(estado, municipio, captura_principal, lugar_principal)
  )

# Guardar las recomendaciones en un archivo CSV
write.csv(resumen_clusters, "recomendaciones_generales.csv", row.names = FALSE)

# También puede guardarlas en un archivo de texto
write.table(resumen_clusters[, c("cluster", "recomendacion_estado", "recomendacion_poblacion")], "recomendaciones_generales.txt", row.names = FALSE, col.names = TRUE, sep = "\t", quote = FALSE)

# Paso 7: Identificar Casos Aislados (Outliers)

# Calcular las distancias de cada observación a su centroide de clúster
centroides <- datos_reducidos %>%
  as.data.frame() %>%
  mutate(cluster = datos_categoricos$cluster) %>%
  group_by(cluster) %>%
  summarise_all(mean)

# Calcular distancias a centroides
distancias_a_centroide <- mapply(function(row, cluster) {
  centroide <- centroides[centroides$cluster == cluster, -1]
  dist(rbind(as.numeric(row), as.numeric(centroide)))
}, split(datos_reducidos, seq(nrow(datos_reducidos))), datos_categoricos$cluster)

# Añadir las distancias al conjunto de datos
datos_categoricos$distancia_centroide <- distancias_a_centroide

# Definir un umbral para considerar casos aislados (por ejemplo, percentil 95)
umbral_outlier <- quantile(distancias_a_centroide, 0.95, na.rm = TRUE)

# Identificar los casos aislados
datos_outliers <- datos_categoricos %>%
  filter(distancia_centroide > umbral_outlier)

# Paso 8: Generar Recomendaciones para Casos Aislados

if(nrow(datos_outliers) > 0) {
  # Función para generar recomendaciones para casos aislados, incluyendo 'captura'
  generar_recomendacion_outlier <- function(estado, municipio, captor, lugar, tipo_secuestro, captura) {
    paste0("En el municipio de ", municipio, " del estado de ", estado, 
           ", se ha identificado un caso particular de secuestro de tipo '", tipo_secuestro, 
           "', realizado mediante '", captura,
           "', perpetrado por '", captor, 
           "' en el lugar '", lugar, 
           "'. Se recomienda investigar este caso en detalle y considerar medidas específicas.")
  }
  
  # Generar recomendaciones para los casos aislados
  datos_outliers <- datos_outliers %>%
    rowwise() %>%
    mutate(recomendacion = generar_recomendacion_outlier(estado, municipio, captor, lugar, tipo_secuestro, captura))
  
  # Guardar las recomendaciones para casos aislados en un archivo CSV
  write.csv(datos_outliers[, c("estado", "municipio", "recomendacion")], "recomendaciones_outliers.csv", row.names = FALSE)
  
  # También puede guardarlas en un archivo de texto
  write.table(datos_outliers[, c("estado", "municipio", "recomendacion")], "recomendaciones_outliers.txt", row.names = FALSE, col.names = TRUE, sep = "\t", quote = FALSE)
  
} else {
  print("No se identificaron casos aislados significativos.")
}

# Cerrar la conexión a la base de datos
dbDisconnect(con)

