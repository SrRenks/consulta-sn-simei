# Consulta Simples Nacional / SIMEI - Automação Stealth com Chrome DevTools

Este projeto realiza consultas automatizadas e **furtivas (stealth)** no site da Receita Federal para verificar a situação de CNPJs no **Simples Nacional** e no **SIMEI**, utilizando simulação realista de comportamento humano para **evitar bloqueios por sistemas como hCaptcha**.

---

## 🧠 Base Teórica

O comportamento do usuário é simulado com base nos seguintes estudos:

- **Keystroke-Level Model (KLM)** — Card, Moran e Newell  
- **Human-Computer Interaction** — Dix et al.  
- **Heurísticas da Nielsen Norman Group** (usabilidade e interação)  
- **OWASP Automated Threat Handbook** — Estratégias para evitar detecção de bots  

---

## 🛠️ Tecnologias Utilizadas

- Python 3.10+
- pychrome — controle do Chrome via DevTools Protocol
- BeautifulSoup — extração de informações do HTML
- pandas, tqdm — manipulação de dados e progresso
- argparse — CLI amigável
- concurrent.futures — execução paralela com múltiplas instâncias do Chrome
- Simulação de comportamento humano:
  - Digitação realista
  - Movimento do mouse suave
  - Hesitação entre ações
  - Scroll de página

---

## 📦 Instalação

1. Clone o repositório:

    ```git clone https://github.com/SrRenks/consulta-sn-simei.git```

    ```cd consulta-sn-simei```

2. Crie e ative um ambiente virtual:

    ```python -m venv .venv```
    
    ```source .venv/bin/activate```  (Linux/macOS)
    ```.venv\Scripts\activate``` (Windows)
    

3. Instale as dependências:

    ```pip install -r requirements.txt```

---

## ⚙️ Como Usar

### 1. Prepare o arquivo de entrada

Um arquivo `.xlsx` com uma coluna chamada `CNPJ`.

Exemplo:

| CNPJ             |
|------------------|
| 18.781.203/0001-28 |
| 06123010000100     |

### 2. Execute o script

    python main.py -i ./entradas.xlsx -o ./resultados.xlsx

---

## 📄 Output

O arquivo de saída conterá as seguintes colunas:

- CNPJ
- Nome Empresarial
- Situação no Simples Nacional
- Situação no SIMEI
- Exception *(se houver erro específico para aquele CNPJ)*

---

## 🧪 Estratégia Stealth

Para evitar detecção por sistemas anti-bot como o hCaptcha:

- Usa uma instância personalizada do Chrome com:
  - `--remote-debugging-port`
  - `--disable-blink-features=AutomationControlled`
  - Perfil de usuário exclusivo
- Movimentação de mouse com ruído e variação
- Scroll aleatório da página
- Hesitação programada entre ações
- Evita uso direto de `.click()` ou `.value =`

---

## 🧩 Estrutura do Projeto

    consulta-sn-simei/
    ├── src/
    │   ├── main.py
    │   ├── utils/
    |   |   ├── __init__.py
    │   │   ├── chrome.py
    │   │   ├── human.py
    │   │   ├── snsimei.py
    ├── requirements.txt
    ├── README.md

---

## ⚠️ Avisos Legais

Este projeto é apenas para fins educacionais. A automação de sistemas públicos deve ser feita com responsabilidade e sem violar os **Termos de Uso** da instituição envolvida. O uso indevido pode acarretar penalidades legais.

### 🔌 Portas Utilizadas

Por padrão, o script inicia o Chrome usando a porta **9222** para o protocolo DevTools. Quando múltiplos CNPJs são processados em paralelo (via multithreading), cada instância do Chrome usa uma porta sequencial: **9222**, **9223**, **9224**, etc., de acordo com o número de threads ativas; o que é modificável, mas a depender dos recursos de sua máquina. Por precaução matenha valores baixos para evitar ser considerado um comportamento suspeito vindo de seu IP (caso não esteja utilizando uma rotação via proxy).

---

## 📬 Contribuições

Contribuições são bem-vindas! Abra uma *issue* ou envie um *pull request* com melhorias.

---

## 🧑‍💻 Autor

Desenvolvido por Renks (https://github.com/SrRenks)
