import pandas as pd
import requests
import json
import logging
import os

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def enriquecer_com_ollama(titulo: str) -> dict:
    """
    Usa o Ollama para inferir a cidade, estado e um endereço
    a partir do título de um anúncio.

    Args:
        titulo: O título do anúncio a ser analisado.

    Returns:
        Um dicionário com as chaves 'cidade', 'estado' e 'endereco_completo'.
    """
    api_url = "http://localhost:11434/api/generate"
    model = "llama3.1:8b" # Substitua pelo modelo que você baixou

    # O prompt é a parte mais importante. Ele instrui o LLM a como se comportar.
    prompt = f"""
    Você é um assistente de inteligência de localização. Sua tarefa é extrair a cidade,
    o estado e um endereço completo de um título de anúncio, se houver.
    Se a localização for um bairro, tente inferir a cidade e o estado.
    Se não for possível identificar, retorne o valor 'nao_encontrado'.

    Siga o seguinte formato para a sua resposta (JSON):
    {{
      "cidade": "nome da cidade",
      "estado": "sigla do estado",
      "endereco_completo": "nome do bairro ou rua, nome da cidade, sigla do estado"
    }}

    Exemplo de entrada:
    "Edifício Bonsucesso Logistics Park - Galpão em Condomínio de 2.839,00m² para Alugar - Vila Nova Bonsucesso"

    Exemplo de saída:
    {{
      "cidade": "Guarulhos",
      "estado": "SP",
      "endereco_completo": "Vila Nova Bonsucesso, Guarulhos, SP"
    }}

    Título para análise: "{titulo}"
    """

    data = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json"  # Solicita a saída em formato JSON
    }

    try:
        response = requests.post(api_url, json=data, timeout=120) # Aumente o timeout se precisar
        response.raise_for_status() # Lança um erro para status de resposta ruins
        result = response.json()
        
        # O Ollama retorna o conteúdo em 'response'. A string JSON precisa ser parseada.
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
    Função principal que orquestra a limpeza e o enriquecimento dos dados.
    """
    input_file = "webindustrial_anuncios_limpos.csv"
    output_file = "webindustrial_anuncios_enriquecidos.csv"
    
    # 1. Carregar o DataFrame
    if not os.path.exists(input_file):
        logging.error(f"Arquivo '{input_file}' não encontrado. Por favor, rode 'main.py' primeiro.")
        return

    df = pd.read_csv(input_file, encoding='utf-8-sig')
    logging.info(f"DataFrame carregado com sucesso. Total de {len(df)} linhas.")

    # 2. Identificar as linhas a serem enriquecidas
    # Cria uma máscara booleana para encontrar as linhas com o erro
    mask_to_enrich = df['endereco_completo'] == 'Detalhes da Oferta'
    anuncios_para_enriquecer = df[mask_to_enrich]
    
    logging.info(f"Encontrei {len(anuncios_para_enriquecer)} anúncios para enriquecer.")

    if anuncios_para_enriquecer.empty:
        logging.info("Nenhum anúncio precisa de enriquecimento. Finalizando.")
        return

    # 3. Processar cada linha com Ollama
    for index, row in anuncios_para_enriquecer.iterrows():
        titulo = row['titulo']
        
        # Chama a função de enriquecimento
        localizacao = enriquecer_com_ollama(titulo)
        
        # 4. Atualizar o DataFrame principal com os novos dados
        df.loc[index, 'cidade'] = localizacao.get('cidade')
        df.loc[index, 'estado'] = localizacao.get('estado')
        df.loc[index, 'endereco_completo'] = localizacao.get('endereco_completo')

        logging.info(f"Anúncio '{row['id']}' enriquecido. Nova cidade: '{localizacao.get('cidade')}'")

    # 5. Salvar o DataFrame enriquecido em um novo arquivo
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    logging.info(f"Processo de enriquecimento concluído. Arquivo salvo como '{output_file}'.")

if __name__ == "__main__":
    main()