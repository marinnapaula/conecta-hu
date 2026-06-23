import os
import time
import glob
import re
import shutil
import unicodedata
from datetime import date
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

# =====================================================================
# CONFIGURAÇÕES GERAIS E DATAS
# =====================================================================
GETS_URL = "https://gets.ceb.unicamp.br/nec/view"
WAIT = 20
TIMEOUT_DOWNLOAD = 300 # Tolerância de 5 minutos

MESES_PT = {
    1: "janeiro",  2: "fevereiro", 3: "março",    4: "abril",
    5: "maio",     6: "junho",     7: "julho",    8: "agosto",
    9: "setembro", 10: "outubro",  11: "novembro", 12: "dezembro",
}

def primeiro_dia_mes():
    hoje = date.today()
    return f"01/{hoje.month:02d}/{hoje.year}"

def primeiro_dia_ano():
    hoje = date.today()
    return f"01/01/{hoje.year}"

def hoje_str():
    hoje = date.today()
    return f"{hoje.day:02d}/{hoje.month:02d}/{hoje.year}"

# =====================================================================
# LÓGICA DE DIRETÓRIOS E RENOMEAÇÃO
# =====================================================================
PASTA_BASE = Path(os.getcwd()) / "planilhas_gets"
PASTA_TEMP = PASTA_BASE / "temp_downloads"

PASTAS_DESTINO = {
    "encerradas":   PASTA_BASE / "01.OS_Encerradas",
    "pendentes":    PASTA_BASE / "02.OS_Pendentes",
    "atividades":   PASTA_BASE / "03.Atividades",
    "inventario":   PASTA_BASE / "04.Inventário",
    "atendimento":  PASTA_BASE / "05. Atendimento de OS",
    "agendamentos": PASTA_BASE / "06. Agendamento MP"
}

PASTA_TEMP.mkdir(parents=True, exist_ok=True)
for p in PASTAS_DESTINO.values():
    p.mkdir(parents=True, exist_ok=True)

def limpar_pasta_temp():
    for f in PASTA_TEMP.glob("*"):
        try: f.unlink()
        except: pass

