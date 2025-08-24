# scrapers/webindustrial_detal.py

from selenium import webdriver
from bs4 import BeautifulSoup
import time
import logging
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import json
import os


# Configuração básica de logging para feedback no terminal
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Função auxiliar para encontrar um valor com base em um texto de label.
# Função auxiliar para encontrar um valor com base em um texto de label.
# Função auxiliar para encontrar um valor com base em um texto de label.
def extrair_detalhe_por_label(soup, label_text):
    """
    Função auxiliar para encontrar um valor com base em um texto de label.
    Garante que a extração seja robusta a pequenas variações.
    
    Args:
        soup: O objeto BeautifulSoup da página do anúncio.
        label_text: O texto do label que identifica a informação (ex: 'Pé Direito').
        
    Returns:
        O valor da informação ou 'Sob consulta' se não for encontrado.
    """
    try:
        # Encontra a tag <p> com o texto do label
        label_element = soup.find('p', string=lambda text: label_text in text)
        if label_element and label_element.parent:
            # Navega até o elemento-pai e depois encontra a tag do valor
            value_element = label_element.parent.find('p', class_='font-semibold')
            if value_element:
                return value_element.text.strip()
    except (AttributeError, IndexError):
        # Retorna 'Sob consulta' se o elemento não for encontrado
        return 'Sob consulta'
    return 'Sob consulta'



# Função auxiliar para encontrar um valor com base em um texto de label usando XPath.
# scrapers/webindustrial_detal.py

# ... (restante do código) ...

# scrapers/webindustrial_detal.py

# ... (restante do código) ...

def extrair_pe_direito_especifico(driver):
    """
    Função dedicada a extrair o valor de 'Pé Direito' usando um XPath relativo
    e manipulação de string.
    
    Args:
        driver: A instância do WebDriver do Selenium.
        
    Returns:
        O valor numérico do Pé Direito como string ou 'Sob consulta' se não for encontrado.
    """
    pe_direito_xpath = "//p[contains(text(), 'Pé Direito')]"
    
    try:
        pe_direito_element = driver.find_element(By.XPATH, pe_direito_xpath)
        texto_completo = pe_direito_element.text.strip()
        
        # O texto_completo será algo como "Pé Direito: 12.00" ou "Pé Direito: 12.00m".
        # Usamos split(':') para dividir a string em duas partes.
        partes = texto_completo.split(':')
        
        # A segunda parte (índice 1) contém o valor que queremos.
        if len(partes) > 1:
            valor = partes[1].strip()
            # Limpa o 'm' do final, se existir.
            valor = valor.replace('m', '').strip()
            return valor
        else:
            return 'Sob consulta'
            
    except NoSuchElementException:
        # Se o elemento com a frase não for encontrado, significa que não há Pé Direito
        return 'Sob consulta'
    except Exception as e:
        logging.error(f"Erro ao extrair o valor de 'Pé Direito': {e}")
        return 'Sob consulta'


def extrair_endereco_especifico(driver):
    """
    Extrai o endereço de um anúncio usando um XPath flexível,
    ancorado em um elemento estável.

    Args:
        driver: A instância do WebDriver do Selenium.

    Returns:
        O texto do endereço ou 'Sob consulta' se não for encontrado.
    """
    # XPath aprimorado: encontra qualquer h3 com a classe 'font-semibold'
    # mas APENAS dentro da div com o id 'scroll-div'.
    endereco_xpath = "//div[@id='scroll-div']//h3[contains(@class, 'font-semibold')]"
    
    try:
        endereco_element = driver.find_element(By.XPATH, endereco_xpath)
        return endereco_element.text.strip()
        
    except NoSuchElementException:
        return 'Sob consulta'
    except Exception as e:
        logging.error(f"Erro ao extrair o endereço: {e}")
        return 'Sob consulta'


# ... (restante do código) ...



# ... (restante do código)


def coletar_detalhes_anuncios(driver: webdriver.Chrome, lista_anuncios: list) -> list:
    """
    Visita a URL de cada anúncio e extrai informações detalhadas.
    
    Args:
        driver: A instância do WebDriver do Selenium.
        lista_anuncios: Uma lista de dicionários, onde cada um contém a 'url' do anúncio.
        
    Returns:
        A mesma lista de dicionários, mas enriquecida com os novos dados.
    """
    logging.info(f"Iniciando a coleta de detalhes para {len(lista_anuncios)} anúncios.")
    
    for i, anuncio in enumerate(lista_anuncios):
        url = anuncio.get('url')
        if not url:
            logging.warning(f"Anúncio no índice {i} não tem URL. Pulando.")
            continue

        logging.info(f"[{i+1}/{len(lista_anuncios)}] Visitando URL: {url}")
        
        try:
            # Navega até a URL do anúncio
            driver.get(url)
            time.sleep(2) # Pausa para o carregamento da página

            # Pega o HTML da página e passa para o Beautiful Soup
            anuncio_html = driver.page_source
            soup = BeautifulSoup(anuncio_html, 'html.parser')

            # Extração dos dados detalhados usando a função auxiliar
            anuncio['area_locavel'] = extrair_detalhe_por_label(soup, 'Área locável m²')
            anuncio['iptu'] = extrair_detalhe_por_label(soup, 'IPTU por m²')
            anuncio['valor_total_mensal'] = extrair_detalhe_por_label(soup, 'Valor total mensal')
            anuncio['pe_direito'] = extrair_pe_direito_especifico(driver)
            
            
            
            # Extração do endereço
            try:
                anuncio['endereco'] = extrair_endereco_especifico(driver)
            except (AttributeError, IndexError):
                anuncio['endereco'] = 'Sob consulta'
            
            logging.info(f"Dados extraídos: {anuncio}")
            
        except Exception as e:
            logging.error(f"Erro ao processar o anúncio em {url}. Erro: {e}")
            anuncio['area_locavel'] = 'Erro na coleta'
            anuncio['iptu'] = 'Erro na coleta'
            anuncio['valor_total_mensal'] = 'Erro na coleta'
            anuncio['pe_direito'] = 'Erro na coleta'
            anuncio['endereco'] = 'Erro na coleta'

    logging.info("Coleta de detalhes finalizada.")
    return lista_anuncios

if __name__ == "__main__":
    # O script vai procurar por 'anuncios.json' no mesmo diretório
    json_path = "anuncios.json"

    # Verifica se o arquivo existe antes de tentar lê-lo
    if not os.path.exists(json_path):
        print("Erro: O arquivo 'anuncios.json' não foi encontrado.")
        print("Por favor, execute 'main.py' primeiro para gerar o arquivo com as URLs.")
    else:
        try:
            # 1. Ler o arquivo JSON
            with open(json_path, "r", encoding="utf-8") as f:
                anuncios = json.load(f)
            
            print(f"URLs carregadas com sucesso de '{json_path}'. Total: {len(anuncios)} anúncios.")
            
            # 2. Configurar o WebDriver do Selenium
            driver = webdriver.Chrome()

            # 3. Chamar a função de coleta de detalhes com a lista de URLs
            anuncios_enriquecidos = coletar_detalhes_anuncios(driver, anuncios)

            # 4. Fechar o navegador
            driver.quit()

            # 5. Imprimir o resultado
            print("\n--- Dados Enriquecidos (Exemplo) ---")
            for anuncio in anuncios_enriquecidos[:5]:
                print(anuncio)
                print("-" * 20)
                
            print(f"Coleta de detalhes finalizada. Total de {len(anuncios_enriquecidos)} anúncios processados.")

        except Exception as e:
            print(f"Ocorreu um erro durante a execução: {e}")

    

  