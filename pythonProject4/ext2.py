from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
import random
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager


# Configurar las opciones de Chrome
opts = Options()
opts.add_argument(
    "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# Inicializar el driver de firefox
driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()))
    #driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)

# Navegar a la página web principal
driver.get('https://www.eluniversal.com.mx/')
sleep(10)  # Esperar 10 segundos para permitir que el anuncio se quite

# Intentar cerrar anuncios si están presentes, de lo contrario, proceder con el login
try:
    anuncio = driver.find_element(By.XPATH,
                                  '//*[@id="some-ad-element"]')  # Cambia el XPATH a uno correcto si es necesario
    if anuncio.is_displayed():
        print("Anuncio encontrado, terminando el programa.")
        driver.quit()
        exit()
except:
    pass

# Buscar y hacer clic en el botón para iniciar sesión
try:
    boton_login = driver.find_element(By.XPATH, '//input[contains(@value,"Iniciar Sesión")]')
    boton_login.click()
    sleep(random.uniform(1, 3))

except Exception as e:
    print("Error al intentar encontrar el botón de login:", e)
    driver.quit()
    exit()

# Buscar el frame correcto cuyo id contiene 'piano-id'
try:
    login_frame = driver.find_element(By.XPATH, '//iframe[contains(@id, "piano-id")]')
    driver.switch_to.frame(login_frame)
except Exception as e:
    print("Error al intentar cambiar al frame de login:", e)
    driver.quit()
    exit()

# Asegurarse de que el campo de correo electrónico esté presente antes de interactuar
try:
    campo_email = driver.find_element(By.XPATH, '//input[contains(@placeholder,"Correo electrónico")]')
    campo_email.send_keys('alexx_hern@outlook.com')
    sleep(random.uniform(1, 3))
except Exception as e:
    print("Error al intentar ingresar el correo electrónico:", e)
    driver.quit()
    exit()

# Asegurarse de que el campo de contraseña esté presente antes de interactuar
try:
    campo_password = driver.find_element(By.XPATH, '//input[contains(@type,"password")]')
    campo_password.send_keys('Soccer.8a')
    sleep(random.uniform(1, 3))
except Exception as e:
    print("Error al intentar ingresar la contraseña:", e)
    driver.quit()
    exit()

# Asegurarse de que el botón de login esté presente antes de interactuar
try:
    boton_submit = driver.find_element(By.XPATH, '//*[@id="cont-acceso"]/p[3]/button')
    boton_submit.click()
    sleep(random.uniform(1, 3))
except Exception as e:
    print("Error al intentar hacer clic en el botón de login:", e)
    driver.quit()
    exit()

# Cambiar de nuevo al contexto principal
driver.switch_to.default_content()

# Buscar el campo de búsqueda y realizar la búsqueda
try:
    campo_busqueda = driver.find_element(By.XPATH, '//*[@id="header-search-input"]')
    campo_busqueda.send_keys('secuestro')
    campo_busqueda.submit()
    sleep(random.uniform(1, 3))
except Exception as e:
    print("Error al intentar realizar la búsqueda:", e)
    driver.quit()
    exit()

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
            titulo = driver.find_element(By.XPATH, '//h1').text
            descripcion = driver.find_element(By.XPATH, '//h2').text
            texto = driver.find_element(By.XPATH, '//section').text

            # Eliminar el texto no deseado
            texto_no_deseado = "Únete a nuestro canal ¡EL UNIVERSAL ya está en Whatsapp!"
            if texto_no_deseado in texto:
                texto = texto.split(texto_no_deseado)[0]

            texto = texto.replace("PUBLICIDAD", "")

            # Imprimir los resultados junto con la URL
            print("Título:", titulo)
            print("Descripción:", descripcion)
            print("Noticia:", texto)
            print("URL:", link)
            print("-" * 50)
            contador_noticias += 1
            driver.back()
            sleep(random.uniform(1, 3))  # Esperar un momento para que la página anterior cargue
        except Exception as e:
            print(e)
            driver.back()
            sleep(random.uniform(1, 3))  # Esperar un momento para que la página anterior cargue

    # Manejar el mensaje de cookies si está presente
    try:
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
                                              '//a[contains(@class,"next_btn") and contains(text(),"Siguiente")]')
        boton_siguiente.click()
        sleep(random.uniform(1, 3))
    except Exception as e:
        print(e)
        break

# Cerrar el driver
driver.quit()