def remover_acentos(texto: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn').lower()

def calcular_nome_atividades(pasta: Path) -> str:
    hoje = date.today()
    mes_nome = MESES_PT[hoje.month]
    sufixo_normalizado = remover_acentos(f"horastrabalhadas_{mes_nome}{hoje.year}")

    todos = list(pasta.glob("*.xlsx"))
    for arq in todos:
        if sufixo_normalizado in remover_acentos(arq.stem):
            return arq.name 

    maior_nn = 0
    for arq in todos:
        match = re.match(r'^(\d+)\.', arq.name)
        if match:
            maior_nn = max(maior_nn, int(match.group(1)))
    
    return f"{maior_nn + 1:02d}.horasTrabalhadas_{mes_nome}{hoje.year}.xlsx"

# =====================================================================
# INTERAÇÕES DO SELENIUM
# =====================================================================
def preencher_data(driver, campo_id, valor):
    el = WebDriverWait(driver, WAIT).until(EC.presence_of_element_located((By.ID, campo_id)))
    driver.execute_script("arguments[0].removeAttribute('readonly')", el)
    driver.execute_script("arguments[0].value = '';", el)
    el.click()
    el.send_keys(valor)
    el.send_keys(Keys.TAB)
    time.sleep(0.5)

def clicar_radio(driver, name, value):
    el = driver.find_element(By.CSS_SELECTOR, f"input[name='{name}'][value='{value}']")
    driver.execute_script("arguments[0].click();", el)
    time.sleep(0.5)

def clicar_gerar_planilha(driver, wait):
    """Clica no botão de gerar buscando pelo texto, evitando erros se o ID mudar"""
    print("   Processando solicitação no servidor do GETS...")
    btn = wait.until(EC.presence_of_element_located((By.XPATH, "//span[text()='Gerar Planilha']/parent::button | //button[.//span[text()='Gerar Planilha']]")))
    driver.execute_script("arguments[0].click();", btn)

def aguardar_dialog_download(driver):
    try:
        # Tolerância aumentada para relatórios muito pesados (ex: 6 meses de OS)
        btn = WebDriverWait(driver, 180).until(
            EC.element_to_be_clickable((By.XPATH, "//button[.//span[contains(@class,'fa-download')]] | //span[contains(@class,'ui-button-text') and text()='Baixar']/parent::button"))
        )
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(2)
    except Exception:
        print("   [Aviso] Popup de download não detectado a tempo.")

def processar_download(chave_destino):
    print(f"   Aguardando a transferência do arquivo...")
    inicio = time.time()
    arquivo_baixado = None
    
    while time.time() - inicio < TIMEOUT_DOWNLOAD:
        arquivos = [f for f in PASTA_TEMP.glob("*.xlsx") if not f.name.endswith(".crdownload")]
        if arquivos:
            arquivo_baixado = max(arquivos, key=lambda f: f.stat().st_mtime)
            break
        time.sleep(2)
    
    if not arquivo_baixado:
        raise RuntimeError(f"Falha de timeout ao baixar o relatório: {chave_destino}")

    if chave_destino == "atividades":
        nome_final = calcular_nome_atividades(PASTAS_DESTINO["atividades"])
    else:
        nome_final = arquivo_baixado.name
        
    destino_final = PASTAS_DESTINO[chave_destino] / nome_final
    shutil.move(str(arquivo_baixado), str(destino_final))
    print(f"   ✅ Arquivo salvo em: {destino_final.relative_to(PASTA_BASE)}")

# =====================================================================
# FLUXO PRINCIPAL DO ROBÔ
# =====================================================================
def executar_robo():
    print("Iniciando o Super Robô de Extração do GETS (GitHub Actions)...")
    
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    
    opts.add_experimental_option("prefs", {
        "download.default_directory": str(PASTA_TEMP),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    })
    
    driver = webdriver.Chrome(options=opts)
    wait = WebDriverWait(driver, WAIT)
    driver.execute_cdp_cmd("Page.setDownloadBehavior", {"behavior": "allow", "downloadPath": str(PASTA_TEMP)})

    try:
        print("\nRealizando Login...")
        driver.get(f"{GETS_URL}/inicio/index.jsf")
        wait.until(EC.presence_of_element_located((By.ID, "j_username"))).send_keys(os.environ.get('GETS_USER'))
        driver.find_element(By.NAME, "j_password").send_keys(os.environ.get('GETS_PASS'))
        driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
        
        wait.until(EC.presence_of_element_located((By.ID, "menu")))
        time.sleep(2)
        print("Login bem-sucedido.")

        # --- 1. OS ENCERRADAS ---
        limpar_pasta_temp()
        print("\nExtraindo: 01. OS Encerradas...")
        driver.get(f"{GETS_URL}/formrelatorios/ordens_encerradas.jsf")
        time.sleep(3)
        preencher_data(driver, "fm1:dataEncerramentoInicial_input", primeiro_dia_mes())
        preencher_data(driver, "fm1:dataEncerramentoFinal_input", hoje_str())
        clicar_gerar_planilha(driver, wait)
        aguardar_dialog_download(driver)
        processar_download("encerradas")

        # --- 2. OS PENDENTES ---
        limpar_pasta_temp()
        print("\nExtraindo: 02. OS Pendentes...")
        driver.get(f"{GETS_URL}/formrelatorios/ordens_pendentes.jsf")
        time.sleep(3)
        preencher_data(driver, "fm1:j_idt76_input", "01/01/2023")
        preencher_data(driver, "fm1:j_idt79_input", hoje_str())
        clicar_radio(driver, "fm1:options5", "1")
        clicar_gerar_planilha(driver, wait)
        aguardar_dialog_download(driver)
        processar_download("pendentes")

        # --- 3. ATIVIDADES (HORAS TRABALHADAS) ---
        limpar_pasta_temp()
        print("\nExtraindo: 03. Atividades (Horas Trabalhadas)...")
        driver.get(f"{GETS_URL}/formrelatorios/horas_trabalhadas.jsf")
        time.sleep(3)
        preencher_data(driver, "fm1:dtInicio_input", primeiro_dia_mes())
        preencher_data(driver, "fm1:dtInicioAte_input", hoje_str())
        preencher_data(driver, "fm1:dtTermino_input", primeiro_dia_mes())
        preencher_data(driver, "fm1:dtTerminoAte_input", hoje_str())
        clicar_gerar_planilha(driver, wait)
        aguardar_dialog_download(driver)
        processar_download("atividades")

        # --- 4. INVENTÁRIO ---
        limpar_pasta_temp()
        print("\nExtraindo: 04. Inventário...")
        driver.get(f"{GETS_URL}/formrelatorios/listaeqptos.jsf")
        time.sleep(3)
        clicar_radio(driver, "fm1:optClasse", "1")
        clicar_radio(driver, "fm1:optDesativado", "0")
        time.sleep(1)
        clicar_radio(driver, "fm1:optIndicadores", "true")
        clicar_gerar_planilha(driver, wait)
        aguardar_dialog_download(driver)
        processar_download("inventario")

        # --- 5. ATENDIMENTO DE OS ---
        limpar_pasta_temp()
        print("\nExtraindo: 05. Atendimento de OS...")
        driver.get(f"{GETS_URL}/formrelatorios/atendimento_ordens_servico.jsf")
        time.sleep(3)
        preencher_data(driver, "fm1:dataInicial_input", primeiro_dia_ano())
        preencher_data(driver, "fm1:dataFinal_input", hoje_str())
        preencher_data(driver, "fm1:dataEncerramentoInicial_input", primeiro_dia_ano())
        preencher_data(driver, "fm1:dataEncerramentoFinal_input", hoje_str())
        clicar_gerar_planilha(driver, wait)
        aguardar_dialog_download(driver)
        processar_download("atendimento")

        # --- 6. AGENDAMENTO MP ---
        limpar_pasta_temp()
        print("\nExtraindo: 06. Agendamento MP...")
        driver.get(f"{GETS_URL}/formrelatorios/agendamentos.jsf")
        time.sleep(3)
        driver.execute_script("document.getElementById('fm1:j_idt50_input').value = '';")
        driver.execute_script("document.getElementById('fm1:j_idt53_input').value = '';")
        time.sleep(1)
        clicar_gerar_planilha(driver, wait)
        aguardar_dialog_download(driver)
        processar_download("agendamentos")

        print("\n🚀 MARATONA DE EXTRAÇÃO CONCLUÍDA COM SUCESSO!")

    finally:
        driver.quit()
        limpar_pasta_temp()
        try: PASTA_TEMP.rmdir()
        except: pass

if __name__ == "__main__":
    executar_robo()
