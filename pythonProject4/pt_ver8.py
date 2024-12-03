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
import mysql.connector

# Configurar las opciones de Chrome
opts = Options()
opts.add_argument(
    "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
opts.page_load_strategy = 'eager'
opts.add_argument('--disable-blink-features=AutomationControlled')

# Inicializar el driver de Chrome
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
driver.set_page_load_timeout(60)

# Configurar la conexión a la base de datos
db_config = {
    'user': 'root',
    'password': 'Soccer.8a',
    'host': '127.0.0.1',
    'database': 'noticias',
    'raise_on_warnings': True
}

def check_url_exists(cursor, url):
    query = "SELECT 1 FROM extracciones WHERE url = %s LIMIT 1"
    cursor.execute(query, (url,))
    return cursor.fetchone() is not None

try:
    # Conectar a la base de datos
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # Navegar a la página web principal
    driver.get('https://www.eluniversal.com.mx/')
    sleep(10)

    # Intentar cerrar anuncios si están presentes
    try:
        anuncio = driver.find_element(By.XPATH, '//*[@id="some-ad-element"]')
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
        sleep(3)
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
        sleep(4)
        campo_email = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/app-main/app-widget/screen-layout/main/current-screen/div/screen-login/div[4]/p[1]/input')))
        campo_email.click()
        campo_email.send_keys('alexx_hern@outlook.com')
        sleep(random.uniform(1, 3))
    except Exception as e:
        print("Error al intentar ingresar el correo electrónico:", e)
        driver.quit()
        exit()

    # Asegurarse de que el campo de contraseña esté presente antes de interactuar
    try:
        campo_password = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/app-main/app-widget/screen-layout/main/current-screen/div/screen-login/div[4]/p[2]/input')))
        campo_password.click()
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
    sleep(10)
    # Intentar la búsqueda varias veces si es necesario
    for intento in range(2):  # Intentar hasta 2 veces
        try:
            sleep(random.uniform(3, 5))
            campo_busqueda = driver.find_element(By.XPATH, '//input[contains(@class,"buscadoreventod ml-2 py-2")]')
            campo_busqueda.click()
            sleep(random.uniform(5, 6))
            campo_busqueda.clear()
            campo_busqueda.send_keys('secuestro')
            sleep(random.uniform(5, 6))
            campo_busqueda.send_keys(Keys.RETURN)
            sleep(random.uniform(5, 6))

            WebDriverWait(driver, 10).until(EC.url_contains('query=secuestro'))
            sleep(random.uniform(5, 6))

            if 'query=secuestro' in driver.current_url:
                print("Búsqueda realizada correctamente en el intento", intento + 1)
                break
        except Exception as e:
            print(f"Error al intentar realizar la búsqueda en el intento {intento + 1}:", e)
            if intento == 1:
                driver.quit()
                exit()

    contador_noticias = 0
    max_noticias = 15000
    sleep(random.uniform(10, 11))

    pagina = 1  # Agregamos un contador de páginas

    while contador_noticias < max_noticias:
        try:
            noticias = driver.find_elements(By.XPATH, '//*[@id="resultdata"]/div[@class="queryly_item_row"]/a')
            links_noticias = [tag_a.get_attribute("href") for tag_a in noticias if tag_a.get_attribute("href")]

            if pagina > 1:
                if links_noticias and check_url_exists(cursor, links_noticias[0]):
                    print(f"La URL {links_noticias[0]} ya está en la base de datos, pasando a la siguiente página.")
                    # Intentar ir a la siguiente página
                    try:
                        sleep(random.uniform(1, 3))
                        try:
                            boton_siguiente = driver.find_element(By.XPATH,
                                                                  '//a[@class="next_btn" and contains(text(),"Siguiente")]')
                        except:
                            boton_siguiente = driver.find_element(By.XPATH,
                                                                  '/html/body/div[1]/div[1]/div[2]/div[1]/div/div/div[2]/a[1]')
                        boton_siguiente.click()
                        pagina += 1
                        sleep(random.uniform(1, 3))
                        continue
                    except Exception as e:
                        print("Error al intentar hacer clic en el botón siguiente:", e)
                        sleep(10)
                        try:
                            driver.back()
                            sleep(3)
                            print(f"URL actual después de volver atrás: {driver.current_url}")
                            try:
                                boton_siguiente = driver.find_element(By.XPATH,
                                                                      '//a[@class="next_btn" and contains(text(),"Siguiente")]')
                            except:
                                boton_siguiente = driver.find_element(By.XPATH,
                                                                      '/html/body/div[1]/div[1]/div[2]/div[1]/div/div/div[2]/a[1]')
                            boton_siguiente.click()
                            pagina += 1
                            continue
                        except Exception as e:
                            print("No se pudo hacer clic en el botón 'Siguiente' después de esperar:", e)
                            break

            for index, link in enumerate(links_noticias):
                if contador_noticias >= max_noticias:
                    break
                try:
                    driver.get(link)
                    sleep(random.uniform(3, 5))
                    titulo = driver.find_element(By.XPATH, '//h1').text
                    descripcion = driver.find_element(By.XPATH, '//h2').text
                    sleep(3)
                    texto = driver.find_element(By.XPATH, '//section').text

                    texto_no_deseado = "Únete a nuestro canal ¡EL UNIVERSAL ya está en Whatsapp!"
                    if texto_no_deseado in texto:
                        texto = texto.split(texto_no_deseado)[0]

                    texto = texto.replace("PUBLICIDAD", "")

                    for fragmento in ["Lee también", "Alerta vial"]:
                        if fragmento in texto:
                            texto = texto.split(fragmento)[0]

                    print("Título:", titulo)
                    print("Descripción:", descripcion)
                    print("Noticia:", texto)
                    print("URL:", link)
                    print(f"Noticia número: {contador_noticias}")
                    print("-" * 50)
                    contador_noticias += 1

                    cursor.execute(
                        "INSERT INTO extracciones (titulo, descripcion, noticia, url) VALUES (%s, %s, %s, %s)",
                        (titulo, descripcion, texto, link)
                    )
                    conn.commit()

                    # Regresar al contenedor de noticias
                    driver.back()
                    sleep(random.uniform(3, 5))
                    print(f"URL actual después de volver atrás: {driver.current_url}")
                except Exception as e:
                    print("Error al intentar hacer la extracción:", e)
                    try:
                        driver.back()
                        sleep(random.uniform(3, 5))
                        print(f"URL actual después de volver atrás: {driver.current_url}")
                    except Exception as e2:
                        print("Error al intentar volver atrás:", e2)
                    sleep(random.uniform(1, 3))

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
                pass

            # Mostrar la URL actual antes de intentar ir a la siguiente página
            print(f"URL actual antes de intentar hacer clic en el botón 'Siguiente': {driver.current_url}")

            # Intentar ir a la siguiente página
            try:
                sleep(random.uniform(1, 3))  # Esperar un momento para que la página cargue completamente
                try:
                    boton_siguiente = driver.find_element(By.XPATH,
                                                          '//a[@class="next_btn" and contains(text(),"Siguiente")]')
                except:
                    boton_siguiente = driver.find_element(By.XPATH,
                                                          '/html/body/div[1]/div[1]/div[2]/div[1]/div/div/div[2]/a[1]')
                boton_siguiente.click()
                pagina += 1  # Incrementar el contador de páginas
                sleep(random.uniform(1, 3))
            except Exception as e:
                print("Error al intentar hacer clic en el botón siguiente:", e)
                sleep(10)  # Esperar 10 segundos para dar tiempo a que desaparezca cualquier anuncio
                try:
                    driver.back()  # Volver atrás para asegurarnos de que estamos en la página con el botón "Siguiente"
                    sleep(3)
                    print(f"URL actual después de volver atrás: {driver.current_url}")
                    try:
                        boton_siguiente = driver.find_element(By.XPATH, '//a[@class="next_btn" and contains(text(),"Siguiente")]')
                    except:
                        boton_siguiente = driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[2]/div[1]/div/div/div[2]/a[1]')
                    boton_siguiente.click()
                    pagina += 1  # Incrementar el contador de páginas
                except Exception as e:
                    print("No se pudo hacer clic en el botón 'Siguiente' después de esperar:", e)
                    break
        except Exception as e:
            print(f"Error al intentar procesar noticias: {e}")
            break

finally:
    # Cerrar el driver y la conexión a la base de datos
    driver.quit()
    cursor.close()
    conn.close()

#//*[@id="webpushBanner-eluniversal"]/div/div/div[4]/button