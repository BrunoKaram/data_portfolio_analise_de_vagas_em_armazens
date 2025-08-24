from selenium import webdriver
from bs4 import BeautifulSoup
import time

# 1. Usar o Selenium para carregar a página
driver = webdriver.Chrome()
url = "https://www.webindustrial.com.br/alugar/galpao"
print(f"Abrindo a página: {url}")
driver.get(url)

# Opcional: Pausar para garantir que a página carregou completamente
time.sleep(3)

# 2. Obter o código-fonte HTML da página
html = driver.page_source

# 3. Usar o Beautiful Soup para analisar o HTML
soup = BeautifulSoup(html, 'html.parser')
print("HTML analisado com Beautiful Soup.")


# 6. Fechar o navegador
print("Fechando o navegador...")
driver.quit()
print("Teste concluído.")

# Opcional: Salvar o HTML em um arquivo para inspeção
with open("pagina_html.html", "w", encoding="utf-8") as file:
    file.write(html)
print("HTML salvo no arquivo 'pagina_html.html'.")