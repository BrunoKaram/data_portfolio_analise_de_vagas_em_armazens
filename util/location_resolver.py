import pandas as pd
import requests
import json
import logging
import os
import numpy as np

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def inferir_localizacao_com_ollama(titulo: str, endereco: str) -> dict:
    """
    Usa o Ollama para inferir a cidade, estado e um endereço completo
    a partir do título e endereço existentes.
    """
    
    api_url = "http://localhost:11434/api/generate"
    model = "llama3.1:8b"

    prompt = f"""
    Você é um assistente de geolocalização. Sua tarefa é extrair a cidade e o estado a partir das informações fornecidas.
    Considere o título do anúncio e o endereço atual para fazer a sua inferência.
    Se você encontrar uma cidade ou bairro, tente inferir a cidade e o estado.
    Se as informações forem insuficientes, retorne 'nao_encontrado'.

    Siga rigorosamente o formato de saída JSON. Não inclua texto explicativo, apenas o JSON.
    {{
      "cidade": "nome da cidade",
      "estado": "sigla do estado",
      "endereco_completo": "Endereço mais preciso ou o bairro, cidade, estado"
    }}

    Exemplo de entrada:
    Título: "Edifício Bonsucesso Logistics Park - Galpão para Alugar - Vila Nova Bonsucesso"
    Endereço: "Detalhes da Oferta"

    Exemplo de saída:
    {{
      "cidade": "Guarulhos",
      "estado": "SP",
      "endereco_completo": "Vila Nova Bonsucesso, Guarulhos, SP"
    }}

    Título para análise: "{titulo}"
    Endereço atual: "{endereco}"
    """

    data = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }

    try:
        response = requests.post(api_url, json=data, timeout=120)
        response.raise_for_status()
        result = response.json()
        
        generated_content = json.loads(result.get('response', '{}'))
        return generated_content
    
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro ao conectar com Ollama. Verifique se o Ollama está rodando e o modelo '{model}' foi baixado. Erro: {e}")
    except json.JSONDecodeError as e:
        logging.error(f"Erro ao decodificar a resposta JSON do Ollama. Resposta: {result.get('response', 'Nenhuma')}. Erro: {e}")
        
    return {
        "cidade": "nao_encontrado",
        "estado": "nao_encontrado",
        "endereco_completo": "nao_encontrado"
    }


def main():
    """
    Função principal para enriquecer a tabela com dados de localização.
    """
    input_file = "webindustrial_anuncios_limpos.csv"
    output_file = "webindustrial_anuncios_localizados.csv"

    # 1. Carregar o DataFrame
    if not os.path.exists(input_file):
        logging.error(f"Arquivo '{input_file}' não encontrado. Por favor, rode 'main.py' primeiro.")
        return

    df = pd.read_csv(input_file, encoding='utf-8-sig')
    logging.info(f"DataFrame carregado com sucesso. Total de {len(df)} linhas.")

    # 2. Criar as colunas 'cidade' e 'estado' se não existirem
    if 'cidade' not in df.columns:
        df['cidade'] = None
    if 'estado' not in df.columns:
        df['estado'] = None

    # 3. Identificar as linhas a serem enriquecidas
    # Condição de filtro robusta: verifica se alguma das colunas-chave está ausente ou com erro
    df['endereco_completo'] = df['endereco_completo'].replace('Detalhes da Oferta', np.nan)
    df['cidade'] = df['cidade'].replace('nao_encontrado', np.nan)
    df['estado'] = df['estado'].replace('nao_encontrado', np.nan)
    
    mask_to_enrich = df['endereco_completo'].isnull() | df['cidade'].isnull() | df['estado'].isnull()
    
    anuncios_para_enriquecer = df[mask_to_enrich].copy() # Cria uma cópia para não alterar o DataFrame original no loop
    
    logging.info(f"Encontrados {len(anuncios_para_enriquecer)} anúncios para enriquecer.")

    if anuncios_para_enriquecer.empty:
        logging.info("Nenhum anúncio precisa de enriquecimento. Finalizando.")
        return

    # 4. Processar cada linha com Ollama
    for index, row in anuncios_para_enriquecer.iterrows():
        titulo = row.get('titulo', '')
        endereco = row.get('endereco_completo', '')
        
        # Chama a função de inferência
        localizacao = inferir_localizacao_com_ollama(titulo, endereco)
        
        # 5. Atualizar o DataFrame principal com os novos dados
        df.loc[index, 'cidade'] = localizacao.get('cidade', '')
        df.loc[index, 'estado'] = localizacao.get('estado', '')
        df.loc[index, 'endereco_completo'] = localizacao.get('endereco_completo', '')

        logging.info(f"Anúncio '{row.get('id', 'N/A')}' enriquecido. Nova localização: '{localizacao.get('cidade', 'N/A')}, {localizacao.get('estado', 'N/A')}'")
        
    # 6. Salvar o DataFrame final enriquecido
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    logging.info(f"Processo de enriquecimento concluído. Arquivo final salvo como '{output_file}'.")

if __name__ == "__main__":
    main()