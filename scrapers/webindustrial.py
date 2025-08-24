from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import time
import logging

# Configuração de logging para feedback no terminal
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def extrair_dados_anuncios(driver: webdriver.Chrome) -> list:
    """
    Extrai os dados de todos os anúncios na página atual.

    Args:
        driver: Instância do WebDriver do Selenium.

    Returns:
        Uma lista de dicionários, onde cada dicionário representa um anúncio.
    """
    anuncios_coletados = []
    
    # Seletor para a grid de anúncios
    grid_xpath = "//div[contains(@class, 'grid-cols-1 md:grid-cols-2')]"
    
    try:
        grid_element = driver.find_element(By.XPATH, grid_xpath)
    except NoSuchElementException:
        logging.error("Não foi possível encontrar a grid de anúncios. Verifique o seletor.")
        return anuncios_coletados

    anuncio_elements = grid_element.find_elements(By.TAG_NAME, 'a')
    
    logging.info(f"Encontrei {len(anuncio_elements)} anúncios nesta página.")

    for anuncio_element in anuncio_elements:
        try:
            anuncio_html = anuncio_element.get_attribute('outerHTML')
            anuncio_soup = BeautifulSoup(anuncio_html, 'html.parser')

            titulo = anuncio_soup.find('h3').text.strip()
            
            # Extração de Preço
            preco_pai = anuncio_soup.find('p', string='Preço de Locação /m²').parent
            preco_bruto = preco_pai.find_all('p')[1].text.strip()
            preco_limpo = preco_bruto.replace('\xa0', '').replace('R$', '')

            # Extração de Condomínio
            condominio_pai = anuncio_soup.find('p', string='Condomínio /m²').parent
            condominio_bruto = condominio_pai.find_all('p')[1].text.strip()
            condominio_limpo = condominio_bruto.replace('\xa0', '').replace('R$', '')

            # Extração de Metragem
            metragem_pai = anuncio_soup.find('p', string='Metragem').parent
            metragem = metragem_pai.find_all('p')[1].text.strip()
            
            url_anuncio = anuncio_soup.find('a')['href']

            anuncio_data = {
                'titulo': titulo,
                'preco': preco_limpo,
                'condominio': condominio_limpo,
                'metragem': metragem,
                'url': url_anuncio
            }
            anuncios_coletados.append(anuncio_data)

        except (AttributeError, IndexError, TypeError) as e:
            logging.warning(f"Não foi possível extrair dados de um anúncio. Erro: {e}. Pulando para o próximo...")
            continue
            
    return anuncios_coletados


def coletar_anuncios_webindustrial(driver: webdriver.Chrome, limite_paginas: int = 8) -> list:
    """
    Navega pelas páginas do WebIndustrial e coleta todos os anúncios,
    com um limite de páginas definido.

    Args:
        driver: Instância do WebDriver do Selenium.
        limite_paginas: O número máximo de páginas a serem visitadas.

    Returns:
        Uma lista de dicionários com todos os anúncios coletados.
    """
    all_anuncios = []
    url = "https://www.webindustrial.com.br/alugar/galpao"
    
    logging.info(f"Iniciando a coleta em: {url}")
    driver.get(url)

    pagina_atual = 1
    while pagina_atual <= limite_paginas:
        logging.info(f"\nColetando dados da página {pagina_atual}...")
        
        # Pausa para dar tempo da página carregar
        time.sleep(5) 
        
        anuncios_pagina_atual = extrair_dados_anuncios(driver)
        all_anuncios.extend(anuncios_pagina_atual)
        
        # Verifica se é a última página ou se o limite foi atingido
        if pagina_atual == limite_paginas:
            logging.info(f"Limite de {limite_paginas} páginas atingido. Finalizando a coleta.")
            break
        
        # Encontra o botão de "Próxima Página"
        try:
            # Novo seletor que busca pelo atributo aria-label
            proxima_pagina_btn = driver.find_element(By.XPATH, "//button[@aria-label='next']")
            
            logging.info("Encontrei o botão para a próxima página. Clicando...")
            proxima_pagina_btn.click()
            pagina_atual += 1
            
        except NoSuchElementException:
            logging.info("Última página atingida. Finalizando a coleta.")
            break
            
    return all_anuncios

# Bloco para testar o script de forma independente
if __name__ == "__main__":
    driver = webdriver.Chrome()
    anuncios_coletados = coletar_anuncios_webindustrial(driver, limite_paginas=2) # Coleta as primeiras 2 páginas

    logging.info("\n" + "="*40)
    logging.info(f"Coleta finalizada! Total de anúncios encontrados: {len(anuncios_coletados)}")
    logging.info("="*40)
    
    if anuncios_coletados:
        logging.info("\nPrimeiros 5 anúncios coletados:")
        for anuncio in anuncios_coletados[:5]:
            logging.info(anuncio)
            logging.info("-" * 20)
    
    driver.quit()