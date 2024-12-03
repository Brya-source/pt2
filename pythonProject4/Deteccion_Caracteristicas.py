import spacy

# Cargamos el modelo de spaCy
nlp = spacy.load('es_core_news_md')

# Diccionario de estados y municipios de México
estados_mexico = {
    "aguascalientes": ["aguascalientes", "calvillo", "jesús maría", "rincón de romos", "san francisco de los romo", "pabellón de arteaga", "tepezalá", "cosío", "el llano", "asientos"],
    "baja california": ["tijuana", "ensenada", "mexicali", "rosarito", "tecate", "san quintín", "playas de rosarito"],
    "baja california sur": ["la paz", "los cabos", "loreto", "comondú", "mulegé", "santa rosalia", "guerrero negro"],
    "campeche": ["campeche", "ciudad del carmen", "calakmul", "hopelchén", "escárcega", "tenabo", "hecelchakán", "calkiní", "palizada", "champotón"],
    "coahuila": ["saltillo", "torreón", "monclova", "piedras negras", "acuña", "frontera", "san pedro", "sabinás", "múzquiz", "allende", "nava", "ramos arizpe"],
    "colima": ["colima", "manzanillo", "tecomán", "villa de álvarez", "comala", "cuauhtémoc", "coquimatlán", "ixtlahuacán", "armenia", "minatitlán"],
    "chiapas": ["tuxtla gutiérrez", "san cristóbal de las casas", "tapachula", "comitán", "palenque", "ocosingo", "tonalá", "arriaga", "villaflores", "mapastepec"],
    "chihuahua": ["chihuahua", "ciudad juárez", "delicias", "cuauhtémoc", "parral", "camargo", "nuevo casas grandes", "meoqui", "jiménez", "guachochi"],
    "ciudad de méxico": ["azcapotzalco", "coyoacán", "cuajimalpa", "gustavo a. madero", "alvaro obregón", "benito juárez", "iztapalapa", "miguel hidalgo", "tlalpan", "xochimilco"],
    "durango": ["durango", "gómez palacio", "lerdo", "canatlán", "poanas", "nuevo ideal", "mapimí", "nombre de dios", "santiago papasquiaro", "guadalupe victoria"],
    "guanajuato": ["león", "irapuato", "celaya", "guanajuato", "salamanca", "silao", "san miguel de allende", "pénjamo", "valle de santiago", "salvatierra"],
    "guerrero": ["acapulco", "chilpancingo", "iguala", "taxco", "zihuatanejo", "tlapa", "chilapa", "ayutla de los libres", "tixtla", "huamuxtitlán"],
    "hidalgo": ["pachuca", "tulancingo", "tizayuca", "tula", "ixmiquilpan", "actopan", "tepeapulco", "huejutla de reyes", "zacualtipán", "molango"],
    "jalisco": ["guadalajara", "zapopan", "puerto vallarta", "tonalá", "tlaquepaque", "tlajomulco de zúñiga", "tequila", "lagos de moreno", "arandas", "cihuatlán"],
    "méxico": ["toluca", "metepec", "ecatepec", "nezahualcóyotl", "naucalpan", "tlalnepantla", "cuautitlán izcalli", "huixquilucan", "chalco", "texcoco"],
    "michoacán": ["morelia", "uruapan", "lázaro cárdenas", "zamora", "pátzcuaro", "zitácuaro", "los reyes", "jacona", "apatzingán", "tacámbaro"],
    "morelos": ["cuernavaca", "cuautla", "jiutepec", "temixco", "yautepec", "tlaltizapán", "ayala", "tlayacapan", "jojutla", "tepoztlán"],
    "nayarit": ["tepic", "bahía de banderas", "santiago ixcuintla", "acaponeta", "xalisco", "ruiz", "tecuala", "rosamorada", "tuxpan", "ahuacatlán"],
    "nuevo león": ["monterrey", "san pedro garza garcía", "guadalupe", "apodaca", "escobedo", "santa catarina", "santiago", "cadereyta jiménez", "lincoln", "garcía"],
    "oaxaca": ["oaxaca", "juchitán", "salina cruz", "tehuantepec", "huatulco", "tuxtepec", "pinotepa nacional", "tlacolula", "nochixtlán", "san pedro mixtepec"],
    "puebla": ["puebla", "tehuacán", "atlixco", "cholula", "huauchinango", "izúcar de matamoros", "teziutlán", "acatlán", "zacatlán", "xicotepec"],
    "querétaro": ["querétaro", "san juan del río", "el marqués", "corregidora", "amealco", "tequisquiapan", "cadereyta de montes", "ezequiel montes", "jalpan", "tolimán"],
    "quintana roo": ["cancún", "playa del carmen", "cozumel", "chetumal", "tulum", "bacalar", "isla mujeres", "puerto morelos", "felipe carrillo puerto", "lázaro cárdenas"],
    "san luis potosí": ["san luis potosí", "soledad de graciano sánchez", "matehuala", "ciudad valles", "tamazunchale", "río verde", "cerritos", "cedral", "xilitla", "charcas"],
    "sinaloa": ["culiacán", "mazatlán", "los mochis", "guasave", "navolato", "el fuerte", "salvador alvarado", "angostura", "escuinapa", "choix"],
    "sonora": ["hermosillo", "ciudad obregón", "nogales", "guaymas", "navojoa", "san luis río colorado", "caborca", "agua prieta", "cananea", "pitiquito"],
    "tabasco": ["villahermosa", "cárdenas", "comalcalco", "centla", "tenosique", "jalpa de méndez", "balancán", "huimanguillo", "jalapa", "paraíso"],
    "tamaulipas": ["ciudad victoria", "ciudad madero", "matamoros", "nuevo laredo", "reynosa", "tampico", "altamira", "mante", "san fernando", "valle hermoso"],
    "tlaxcala": ["tlaxcala", "huamantla", "apizaco", "zacatelco", "chiautempan", "calpulalpan", "panotla", "san pablo del monte", "santa cruz tlaxcala", "tequexquitla"],
    "veracruz": ["veracruz", "xalapa", "coatzacoalcos", "orizaba", "poza rica", "minatitlán", "córdoba", "tuxpan", "cosamaloapan", "papantla"],
    "yucatán": ["mérida", "progreso", "valladolid", "tekax", "tizimín", "umán", "motul", "temozón", "maxcanú", "ticul"],
    "zacatecas": ["zacatecas", "fresnillo", "jerez", "guadalupe", "sombrerete", "villanueva", "río grande", "pinos", "concepción del oro", "loreto"]
}

