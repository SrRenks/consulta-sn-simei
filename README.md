
# Consulta Automatizada no Portal do Simples Nacional com Stealth Anti-Bot

Este projeto automatiza o processo de consulta de situação no Simples Nacional e SIMEI para CNPJs, utilizando uma instância controlada do Chrome em modo **stealth**, com múltiplas camadas de **evasão anti-bot**, simulação de comportamento humano e mitigação de **fingerprints detectáveis por sistemas de Captcha e similares**.

---

## Instalação

### 1. Requisitos

- Python 3.10+
- Google Chrome (instalado e acessível via linha de comando)
- Portas disponíveis para depuração remota (9222, 9223, ...)

#### Originalmente desenvolvido em ambiente Linux (Debian, Gnome). Adaptado para funcionamento também em Windows e Mac, porém essas versões ainda não foram completamente testadas e podem apresentar instabilidades.

---
### 2. Dependências

Instale as dependências com:

```bash
pip install -r requirements.txt
```

## Uso

### 1. Inicie uma instância do Chrome com DevTools remoto

```bash
google-chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-stealth \
  --no-first-run \
  --disable-blink-features=AutomationControlled \
  --disable-extensions \
  --lang=pt-BR \
  --window-size=1280,800
```

> Ou utilize o `ChromeManager` do próprio projeto para isso.

### 2. Execute a consulta

```python
from src.snsimei import SnSimei
from src.utils import ChromeManager

cnpj = "12.345.678/0001-90"

manager = ChromeManager(remote_debugging_port=9222)
bot = SnSimei(manager)
resultado = bot.get_cnpj_info(cnpj)

print(resultado)
```
---

### 3. Uso via CLI com `src/main/main.py`

O script `main.py` implementa um gerenciador (`SNSimeiManager`) para processar listas de CNPJs em paralelo usando múltiplas instâncias do Chrome controladas via DevTools Protocol. Ele valida, normaliza e executa consultas simultâneas para obter informações do Simples Nacional / SIMEI, exportando o resultado para arquivo Excel.

---

#### Como usar:

```bash
python src/main/main.py -i input.xlsx -o output.xlsx
```

* `-i, --input`: caminho para arquivo Excel de entrada contendo uma coluna `CNPJ` com os números de CNPJ para consulta.
* `-o, --output`: caminho para arquivo Excel onde os dados extraídos serão salvos.

---

#### Benefícios do uso multithread:

* **Paralelismo com múltiplas instâncias do Chrome:** Cada CNPJ é consultado em uma instância Chrome isolada, usando portas diferentes no protocolo DevTools, evitando bloqueios e melhorando o throughput.
* **Redução significativa no tempo total de consulta:** Ao usar um pool de threads (configurado para 3 simultâneas), o processo aproveita melhor os recursos do sistema e executa múltiplas requisições em paralelo.
* **Robustez na execução:** O sistema gerencia automaticamente portas e instâncias, garantindo que cada tarefa de scraping rode isoladamente, minimizando interferências entre elas.
* **Validação prévia dos CNPJs:** O manager filtra e rejeita CNPJs inválidos, evitando chamadas desnecessárias e melhorando a confiabilidade do resultado final.


Esse design é especialmente útil para consultas em massa em sistemas que aplicam limitações ou bloqueios baseados em comportamento e IP, já que o paralelismo pode ser combinado com uso de proxies e técnicas stealth para aumentar a eficiência e anonimato das requisições.


---

## Estrutura do Projeto

```
consulta-sn-simei/
│
├── src/
│   ├── main/
│   │   └── main.py                           # Executável principal
│   │
│   ├── utils/
│       ├── __init__.py
│       ├── chrome.py                         # ChromeManager
│       ├── stealth.py                        # StealthToolkit
│       ├── human.py                          # HumanMouseMover e simulador de interação
│       └── scraper.py                        # Classe SnSimei com scraping em si
│
├── resources/
│   └── *.js                                   # Scripts de evasão e spoofing

```

