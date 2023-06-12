import os
import zipfile
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import xlsxwriter


def read_plv_file(file_path):
    data = []
    with open(file_path, 'r') as file:
        for i, line in enumerate(file):
            if i < 3:
                continue
            line = line.strip()
            if line:
                columns = line.split()
                data.append(columns)
    return data


def process_plv_files(file_paths):
    data = []
    for file_path in file_paths:
        file_data = read_plv_file(file_path)
        data.extend(file_data)
    return data


def obter_dados_rio_janeiro(inicio, fim):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": "", # Altere para o diretório desejado para download
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.set_window_size(1920, 1080)

    for ano in range(inicio, fim + 1):
        driver.get("http://www.sistema-alerta-rio.com.br/dados-meteorologicos/download/dados-pluviometricos")


        iframe_element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".iframe-class")))

        driver.switch_to.frame(iframe_element)


        select_ano = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "id_1-choice")))


        for i in range(1, 34):
            select = Select(driver.find_element(By.ID, f"id_{i}-choice"))
            select.select_by_value(str(ano))


        driver.find_element(By.ID, "all_check").click()
        driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Download']").click()


        time.sleep(65)

        # Altere o caminho do arquivo ZIP para o diretório desejado
        zip_file_path = "DadosPluviometricos.zip"


        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(f"{ano}") # Altere para o diretório desejado para extração


        os.remove(zip_file_path)


        pasta_ano = f"{ano}" # Altere para o diretório desejado para extração
        if not os.path.exists(pasta_ano):
            os.makedirs(pasta_ano)

        dados_ano = pd.DataFrame()
        txt_files = [f for f in os.listdir(pasta_ano) if f.endswith('.txt')]
        for txt_file in txt_files:
            try:
                txt_file_path = os.path.join(pasta_ano, txt_file)
                dados_estacao = pd.DataFrame(process_plv_files([txt_file_path]))
                dados_estacao["localidade"] = txt_file.split("_")[0]
                dados_ano = pd.concat([dados_ano, dados_estacao], axis=0, ignore_index=True)
                print(f"Dados obtidos para o ano {ano} e arquivo {txt_file}.")
            except pd.errors.EmptyDataError:
                print(f"Arquivo {txt_file} está vazio e será desconsiderado.")
            except Exception as e:
                print(f"Erro ao obter dados para o ano {ano} e arquivo {txt_file}.")
                print(str(e))

        dados_ano.to_csv(os.path.join(pasta_ano, f"dados_precipitacao_{ano}.csv"), index=False)

        print(f"Tabela do ano {ano} criada.")

    driver.quit()

    return "D:\\Documentos D\\dacri\\PluvRio"


inicio_ano = 2000
fim_ano = 2023


pasta_dados_rio_janeiro = obter_dados_rio_janeiro(inicio_ano, fim_ano)


if pasta_dados_rio_janeiro:
    print("Pasta com os arquivos:", pasta_dados_rio_janeiro)
else:
    print("Falha ao obter os dados do Rio de Janeiro.")