# Diccionario para convertir números escritos en palabras a su equivalente numérico
numero_palabras = {
    "uno": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
    "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10
}


# Función auxiliar para convertir palabras en números
def convertir_a_numero(token):
    # Si el token es un número en formato numérico
    if token.like_num:
        try:
            return int(token.text)
        except ValueError:
            return None
    # Si el token es una palabra que representa un número
    elif token.text.lower() in numero_palabras:
        return numero_palabras[token.text.lower()]
    else:
        return None


# Función para detectar la ubicación
# Función para detectar la ubicación
def detectar_ubicacion(texto):
    doc = nlp(texto.lower())

    pais = None
    estado = None
    ciudad = None

    for ent in doc.ents:
        if ent.label_ == "LOC":
            # Detectar el país en base a la entidad detectada
            if ent.text in ["méxico", "mexico", "guatemala", "honduras"]:
                pais = ent.text.capitalize()
            for estado_nombre, ciudades in estados_mexico.items():
                if estado_nombre in ent.text:
                    estado = estado_nombre.capitalize()
                    for ciudad_nombre in ciudades:
                        if ciudad_nombre in texto.lower():
                            ciudad = ciudad_nombre.capitalize()

    # Si se detecta un estado mexicano, el país se establece automáticamente como "México"
    if estado:
        pais = "México"

    return {
        "pais": pais,
        "estado": estado,
        "ciudad": ciudad
    }



