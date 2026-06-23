import os
import time
import glob
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def baixar_relatorio():
    print("Iniciando o robô de extração do GETS...")
    
    # Garante a criação do caminho absoluto da pasta
    pasta_planilhas = os.path.abspath(os.path.join(os.getcwd(), "planilhas_gets"))
    os.makedirs(pasta_planilhas, exist_ok=True)
    
    chrome_options = Options()
    chrome_options.add_argument("--headless=new") # Força a nova engine headless do Chrome
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    prefs = {
        "download.default_directory": pasta_planilhas,
        "download.prompt_for_download": False,
        "directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    driver = webdriver.Chrome(options=chrome_options)
    
    # COMANDO CRÍTICO: Força o Chrome Headless no Linux a permitir downloads
    driver.execute_cdp_cmd("Page.setDownloadBehavior", {
        "behavior": "allow",
        "downloadPath": pasta_planilhas
    })
    
    wait = WebDriverWait(driver, 20)

    try:
        print("Acessando página de login...")
        driver.get("https://gets.ceb.unicamp.br/nec/view/inicio/index.jsf")
        
        usuario = os.environ.get('GETS_USER') 
        senha = os.environ.get('GETS_PASS')

        wait.until(EC.presence_of_element_located((By.NAME, "j_username"))).send_keys(usuario)
        driver.find_element(By.NAME, "j_password").send_keys(senha)
        driver.find_element(By.XPATH, "//input[@value='Entrar']").click()
        time.sleep(5) 
        
        print("Navegando para o relatório de agendamentos...")
        driver.get("https://gets.ceb.unicamp.br/nec/view/formrelatorios/agendamentos.jsf")
        time.sleep(3)

        print("Limpando os campos de data...")
        driver.execute_script("document.getElementById('fm1:j_idt50_input').value = '';")
        driver.execute_script("document.getElementById('fm1:j_idt53_input').value = '';")
        time.sleep(1)
        
        print("Clicando em Gerar Planilha...")
        botao_gerar = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Gerar Planilha']/parent::button | //span[text()='Gerar Planilha']")))
        botao_gerar.click()

        print("Aguardando a conclusão do download...")
        # Loop de 15 segundos checando se o arquivo de fato surgiu na pasta
        for i in range(15):
            time.sleep(1)
            arquivos = glob.glob(os.path.join(pasta_planilhas, "*.xlsx"))
            if arquivos and not any(f.endswith('.crdownload') for f in arquivos):
                break

        arquivos_baixados = glob.glob(os.path.join(pasta_planilhas, "*.xlsx"))
        if arquivos_baixados:
            arquivo_final = max(arquivos_baixados, key=os.path.getctime)
            print(f"Sucesso absoluto! Planilha salva em: {arquivo_final}")
        else:
            # Levanta um erro real para fazer o GitHub Actions parar e avisar se falhar
            raise RuntimeError("O botão foi clicado, mas nenhum arquivo .xlsx foi gerado na pasta.")
            
    finally:
        driver.quit()

if __name__ == "__main__":
    baixar_relatorio()