---

## Detalhes Técnicos: Blindagem Anti-Bot e Anti-Captcha

### Objetivo

Evitar a detecção por mecanismos de análise comportamental e fingerprinting como:

- **Captcha Invisble**
- **BotD / FingerprintJS**
- **Detecção via `navigator` e `WebGL`**
- **Verificação de `Chrome Runtime`, `toString` e `plugins`**


### Spoofing e Patching via DevTools Protocol (Explicado em Detalhes)

Abaixo a descrição técnica de **todos os arquivos JS** utilizados pelo `StealthToolkit`, injetados com `Runtime.evaluate`:

| Arquivo                                       | Função                                                                                                                                                    |
| --------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`stealth_injection.js`**                    | Script base que aplica camadas mínimas de evasão (`navigator.webdriver = false`, etc).                                                                    |
| **`spoof_canvas_fingerprint.js`**             | Substitui `CanvasRenderingContext2D.prototype.getImageData` e `toDataURL` para retornar pixels com ruído determinístico, evitando fingerprint por canvas. |
| **`canvas_noise.js`**                         | Versão alternativa com ruído aleatório a cada execução — útil para sessões efêmeras.                                                                      |
| **`spoof_webgl_precision.js`**                | Modifica a resposta de `getShaderPrecisionFormat` e `getParameter` do WebGL para valores típicos de hardware real.                                        |
| **`webgl_spoof.js`**                          | Injeta spoof completo de `WebGLRenderingContext`, com vendor e renderer personalizados (ex: "NVIDIA Corporation").                                        |
| **`mock_navigator_plugins_and_mimetypes.js`** | Preenche `navigator.plugins` e `navigator.mimeTypes` com mocks de plugins reais como Flash, PDF Viewer etc.                                               |
| **`override_function_toString.js`**           | Sobrescreve `Function.prototype.toString` para retornar código legítimo de funções spoofadas, evitando fingerprint reverso.                               |
| **`mock_chrome_runtime.js`**                  | Cria um objeto `chrome.runtime` falso para evitar erros em sites que testam `typeof chrome.runtime === 'object'`.                                         |
| **`mock_webrtc.js`**                          | Neutraliza `RTCPeerConnection` e `createDataChannel`, evitando fingerprint de IP local e interfaces de rede via WebRTC.                                   |
| **`rtc_peerconnection_patch.js`**             | Similar ao anterior, porém mais granular: intercepta `addIceCandidate`, `onicecandidate`, e oculta candidatos com IP local.                               |
| **`mock_audio_fingerprint.js`**               | Spoofa `AudioContext` e `AnalyserNode.getFloatFrequencyData`, inserindo pequenas variações de ruído no áudio gerado.                                      |
| **`audio_oscillator_patch.js`**               | Intercepta `OscillatorNode` para retornar valores consistentes, evitando fingerprint baseado em render de som oscilatório.                                |
| **`mock_navigator_connection.js`**            | Preenche `navigator.connection` com valores plausíveis (`downlink`, `rtt`, `type`) para simular rede real (4g, etc).                                      |
| **`screen_properties.js`**                    | Define valores customizados de `screen.width`, `height`, `availWidth`, etc, evitando identificação de headless ou VMs.                                    |
| **`navigator_properties.js`**                 | Sobrescreve propriedades comuns como `hardwareConcurrency`, `deviceMemory`, `languages`, `userAgentData`.                                                 |
| **`mock_media_devices.js`**                   | Adiciona simulações a `navigator.mediaDevices.enumerateDevices`, simulando webcam e microfone.                                                            |
| **`permissions_query_patch.js`**              | Evita erros ao chamar `navigator.permissions.query` — define resposta para permissões típicas (`notifications`, etc).                                     |
| **`intl_datetime_patch.js`**                  | Altera a resposta de formatações com `Intl.DateTimeFormat`, simulando timezone coerente com o idioma/região configurada.                                  |