# Función para extraer otras características
def extraer_caracteristicas(texto):
    doc = nlp(texto.lower())

    tipo_secuestro = None
    hubo_rescate = False
    numero_fallecidos = 0
    uso_violencia = False
    numero_secuestradores = 0
    nacionalidad_victima = None

    if "secuestro exprés" in texto:
        tipo_secuestro = "Secuestro Express"
    elif "secuestro virtual" in texto:
        tipo_secuestro = "Secuestro Virtual"
    elif "secuestro de migrantes" in texto or "migrantes" in texto:
        tipo_secuestro = "Secuestro de Migrantes"
    else:
        tipo_secuestro = "Desconocido"

    if "rescate" in texto or "fue liberado" in texto:
        hubo_rescate = True

    for token in doc:
        if token.lemma_ in ["fallecido", "muerto", "asesinado"]:
            numero_fallecidos += 1

    if "violencia" in texto or "arma" in texto:
        uso_violencia = True

    # Convertir el número de secuestradores
    for token in doc:
        numero = convertir_a_numero(token)
        if numero is not None:
            numero_secuestradores = numero

    if "de nacionalidad" in texto:
        nacionalidad_victima = texto.split("de nacionalidad")[1].split()[0]

    return {
        "tipo_secuestro": tipo_secuestro,
        "hubo_rescate": hubo_rescate,
        "numero_fallecidos": numero_fallecidos,
        "uso_violencia": uso_violencia,
        "numero_secuestradores": numero_secuestradores,
        "nacionalidad_victima": nacionalidad_victima
    }


# Función para analizar el texto de la noticia
def analizar_noticia(texto):
    ubicacion = detectar_ubicacion(texto)
    caracteristicas = extraer_caracteristicas(texto)

    return {
        "ubicacion": ubicacion,
        "caracteristicas": caracteristicas
    }


# --- ESPACIO PARA TU TEXTO DE NOTICIA ---
texto_noticia = """
Ciudad Victoria, Tamaulipas.- Dos personas acusadas por secuestrar a ocho migrantes centroamericanos recibieron una condena histórica de 454 años de prisión y una multa de más de 2 millones 500 mil pesos, informó el vocero de Seguridad de Tamaulipas, Jorge Cuéllar Montoya.
El vocero de Seguridad destacó que esta sentencia confirma el combate a la impunidad en el estado y el trabajo coordinado entre las instituciones de seguridad y procuración de justicia.
Cuéllar Montoya reiteró que como se ha demostrado en lo que va de la actual administración estatal, el respeto a los derechos de los migrantes que transitan por nuestra entidad es tarea prioritaria por lo que ningún agravio en su contra quedará impune. Explicó que la Fiscalía General de la República (FGR) a través de la Fiscalía Especializada de Control Regional, obtuvo del juez Décimo de Distrito en el Estado de Tamaulipas en el Sistema Inquisitivo Mixto, sentencia condenatoria en contra de Miguel Angel “G” y Marco Antonio “G”, por los delitos de Secuestro y Portación de Arma de Fuego de Uso Exclusivo del Ejército, Armada y Fuerza Aérea.
Recordó que ambos masculinos fueron detenidos en marzo del año 2015, a través de una denuncia ciudadana que reportó que en la Colonia Jardín 20 de Noviembre en Ciudad Madero, Tamaulipas, se encontraban personas armadas, trasladándose a dicho lugar elementos de la Secretaría de la Defensa Nacional.
Al arribar al inmueble denunciado, los elementos del ejército mexicano detuvieron a dos personas quienes portaban armas de fuego, además de que en el interior del inmueble, se encontraban privadas de su libertad ocho personas y un menor de edad originarios de Honduras, Guatemala y Salvador.
Por lo anterior, Miguel Angel “G” y Marco Antonio “G”, fueron puestos a disposición del Agente del Ministerio Publico de la Federación y luego de los procesos legales correspondientes, se dictó sentencia condenatoria de 454 años de prisión y multa de $ 2, 530,610.00 por los delitos antes mencionados.
"""

# Analizamos la noticia
resultado = analizar_noticia(texto_noticia)

# Mostramos el resultado
print("Ubicación Detectada:", resultado["ubicacion"])
print("Características Detectadas:", resultado["caracteristicas"])

