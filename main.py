import pandas as pd
from selenium import webdriver
import logging
import time

# Importa as funções dos seus módulos
from scrapers.webindustrial import coletar_anuncios_webindustrial
from scrapers.webindustrial_detal import coletar_detalhes_anuncios

# Configuração de logging para feedback no terminal
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def processar_dados(df: pd.DataFrame) -> pd.DataFrame:
    """
    Realiza a limpeza e conversão de tipos de dados no DataFrame.
    
    Args:
        df: DataFrame original com os dados coletados.
        
    Returns:
        DataFrame com os dados limpos e convertidos.
    """
    logging.info("Iniciando a limpeza e conversão de dados.")
    
    # Lista de colunas a serem convertidas para numérico
    colunas_numericas = ['preco', 'condominio', 'area_locavel', 'iptu', 'valor_total_mensal', 'pe_direito']
    
    for col in colunas_numericas:
        # Garante que a coluna existe antes de tentar processá-la
        if col in df.columns:
            # Substitui o "Sob consulta" por um valor nulo (NaN) e remove caracteres
            df[col] = df[col].astype(str).str.replace('Sob consulta', '', regex=False)
            df[col] = df[col].str.replace('R$', '', regex=False).str.strip()
            df[col] = df[col].str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df[col] = df[col].str.replace('m²', '', regex=False).str.strip()
            df[col] = df[col].str.replace(':', '', regex=False).str.strip()
            
            # Converte a coluna para tipo numérico, forçando erros para NaN
            df[col] = pd.to_numeric(df[col], errors='coerce')

    logging.info("Limpeza e conversão de dados concluída.")
    return df

def main():
    """
    Função principal que orquestra toda a pipeline de coleta e processamento.
    """
    logging.info("Iniciando a pipeline de web scraping.")
    
    # 1. Configurar o WebDriver do Selenium
    driver = webdriver.Chrome()

    try:
        # 2. Primeira etapa: Coletar as URLs e dados da grid
        # Altere o 'limite_paginas' para controlar a quantidade de dados
        anuncios_coletados = coletar_anuncios_webindustrial(driver, limite_paginas=1)
        
        if not anuncios_coletados:
            logging.warning("Nenhum anúncio foi coletado na primeira etapa. Encerrando.")
            return

        # 3. Segunda etapa: Coletar os detalhes de cada anúncio
        anuncios_enriquecidos = coletar_detalhes_anuncios(driver, anuncios_coletados)

        # 4. Adicionar um ID único a cada dicionário
        for i, anuncio in enumerate(anuncios_enriquecidos):
            anuncio['id'] = i + 1

        # 5. Converter a lista de dicionários para um DataFrame do Pandas
        df_anuncios = pd.DataFrame(anuncios_enriquecidos)
        
        # 6. Renomear a coluna 'endereco' para 'endereco_completo'
        if 'endereco' in df_anuncios.columns:
            df_anuncios.rename(columns={'endereco': 'endereco_completo'}, inplace=True)

        # 7. Reordenar as colunas para que o 'id' seja a primeira
        if 'id' in df_anuncios.columns:
            colunas_ordenadas = ['id'] + [col for col in df_anuncios.columns if col != 'id']
            df_anuncios = df_anuncios[colunas_ordenadas]

        # 8. Processar e limpar os dados
        df_final = processar_dados(df_anuncios)

        # 9. Salvar o resultado final em um arquivo CSV
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        nome_arquivo = f"webindustrial_anuncios_limpos_{timestamp}.csv"
        df_final.to_csv(nome_arquivo, index=False, encoding='utf-8-sig')

        logging.info(f"Pipeline concluída! Dados salvos em '{nome_arquivo}'.")

    except Exception as e:
        logging.error(f"Ocorreu um erro na execução principal: {e}", exc_info=True)

    finally:
        # 10. Fechar o navegador de forma segura
        driver.quit()
        logging.info("Navegador fechado.")

if __name__ == "__main__":
    main()