Esses patches são modulados e selecionáveis conforme o `level` configurado em `StealthToolkit(level="low" | "normal" | "strict")` ou listados de forma personalizadas pelo modo `custom`, passando-os por meio do atributo `custom_methods` em lista.

### 2. **Simulação de Comportamento Humano (Mouse/Teclado)**

A classe `HumanMouseMover` usa movimentos reais e não-lineares, com delays e hesitação baseada em **distribuição gaussiana**.

**Exemplo de digitação:**

```python
self.human.type_text('12345678', max(0.05, random.gauss(0.1, 0.15)))
```

**Exemplo de clique:**

```python
self.human.click(x, y)
```

Esses movimentos são executados:

- Com pausa antes de digitar
- Com variação de tempo por caractere
- Com cálculo de posição real via `getBoundingClientRect`


### 3. **Detecção de DOM Dinâmico e Espera Assíncrona**

Para evitar interações precipitadas:

- O HTML da página é verificado antes e depois do clique.
- A automação espera mudanças reais no DOM, sinalizando carregamento de nova página.

```python
while new_html == prev_html:
    time.sleep(0.1)
```

Além disso, é utilizado:

```python
self.human.wait_for_pageload()
```

### 4. **Fechamento Controlado e Reset de Sessão**

Após cada execução:

- O `ChromeManager` encerra a instância.
- O perfil de usuário é isolado por diretório (`--user-data-dir`), permitindo multithreading com IP/proxy distintos.

---

## Recomendações e Melhorias para Robustez e Escalabilidade

### Uso de Proxy por Instância para Evitar Banimento e Fingerprint Comportamental

Para evitar bloqueios comuns baseados em IP e reduzir o risco de fingerprint comportamental, recomenda-se fortemente a utilização de **instâncias independentes do Chrome, cada uma com seu próprio proxy**. Isso permite:

* **Distribuição da carga e anonimização** do tráfego, dificultando a detecção por IP repetido.
* Redução do acoplamento entre fingerprint de rede e fingerprint comportamental, já que cada instância navega por uma rota distinta.
* Maior resistência a bloqueios geográficos e políticas regionais específicas.

### Estratégias Recomendadas:

1. **Proxies Rotativos e Dedicados:**

   * Utilize proxies rotativos com pool de IPs brasileiros para maior naturalidade.
   * Sempre que possível, prefira proxies residenciais ou mobile, que simulam conexões legítimas.

2. **Isolamento Completo de Perfil por Instância:**

   * Use diferentes `user-data-dir` para cada instância para evitar cache e armazenamento compartilhado.
   * Configure cookies, localStorage e IndexedDB isoladamente.

3. **Simulação Avançada de Comportamento Humano:**

   * Combine o uso do `HumanMouseMover` e `StealthToolkit` com delays e movimentos randômicos.
   * Intercale padrões de navegação — evite sequências idênticas entre instâncias.

4. **Monitoramento e Feedback Dinâmico:**

   * Implemente captura e análise de logs para detectar bloqueios ou respostas suspeitas.
   * Ajuste proxies e scripts stealth conforme o feedback dos servidores.

5. **Escalonamento Paralelo Cuidadoso:**

   * Ajuste o número de threads/processos conforme capacidade da máquina e qualidade do proxy.
   * Respeite limites e intervalos entre requisições para não gerar comportamento robótico.

---

## Considerações Finais

Esse projeto serve como base para aplicações onde é necessário:

- Executar **web scraping seguro** em domínios com detecção avançada
- Automatizar interações com **alta fidelidade de simulação humana**
- Realizar **pesquisas com CNPJs** sem bloqueios ou captchas persistentes

---

## Disclaimer

Este projeto é estritamente educacional. O uso indevido em violação aos Termos de Serviço de sites-alvo pode ser ilegal. Use com responsabilidade.