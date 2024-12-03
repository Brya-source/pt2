import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import mysql.connector
import time
from time import sleep
import random
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager


opts = Options()
opts.add_argument(
    "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
opts.page_load_strategy = 'eager'
opts.add_argument('--disable-blink-features=AutomationControlled')


driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()))
#driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
driver.set_page_load_timeout(30)


db_config = {
    'user': 'root',
    'password': 'Soccer.8a',
    'host': '127.0.0.1',
    'database': 'noticias3',
    'raise_on_warnings': True
}


def cerrar_mensaje_cookies(driver):
    try:
        boton_cookies = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'btnAceptarCookies'))
        )
        boton_cookies.click()
        print("Mensaje de cookies cerrado.")
    except Exception as e:
        print(f"No se pudo cerrar el mensaje de cookkies: {e}")


def extraer_noticia(driver, link, cursor, conn):
    original_window = driver.current_window_handle  # Guardar la ventana principal

    try:

        driver.execute_script("window.open(arguments[0]);", link)
        driver.switch_to.window(driver.window_handles[-1])
        driver.set_page_load_timeout(30)


        time.sleep(4)
        sleep(5)


        titulo = driver.find_element(By.XPATH, '//h1').text
        descripcion = driver.find_element(By.XPATH, '//h2').text
        sleep(3)
        texto = driver.find_element(By.XPATH, '//section').text
        fecha = driver.find_element(By.XPATH, '//span[contains(@class, "sc__author--date")]').text
        try:
            autor = driver.find_element(By.XPATH, '//div[@class="sc__author-nota font-bold text-lg"]').text
        except NoSuchElementException:
            autor = "Autor desconocido"


        texto_no_deseado = "Únete a nuestro canal ¡EL UNIVERSAL ya está en Whatsapp!"
        if texto_no_deseado in texto:
            texto = texto.split(texto_no_deseado)[0]

        patrones_no_deseados = ["Lee también", "Lea también", "Leer también", "También lee"]
        for patron in patrones_no_deseados:
            while patron in texto:
                index_inicio = texto.find(patron)
                index_final = texto.find("\n", index_inicio)
                if index_final != -1:
                    texto = texto[:index_inicio] + texto[index_final:]


        print(f"Título: {titulo}")
        print(f"Descripción: {descripcion}")
        print(f"Fecha: {fecha}")
        print(f"Noticia: {texto}")
        print(f"Autor: {autor}")
        print(f"URL: {link}")
        print("-" * 50)


        cursor.execute(
            "INSERT INTO extracciones (titulo, descripcion, noticia, autor, fecha, url) VALUES (%s, %s, %s, %s, %s, %s)",
            (titulo, descripcion, texto, autor, fecha, link)
        )
        conn.commit()

    except (TimeoutException, NoSuchElementException, WebDriverException) as e:
        print(f"Error durante la extracción: {e}")
        cursor.execute("INSERT INTO extracciones (url) VALUES (%s)", (link,))
        conn.commit()
        print("Saltando, no fue posible extraer la noticia. Pasando a la siguiente.")

    finally:

        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
            driver.close()  # Cerrar la pestaña actual de la noticia
        driver.switch_to.window(original_window)  # Regresar a la ventana principal
        print("Pestaña cerrada y regresando a la ventana principal.")

        sleep(5)


def extraer_noticia_con_timeout(driver, link, cursor, conn, timeout=45):
    thread = threading.Thread(target=extraer_noticia, args=(driver, link, cursor, conn))
    thread.start()

    # Esperar a que el hilo termine dentro del tiempo límite
    thread.join(timeout)

    # Si el hilo sigue activo después del tiempo límite
    if thread.is_alive():
        print("Timeout: la extracción de la noticia tardó demasiado, saltando a la siguiente.")

        # Cerrar la pestaña en la que la noticia estaba siendo procesada (si es posible)
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
            driver.close()

        # Regresar a la ventana principal
        driver.switch_to.window(driver.window_handles[0])
        cursor.execute("INSERT INTO extracciones (url) VALUES (%s)", (link,))
        conn.commit()
        sleep(2)

        print(f"Regresando a la ventana principal.")
    else:
        print(f"La extracción de la noticia {link} finalizó correctamente dentro del tiempo.")

def check_url_exists(cursor, url):
    query = "SELECT 1 FROM extracciones WHERE url = %s LIMIT 1"
    cursor.execute(query, (url,))
    return cursor.fetchone() is not None
