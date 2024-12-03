from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
import random
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
# Configurar las opciones de Chrome
opts = Options()
opts.add_argument(
    "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# Inicializar el driver de Chrome
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
#driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()))
# Navegar a la página web
driver.get('https://www.eluniversal.com.mx/buscador/?query=secuestro')
sleep(random.uniform(1, 3))

# Contador de noticias
contador_noticias = 0
max_noticias = 1000

while contador_noticias < max_noticias:
    # Encontrar los elementos de las noticias usando el XPATH proporcionado
    noticias = driver.find_elements(By.XPATH, '//*[@id="resultdata"]/div[@class="queryly_item_row"]/a')

    # Asegurarse de obtener los enlaces correctos
    links_noticias = []

    for tag_a in noticias:
        link = tag_a.get_attribute("href")
        if link:
            links_noticias.append(link)

    # Iterar sobre los enlaces de las noticias
    for link in links_noticias:
        if contador_noticias >= max_noticias:
            break
        try:
            driver.get(link)
            sleep(random.uniform(1, 3))  # Esperar un momento para que la página cargue

            # Intentar cerrar ventana emergente si aparece
            try:
                sleep(random.uniform(1, 3))
                cerrar_ventana = driver.find_element(By.XPATH, '//svg[contains(@width,"20")]')
                cerrar_ventana.click()
                sleep(random.uniform(1, 3))
            except:
                pass

            titulo = driver.find_element(By.XPATH, '//h1').text
            descripcion = driver.find_element(By.XPATH, '//h2').text
            texto = driver.find_element(By.XPATH, '//section').text

            # Eliminar el texto no deseado
            texto_no_deseado = "Únete a nuestro canal ¡EL UNIVERSAL ya está en Whatsapp!"
            if texto_no_deseado in texto:
                texto = texto.split(texto_no_deseado)[0]

            texto = texto.replace("PUBLICIDAD", "")

            # Incrementar el contador de noticias
            contador_noticias += 1

            # Imprimir los resultados junto con la URL y el número de noticia
            print("Título:", titulo)
            print("Descripción:", descripcion)
            print("Noticia:", texto)
            print("URL:", link)
            print(f"Noticia número: {contador_noticias}")
            print("-" * 50)

            driver.back()
            sleep(random.uniform(1, 3))  # Esperar un momento para que la página anterior cargue
        except Exception as e:
            print(e)
            driver.back()
            sleep(random.uniform(1, 3))  # Esperar un momento para que la página anterior cargue

    # Manejar el mensaje de cookies si está presente
    try:
        driver.back()
        cookies_message = driver.find_element(By.CLASS_NAME, 'cookies-message')
        if cookies_message.is_displayed():
            close_button = cookies_message.find_element(By.XPATH, './/button')
            close_button.click()
            sleep(random.uniform(1, 3))
    except Exception as e:
        pass  # Si no se encuentra el mensaje de cookies, continuar

    # Intentar ir a la siguiente página
    try:
        sleep(random.uniform(1, 3))  # Esperar un momento para que la página cargue completamente
        boton_siguiente = driver.find_element(By.XPATH,
                                              '//a[contains(.,"Siguiente")]')
        boton_siguiente.click()
        sleep(random.uniform(1, 3))
    except Exception as e:
        print(e)
        break

# Cerrar el driver
driver.quit()

#//svg[contains(@width,'20')]
#//*[@id="resultdata"]/a
#//*[@id="piano-id-iCCPe"]    iframe
#//b[contains(.,'Inicia sesión aquí')] //*[@id="cont-acceso"]/p[1]/input  boton de iniciar sesion despues de que aparece el iframe
#//input[contains(@placeholder,'Correo electrónico')]
#//input[contains(@placeholder,'Contraseña')]
#//input[contains(@placeholder,'Contraseña')]
#//t[contains(.,'Iniciar sesión')]