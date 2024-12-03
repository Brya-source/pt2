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
# Configurar las opciones de Firefox
opts = Options()
opts.add_argument(
    "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# Inicializar el driver de Firefox
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)

try:
    # Navegar a la página web principal
    driver.get('https://www.eluniversal.com.mx/')
    sleep(10)  # Esperar 10 segundos para permitir que el anuncio se quite

    # Intentar cerrar anuncios si están presentes
    try:
        anuncio = driver.find_element(By.XPATH, '//*[@id="some-ad-element"]')  # Cambia el XPATH a uno correcto si es necesario
        if anuncio.is_displayed():
            print("Anuncio encontrado, terminando el programa.")
            driver.quit()
            exit()
    except:
        pass

    # Intentar cerrar el mensaje de cookies si está presente
    try:
        boton_cookies = driver.find_element(By.ID, 'btnAceptarCookies')
        if boton_cookies.is_displayed():
            boton_cookies.click()
            print("Mensaje de cookies cerrado al principio.")
            sleep(3)
    except Exception as e:
        print("No se encontró el mensaje de cookies o hubo un error al cerrarlo al principio:", e)
        pass

    # Intentar cerrar la publicidad en la parte inferior si está presente
    try:
        iframe_publicidad = driver.find_element(By.XPATH, '//iframe[contains(@id, "google_ads_iframe")]')
        driver.switch_to.frame(iframe_publicidad)
        boton_cerrar_publicidad = driver.find_element(By.XPATH, '//*[@id="gpt_unit_178068052_close"]')
        if boton_cerrar_publicidad.is_displayed():
            boton_cerrar_publicidad.click()
            print("Publicidad cerrada al principio.")
            sleep(3)
        driver.switch_to.default_content()
    except Exception as e:
        print("No se encontró la publicidad o hubo un error al cerrarla al principio:", e)
        driver.switch_to.default_content()
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

    # Esperar a que el frame de inicio de sesión esté presente y cambiar al frame correcto
    try:
        WebDriverWait(driver, 10).until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//iframe[contains(@src, "login")]')))
    except Exception as e:
        print("Error al intentar cambiar al frame de login:", e)
        driver.quit()
        exit()

    # Asegurarse de que el campo de correo electrónico esté presente antes de interactuar
    try:
        campo_email = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/app-main/app-widget/screen-layout/main/current-screen/div/screen-login/div[4]/p[1]/input')))
        campo_email.click()  # Hacer clic en el campo de correo electrónico para enfocarlo
        campo_email.send_keys('alexx_hern@outlook.com')
        sleep(random.uniform(1, 3))
    except Exception as e:
        print("Error al intentar ingresar el correo electrónico:", e)
        driver.quit()
        exit()

    # Asegurarse de que el campo de contraseña esté presente antes de interactuar
    try:
        campo_password = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/app-main/app-widget/screen-layout/main/current-screen/div/screen-login/div[4]/p[2]/input')))
        campo_password.click()  # Hacer clic en el campo de contraseña para enfocarlo
        campo_password.send_keys('Soccer.8a')
        sleep(random.uniform(1, 3))
    except Exception as e:
        print("Error al intentar ingresar la contraseña:", e)
        driver.quit()
        exit()

    # Asegurarse de que el botón de login esté presente antes de interactuar
    try:
        boton_submit = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH,
                                                                                       '/html/body/app-main/app-widget/screen-layout/main/current-screen/div/screen-login/div[4]/p[3]/button')))
        boton_submit.click()
        sleep(random.uniform(1, 3))
    except Exception as e:
        print("Error al intentar hacer clic en el botón de login:", e)
        driver.quit()
        exit()

    # Cambiar de nuevo al contexto principal
    driver.switch_to.default_content()
    sleep(random.uniform(3, 5))

    # Intentar la búsqueda varias veces si es necesario
    for intento in range(2):  # Intentar hasta 2 veces
        try:
            sleep(random.uniform(3, 5))
            campo_busqueda = driver.find_element(By.XPATH, '//input[contains(@class,"buscadoreventod ml-2 py-2")]')
            campo_busqueda.click()
            sleep(random.uniform(5, 6))
            campo_busqueda.clear()  # Limpiar el campo antes de escribir
            campo_busqueda.send_keys('secuestro')
            sleep(random.uniform(5, 6))
            campo_busqueda.send_keys(Keys.RETURN)
            sleep(random.uniform(5, 6))

            # Esperar hasta que la URL cambie después de la búsqueda
            WebDriverWait(driver, 10).until(EC.url_contains('query=secuestro'))
            sleep(random.uniform(5, 6))

            # Verificar la URL actual
            if 'query=secuestro' in driver.current_url:
                print("Búsqueda realizada correctamente en el intento", intento + 1)
                break
        except Exception as e:
            print(f"Error al intentar realizar la búsqueda en el intento {intento + 1}:", e)
            if intento == 1:  # Si es el último intento, cerrar el navegador
                driver.quit()
                exit()

    # Contador de noticias
    contador_noticias = 0
    max_noticias = 45  # Solo para hacer pruebas
    sleep(random.uniform(10, 11))
    while contador_noticias < max_noticias:
        # Encontrar los elementos de las noticias usando el XPATH proporcionado
        try:
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
                    driver.set_page_load_timeout(30)  # Establecer tiempo de espera de carga de página a 60 segundos
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
                    print(f"Noticia número: {contador_noticias}")
                    print("-" * 50)
                    contador_noticias += 1
                    driver.back()
                    sleep(random.uniform(1, 3))  # Esperar un momento para que la página anterior cargue
                except Exception as e:
                    print("Error al intentar hacer la extracción:", e)
                    try:
                        driver.back()
                    except Exception as e2:
                        print("Error al intentar volver atrás:", e2)
                    sleep(random.uniform(1, 3))  # Esperar un momento para que la página anterior cargue

            # Verificar si estamos en la página que contiene 'query=secuestro' en la URL
            if 'query=secuestro' in driver.current_url:
                # Manejar el mensaje de cookies si está presente
                try:
                    cookies_message = driver.find_element(By.CLASS_NAME, 'cookies-message')
                    if cookies_message.is_displayed():
                        close_button = cookies_message.find_element(By.XPATH, './/button')
                        close_button.click()
                        print("Mensaje de cookies cerrado antes del botón 'Siguiente'.")
                        sleep(random.uniform(1, 3))
                except Exception as e:
                    print("No se encontró el mensaje de cookies o hubo un error al cerrarlo antes del botón 'Siguiente':", e)
                    pass  # Si no se encuentra el mensaje de cookies, continuar

                # Intentar cerrar la publicidad en la parte inferior si está presente
                try:
                    iframe_publicidad = driver.find_element(By.XPATH, '//iframe[contains(@id, "google_ads_iframe")]')
                    driver.switch_to.frame(iframe_publicidad)
                    boton_cerrar_publicidad = driver.find_element(By.XPATH, '//*[@id="gpt_unit_178068052_close"]')
                    if boton_cerrar_publicidad.is_displayed():
                        boton_cerrar_publicidad.click()
                        print("Publicidad cerrada antes del botón 'Siguiente'.")
                        sleep(3)
                    driver.switch_to.default_content()
                except Exception as e:
                    print("No se encontró la publicidad o hubo un error al cerrarla antes del botón 'Siguiente':", e)
                    driver.switch_to.default_content()
                    pass

                # Mostrar la URL actual antes de intentar ir a la siguiente página
                print(f"URL actual antes de intentar hacer clic en el botón 'Siguiente': {driver.current_url}")

                # Intentar ir a la siguiente página
                try:
                    sleep(random.uniform(3, 5))  # Esperar un momento para que la página cargue completamente
                    try:
                        boton_siguiente = driver.find_element(By.XPATH, '//a[contains(@class,"next_btn") and contains(text(),"Siguiente")]')
                    except:
                        boton_siguiente = driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[2]/div[1]/div/div/div[2]/a[1]')
                    boton_siguiente.click()
                    sleep(random.uniform(3, 5))
                except Exception as e:
                    print("Error al intentar hacer clic en el botón siguiente:", e)
                    break
            else:
                print("No estamos en la página esperada. Intentando volver atrás.")
                driver.back()
                sleep(random.uniform(1, 3))
        except Exception as e:
            print(f"Error al intentar procesar noticias: {e}")
            break

finally:
    # Cerrar el driver
    driver.quit()

#/html/body/div[1]/div[1]/div[2]/div[1]/div/div/div[2]/a[1]
#/html/body/div[1]/div[1]/div[2]/div[1]/div/div/div[2]/a[1]
#/html/body/div[1]/div[1]/div[2]/div[1]/div/div/div[2]/a[1]