# Función para cerrar popups
def cerrar_popup(driver):
    try:
        # Intentar cerrar el popup si aparece
        time.sleep(3)
        popup = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div#webpushBanner-eluniversal'))
        )
        boton_no_gracias = popup.find_element(By.XPATH, '//*[@id="webpushBanner-eluniversal"]/div/div/div[4]/button')
        if boton_no_gracias.is_displayed():
            boton_no_gracias.click()
            print("Popup 'No, gracias' cerrado exitosamente.")
    except Exception as e:
        print(f"No se pudo cerrar el popup 'No, gracias': {e}")

try:
    # Conectar a la base de datos
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # Navegar a la página web principal
    driver.get('https://www.eluniversal.com.mx/buscador/?query=secuestro')
    sleep(10)
    sleep(10)

    cerrar_popup(driver)
    cerrar_mensaje_cookies(driver)


    cerrar_mensaje_cookies(driver)


    cerrar_popup(driver)


    for intento in range(2):  # Intentar hasta 2 veces
        try:
            sleep(10)

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
    sleep(10)
    sleep(10)
    pagina = 1  # Agregamos un contador de páginas

    while contador_noticias < max_noticias:
        try:
            sleep(10)
            noticias = driver.find_elements(By.XPATH, '//*[@id="resultdata"]/div[@class="queryly_item_row"]/a')
            links_noticias = [tag_a.get_attribute("href") for tag_a in noticias if tag_a.get_attribute("href")]
            if pagina > 1:
                urls_nuevas = [url for url in links_noticias if not check_url_exists(cursor, url)]

                if not urls_nuevas:
                    print("Todas las URLs en esta página ya están en la base de datos. Siguiente.")
                    try:
                        sleep(random.uniform(1, 3))
                        try:
                            sleep(3)
                            boton_siguiente = driver.find_element(By.XPATH,
                                                                  '//a[@class="next_btn" and contains(text(),"Siguiente")]')
                        except:
                            boton_siguiente = driver.find_element(By.XPATH,
                                                                  '/html/body/div[1]/div[1]/div[2]/div[1]/div/div/div[2]/a[1]')
                        #desplazar_a_elemento(driver, boton_siguiente)
                        boton_siguiente.click()
                        pagina += 1
                        sleep(random.uniform(1, 3))
                        continue
                    except Exception as e:
                        print("Error al intentar hacer clic en el botón siguiente:", e)
                        sleep(10)
                        try:
                            driver.get('https://www.eluniversal.com.mx/buscador/?query=secuestro')
                            sleep(3)
                            continue
                        except Exception as e:
                            print("No se pudo hacer clic en el botón 'Siguiente' después de esperar:", e)
                            break
            for link in links_noticias:
                if contador_noticias >= max_noticias:
                    break
                if check_url_exists(cursor, link):
                    print(f"La URL {link} ya está en la base de datos")
                    continue

                # Llamar a la función para extraer la noticia con timeout
                extraer_noticia_con_timeout(driver, link, cursor, conn, timeout=60)
                contador_noticias += 1

        except Exception as e:
            print(f"Error durante la obtención de noticias: {e}")
            break

        # Intentar ir a la siguiente página
        try:
            sleep(10)
            sleep(10)
            sleep(random.uniform(1, 3))  # Esperar un momento para que la página cargue completamente
            try:
                boton_siguiente = driver.find_element(By.XPATH, '//a[@class="next_btn" and contains(text(),"Siguiente")]')
            except:
                boton_siguiente = driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[2]/div[1]/div/div/div[2]/a[1]')
            #desplazar_a_elemento(driver, boton_siguiente)
            boton_siguiente.click()
            pagina += 1  # Incrementar el contador de páginas
            sleep(random.uniform(1, 3))
            sleep(10)
        except Exception as e:
            print("Error al intentar hacer clic en el botón siguiente:", e)
            sleep(10)  # Esperar 10 segundos para dar tiempo a que desaparezca cualquier anuncio
            try:
                driver.get('https://www.eluniversal.com.mx/buscador/?query=secuestro')
                sleep(3)
                sleep(10)
            except Exception as e:
                print("No se pudo hacer clic en el botón 'Siguiente' después de esperar:", e)
                break

finally:
    # Cerrar el driver y la conexión a la base de datos
    driver.quit()
    cursor.close()
    conn.close()
