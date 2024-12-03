# Instalación y carga de paquetes necesarios
library(RMySQL)
library(dplyr)
library(fastDummies)
library(dendextend)
library(factoextra)

# Conexión a la base de datos
con <- dbConnect(MySQL(),
                 user = 'root',
                 password = 'Soccer.8a',
                 host = 'localhost',
                 dbname = 'noticias')

# Cargar los datos de la tabla 'extracciones_filtradas'
datos <- dbGetQuery(con, "SELECT * FROM extracciones_filtradas")

# Paso 1: Seleccionar los Municipios Relevantes

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
print(paste("Número de registros seleccionados:", nrow(datos_filtrados)))

# Paso 2: Preparar los Datos para la Clusterización

# Seleccionar variables relevantes
datos_seleccionados <- datos_filtrados %>%
  select(estado, municipio, captor, lugar, tipo_secuestro)

# Convertir variables categóricas a factores
datos_seleccionados[] <- lapply(datos_seleccionados, as.factor)

# Generar variables dummy
datos_codificados <- dummy_cols(datos_seleccionados, 
                                remove_selected_columns = TRUE)

# Escalar los datos
datos_escalados <- scale(datos_codificados)

# Paso 3: Realizar la Clusterización Jerárquica

# Calcular la matriz de distancias
distancias <- dist(datos_escalados, method = "euclidean")

# Aplicar clusterización jerárquica
cluster_jerarquico <- hclust(distancias, method = "complete")

# Crear etiquetas para el dendrograma
datos_seleccionados$etiqueta <- paste(datos_seleccionados$estado, datos_seleccionados$municipio, sep = "-")

# Asignar las etiquetas al objeto de clusterización
cluster_jerarquico$labels <- datos_seleccionados$etiqueta

# Convertir a un objeto dendrograma
dendro <- as.dendrogram(cluster_jerarquico)

# Ajustar el tamaño de las etiquetas para mejorar la legibilidad
dendro <- set(dendro, "labels_cex", 0.6)

# Graficar el dendrograma con etiquetas
plot(dendro, main = "Dendrograma de Clusterización Jerárquica con Etiquetas",
     ylab = "Distancia", cex.lab = 0.8, cex.axis = 0.8)

# Paso 4: Validar el Número de Clústeres

# Validar el número de clústeres usando el método del codo
fviz_nbclust(datos_escalados, FUN = hcut, method = "wss", k.max = 10) +
  labs(title = "Determinación del Número Óptimo de Clústeres (Método del Codo)")

# Validar el número de clústeres usando el índice de silueta
fviz_nbclust(datos_escalados, FUN = hcut, method = "silhouette", k.max = 10) +
  labs(title = "Determinación del Número Óptimo de Clústeres (Índice de Silueta)")

# Definir el número de clústeres según la validación
k <- 4  # Ajusta este número según el resultado de la validación

# Cortar el dendrograma para formar los clústeres
grupos <- cutree(cluster_jerarquico, k = k)

# Agregar los clústeres al conjunto de datos
datos_seleccionados$cluster <- grupos

# Colorear las ramas según los clústeres
dendro_coloreado <- color_branches(dendro, k = k)

# Graficar el dendrograma con ramas coloreadas y etiquetas
plot(dendro_coloreado, main = "Dendrograma de Clusterización Jerárquica con Etiquetas",
     ylab = "Distancia", cex.lab = 0.8, cex.axis = 0.8)

# Paso 5: Analizar e Interpretar los Clústeres

# Resumir las características de cada clúster con los valores más frecuentes
resumen_clusters <- datos_seleccionados %>%
  group_by(cluster) %>%
  summarise(
    n = n(),
    estados_principales = paste(names(sort(table(estado), decreasing = TRUE)[1:2]), collapse = ", "),
    municipios_principales = paste(names(sort(table(municipio), decreasing = TRUE)[1:2]), collapse = ", "),
    captor_principal = names(sort(table(captor), decreasing = TRUE))[1],
    lugar_principal = names(sort(table(lugar), decreasing = TRUE))[1],
    tipo_secuestro_principal = names(sort(table(tipo_secuestro), decreasing = TRUE))[1]
  )

# Ver el resumen
print(resumen_clusters)

# Paso 6: Generar Recomendaciones Generales

# Función para generar recomendaciones generales
generar_recomendacion_general <- function(cluster_info) {
  paste0("En los municipios de ", cluster_info$municipios_principales,
         " del estado(s) ", cluster_info$estados_principales,
         ", se observa una alta incidencia de secuestros del tipo '", cluster_info$tipo_secuestro_principal,
         "', frecuentemente realizados por '", cluster_info$captor_principal,
         "'. Se recomienda implementar medidas de seguridad enfocadas en '", cluster_info$lugar_principal,
         "'.")
}

# Generar recomendaciones para cada clúster
resumen_clusters <- resumen_clusters %>%
  rowwise() %>%
  mutate(recomendacion = generar_recomendacion_general(cur_data()))

# Ver las recomendaciones generales
print(resumen_clusters[, c("cluster", "recomendacion")])

# Paso 7: Identificar Casos Aislados (Outliers)

# Calcular las distancias de cada observación a su clúster correspondiente
# Usaremos la distancia al centroide del clúster (media de las observaciones del clúster)

# Añadir las coordenadas de cada observación
datos_seleccionados <- cbind(datos_seleccionados, datos_escalados)

# Calcular los centroides de cada clúster
centroides <- datos_seleccionados %>%
  group_by(cluster) %>%
  summarise(across(starts_with("estado_"), mean),
            across(starts_with("municipio_"), mean),
            across(starts_with("captor_"), mean),
            across(starts_with("lugar_"), mean),
            across(starts_with("tipo_secuestro_"), mean))

# Calcular la distancia euclidiana de cada observación a su centroide
distancias_a_centroide <- numeric(nrow(datos_seleccionados))

for (i in 1:nrow(datos_seleccionados)) {
  cluster_i <- datos_seleccionados$cluster[i]
  centroide_i <- centroides[centroides$cluster == cluster_i, -1]
  observacion_i <- datos_seleccionados[i, names(centroide_i)]
  distancias_a_centroide[i] <- dist(rbind(observacion_i, centroide_i))
}

# Añadir las distancias al conjunto de datos
datos_seleccionados$distancia_centroide <- distancias_a_centroide

# Definir un umbral para considerar casos aislados (por ejemplo, percentil 95)
umbral_outlier <- quantile(distancias_a_centroide, 0.95)

# Identificar los casos aislados
datos_outliers <- datos_seleccionados %>%
  filter(distancia_centroide > umbral_outlier)

# Paso 8: Generar Recomendaciones para Casos Aislados

if(nrow(datos_outliers) > 0) {
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
  
  # Ver las recomendaciones para los casos aislados
  print(datos_outliers[, c("estado", "municipio", "recomendacion")])
} else {
  print("No se identificaron casos aislados significativos.")
}

# Cerrar la conexión a la base de datos
dbDisconnect(con)
