# 🎬 Roteiro do Vídeo Demonstrativo — Guardiã AI
### Tech Challenge Fase 5 — Pós-Tech IA para Devs (FIAP)
**Tempo total estimado:** 14 min 30 s a 14 min 50 s *(Limite máximo do edital: 15 minutos)*  
**Tom da apresentação:** Técnico, claro, objetivo e em primeira pessoa do plural (≈ 135–140 palavras/min).  
**Formato de entrega:** Vídeo publicado no YouTube ou Vimeo (público ou não listado).

---

## ⏱️ Grade de Distribuição do Tempo (Visão Geral)

| Bloco | Minutagem | Duração | Tema Principal |
|---|---|---|---|
| **1** | 0:00 – 1:30 | 1m 30s | Abertura, contextualização do desafio e cenário escolhido |
| **2** | 1:30 – 3:30 | 2m 00s | Arquitetura sistêmica e fluxo orquestrado com LangGraph |
| **3** | 3:30 – 6:00 | 2m 30s | Machine Learning, métricas com foco em Recall e explicabilidade SHAP |
| **4** | 6:00 – 8:00 | 2m 00s | RAG sobre protocolos oficiais (INCA/BI-RADS), LLM e guardrails |
| **5** | 8:00 – 11:30 | 3m 30s | **Demonstração Prática ao Vivo (Jornada Completa):** Login, triagem, PII, SHAP, **Homologação da Decisão Médica Final** e Assistente RAG |
| **6** | 11:30 – 13:15 | 1m 45s | Governança: Trilha de auditoria encadeada (SHA-256), histórico e API REST |
| **7** | 13:15 – 14:15 | 1m 00s | Containerização (Docker / Compose) e 14 testes automatizados (pytest) |
| **8** | 14:15 – 15:00 | 0m 45s | Dificuldades superadas, "Tradução para Leigos" e conclusão |

---

## 📽️ Roteiro Detalhado Passo a Passo

### 0:00 – 1:30 · Bloco 1: Abertura e Contexto do Desafio
*(Tela: Slide inicial com os dados do projeto, Grupo 33, integrantes e título "Guardiã AI — Triagem de Risco de Câncer de Mama")*

**Fala:**  
"Olá a todos! Sejam muito bem-vindos. Somos o Grupo 33, composto por Cesar Melo Dutra e Fernando Ramos Etchepare, e estamos apresentando a nossa solução para o **Tech Challenge da Fase 5** da Pós-Tech em IA para Devs da FIAP.

O desafio nos convidou a desenvolver a **Guardiã AI**, uma plataforma de Inteligência Artificial voltada a instituições de assistência à mulher, capaz de analisar dados clínicos e relatos de atendimento. 

Dentre os contextos propostos, selecionamos como **cenário principal a Saúde da Mulher focada no Apoio à Triagem e Estratificação de Risco de Câncer de Mama**, integrando o processamento de relatos clínicos com proteção rigorosa à privacidade e identificação de sinais de alerta. O câncer de mama é a neoplasia que mais vitima mulheres no Brasil; a precocidade no diagnóstico eleva a probabilidade de cura para mais de 90%, mas os serviços de triagem enfrentam sobrecarga e dados complexos.

E estabelecemos como pilar inegociável a diretriz ética do edital: **a Guardiã AI não faz diagnóstico definitivo, não prescreve medicamentos e não decide nada sozinha**. Ela funciona como um acelerador e suporte à decisão, onde **a decisão final sempre deverá permanecer com uma pessoa responsável pelo atendimento**."

---

### 1:30 – 3:30 · Bloco 2: Arquitetura Sistêmica e LangGraph
*(Tela: Diagrama da arquitetura — Figura 13 do relatório técnico / slide do fluxo)*

**Fala:**  
"Para transformar modelos isolados em um produto robusto, desenhamos uma arquitetura modular orquestrada com **LangGraph**, dividida em oito etapas encadeadas:

1. **Validação e Sanitização:** os dados citológicos são verificados e o relato de atendimento passa por mascaramento automático de dados pessoais sensíveis (como CPF, e-mail e telefone) em conformidade com a LGPD, além de detecção de injeção de prompt;
2. **Modelo de Machine Learning:** o classificador supervisionado calcula a probabilidade estimada de malignidade;
3. **Explicabilidade por SHAP:** cálculo em tempo real da contribuição das variáveis morfológicas celulares;
4. **Extração de Achados:** analisador léxico extrai sinais de alerta clínico presentes no relato, como nódulos palpáveis ou secreção mamilar;
5. **RAG Contextual:** busca vetorial em protocolos clínicos oficiais do Ministério da Saúde e do INCA;
6. **LLM Synthesis:** o modelo de linguagem Claude contextualiza os dados técnicos em uma redação clínica clara, com modo offline determinístico de contingência;
7. **Guardrails de Saída:** filtros bloqueiam qualquer tentativa de diagnóstico taxativo ou prescrição indevida e anexam o aviso obrigatório de suporte à decisão;
8. **Persistência e Homologação:** gravação transacional no banco SQLite com hash encadeado e posterior **homologação da decisão médica final pelo profissional responsável**."

---

### 3:30 – 6:00 · Bloco 3: Dados, Machine Learning e Explicabilidade SHAP
*(Tela: Gráficos de dispersão, matriz de confusão e tabela comparativa dos 4 modelos)*

**Fala:**  
"Nossa modelagem preditiva utiliza o dataset público **UCI Wisconsin Diagnostic Breast Cancer (WDBC)**, contendo 569 casos reais de punção aspirativa por agulha fina (PAAF), com 30 atributos descrevendo geometria e textura dos núcleos celulares. 

Adotamos extremo rigor metodológico: o rótulo foi corrigido para que a classe positiva seja o caso maligno, e dividimos o dataset em **80% para treino (455 amostras) e 20% para teste final cego (114 amostras)** com estratificação. A padronização dos dados e imputação foram ajustadas exclusivamente dentro dos pipelines de treino, eliminando qualquer risco de vazamento de dados (*data leakage*).

Com validação cruzada estratificada de 5 folds e busca em grade de hiperparâmetros, comparamos quatro algoritmos: **Regressão Logística, Random Forest, Gradient Boosting e XGBoost**. Os quatro obtiveram desempenho excelente, acima de 97% de acurácia.

**Por que escolhemos a Regressão Logística calibrada para produção?**  
Porque em triagem médica, precisávamos de um modelo intrinsecamente calibrado, com excelente probabilidade contínua (Brier Score de 0,021) e comportamento convexo previsível. 

Mais importante: **por que a acurácia é insuficiente?**  
Em triagem de câncer, um falso positivo gera um exame complementar de ultrassom; já um falso negativo atrasa o tratamento de uma paciente doente, com risco de vida. Por isso, definimos um **limiar de segurança de 0,09**, focado em **Recall**. 

No teste cego com 114 casos não vistos, o modelo atingiu **Recall de 97,6%**, capturando **41 de 42 casos malignos com apenas 1 falso negativo**, precisão de 85,4% e área sob a curva ROC de 0,996.

*(Transição de tela: Gráfico de barras SHAP)*  
Para abrir a 'caixa-preta', integramos a biblioteca **SHAP**. Para cada exame, o profissional visualiza exatamente quais características aumentaram o risco — como pior número de pontos côncavos e pior perímetro — ou reduziram a suspeita, garantindo total explicabilidade clínica."

---

### 6:00 – 8:00 · Bloco 4: Base de Protocolos (RAG), LLM e Guardrails
*(Tela: Estrutura da pasta `data/kb/` com os arquivos Markdown e diagrama do fluxo RAG)*

**Fala:**  
"A literatura médica e os fluxos de regulação são essenciais para orientar a conduta do profissional. Por isso, implementamos um motor de **RAG (Retrieval-Augmented Generation)** fundamentado em uma base de conhecimento própria com 7 documentos oficiais em Markdown:
1. Diretrizes de Rastreamento do Câncer de Mama (INCA/MS);
2. Sinais e Sintomas de Alerta;
3. Classificação e Condutas BI-RADS;
4. Interpretação Citológica de PAAF;
5. Governança e Limites da IA na Saúde;
6. Linhas de Cuidado e Fluxos de Encaminhamento no SUS;
7. Fatores de Risco e Histórico Familiar.

Esses documentos foram segmentados em 29 trechos temáticos indexados por **TF-IDF e similaridade por cosseno**. Em nossa suíte de testes de recuperação, o RAG atingiu **100% de Hit@1 e Hit@3**, rejeitando automaticamente perguntas fora do escopo.

A **LLM (Claude 3.5 Sonnet via Anthropic)** recebe um prompt estruturado em XML contendo os dados do caso, os sinais de alerta e os trechos recuperados do RAG. Caso ocorra indisponibilidade de rede ou ausência de chave de API, entra em ação nosso **mecanismo offline determinístico**, garantindo que a aplicação jamais pare de funcionar.

E nos **guardrails**, aplicamos sanitização bidirecional: na entrada, mascaramos CPFs e telefones e detectamos injeção de prompt; na saída, bloqueamos qualquer afirmativa categórica de diagnóstico ou prescrição farmacológica."

---

### 8:00 – 11:30 · Bloco 5: Demonstração Prática ao Vivo (Jornada Completa)
*(Tela: Navegador com o Streamlit em `http://localhost:8501`)*

**Passo 1 — Autenticação e Perfis (≈0:40):**  
*(Na tela: Efetuar login com usuário `admin` e senha `TroqueEstaSenha123`)*  
"Vamos demonstrar a jornada completa na prática. Acessamos a aplicação em `localhost:8501`. O sistema conta com controle de acesso baseado em papéis (RBAC). Fazemos login com a conta de administrador. As senhas usam hash bcrypt com 12 rounds, bloqueio temporário de 15 minutos após 5 erros e expiração automática de sessão."

**Passo 2 — Entrada de Dados e Mascaramento de PII (≈0:45):**  
*(Na tela: Clicar em '🩺 Nova análise', selecionar 'Exemplo maligno' e colar o relato)*  
"Na tela de Nova Análise, informamos o código pseudonimizado `CASO-TRIAGEM-2026`. Para agilidade, selecionamos o exemplo maligno do dataset público, que preenche as 30 variáveis citológicas nas abas de Médias, Desvios e Piores Valores. 
No campo de relato livre, digitamos propositalmente dados pessoais e clínicos:  
*'Paciente de 54 anos apresenta nódulo endurecido no quadrante superior da mama direita e secreção. Contato: maria@email.com e CPF 123.456.789-00.'*"

**Passo 3 — Execução da IA e Explicabilidade (≈0:45):**  
*(Na tela: Clicar no botão 'Analisar' e aguardar o resultado)*  
"Clicamos em Analisar. Em segundos, o LangGraph executa o fluxo:
Vejam o resultado: Faixa de Risco **🔴 ALTO**, probabilidade estimada de 98,2% (muito acima do limiar seguro de 0,09).
Ao lado, o gráfico SHAP demonstra que o *pior número de pontos côncavos* e o *pior raio* foram determinantes para a classificação.
Abaixo, o relatório da LLM sintetiza a situação e cita as fontes oficiais do RAG recuperadas. E notem o alerta de segurança: **o CPF e o e-mail foram mascarados automaticamente como `[CPF]` e `[EMAIL]`**, preservando a privacidade da paciente perante a LGPD."

**Passo 4 — Homologação da Decisão Médica Final (≈0:50):**  
*(Na tela: Descer até o card '⚖️ Decisão Final do(a) Médico(a)')*  
"Aqui está o diferencial ético implementado em nossa solução: o card de **Decisão Médica Final**.  
Destacamos a diretriz mandatória do edital: **'A decisão final sempre deverá permanecer com uma pessoa responsável pelo atendimento'**.
O médico responsável seleciona o parecer: *'Concordo com a análise — Investigação prioritária (Alto Risco)'*, informa o seu registro profissional *'CRM/SP 123456'*, detalha a conduta: *'Solicitada mamografia diagnóstica bilateral e encaminhamento prioritário ao mastologista para biópsia'* e confirma a ciência do termo de responsabilidade.
Clicamos em **Gravar Decisão Médica Final**. O caso é homologado imediatamente e gravado com carimbo de tempo!"

**Passo 5 — Assistente RAG de Protocolos (≈0:30):**  
*(Na tela: Acessar a aba '💬 Assistente' e fazer uma pergunta)*  
"Na aba do Assistente de Protocolos, o profissional pode sanar dúvidas a qualquer momento. Digitamos: *'Qual a conduta para achado BI-RADS categoria 4?'*. A LLM consulta a base RAG e responde com exatidão citando a cartilha `03_birads.md`: indicação de investigação histopatológica com biópsia."

---

### 11:30 – 13:15 · Bloco 6: Governança, Trilha de Auditoria e API REST
*(Tela: Aba '🗂️ Histórico' e depois '🔍 Auditoria')*

**Fala:**  
"Na aba de **Histórico**, temos a visão completa de todos os atendimentos. Vejam que a tabela destaca claramente quais casos já foram homologados com `✅ [Decisão médica]` e quais ainda estão pendentes. Ao selecionar um caso pendente, o médico pode registrar sua decisão diretamente pelo histórico.

*(Transição de tela: Aba '🔍 Auditoria')*  
Na aba de **Auditoria**, implementamos um mecanismo inspirado em **blockchain**: cada login, análise, pergunta ao assistente e decisão médica é registrado com um **hash SHA-256 encadeado**. O sistema recalcula os elos da cadeia em tempo real e exibe: **'Cadeia de hashes íntegra ✔'**. Se qualquer invasor tentar adulterar um dado diretamente no SQLite, o sistema identifica instantaneamente em qual ID ocorreu a violação.

*(Transição de tela: Navegador em `http://localhost:8000/docs`)*  
Além da interface visual, containerizamos e disponibilizamos uma **API RESTful completa em FastAPI**, documentada via Swagger UI em `/docs`. Ela oferece autenticação Bearer JWT e endpoints para predições (`/analyses`), consultas ao RAG (`/ask`) e homologação de revisões médicas (`/analyses/{id}/review`)."

---

### 13:15 – 14:15 · Bloco 7: Containerização e Testes Automatizados
*(Tela: Terminal executando `pytest` e mostrando os arquivos Docker)*

**Fala:**  
"A solução foi totalmente containerizada com **Dockerfile multi-estágio e docker-compose.yml**, com isolamento em usuário não-root, healthchecks e volumes persistentes, além de um script facilitador `scripts/run_docker.sh`.

*(Na tela: Executar no terminal: `PYTHONPATH=src .venv/bin/pytest -v`)*  
Para comprovar a robustez e confiabilidade de todo o código, desenvolvemos uma suíte com **14 testes automatizados com pytest**.  
Eles testam: regras de senhas fortes, proteção de hashes, política de lockout após falhas, ciclo de vida de tokens JWT, permissões RBAC, fluxo completo maligno e benigno, divergência entre modelo e relato clínico, sanitização de PII e injeções de prompt, guardrails de saída, acurácia do RAG, integridade e detecção de adulteração na auditoria, endpoints da API e **o teste específico da homologação da decisão médica final**.

Como vocês podem ver na tela, **todos os 14 testes executam com 100% de sucesso!**"

---

### 14:15 – 15:00 · Bloco 8: Limitações, "Tradução para Leigos" e Conclusão
*(Tela: PDF do Relatório Técnico mostrando a capa e a caixa amarela 'Tradução para Leigos')*

**Fala:**  
"Como contribuição pedagógica em nosso Relatório Técnico e no arquivo Word preenchido, incluímos ao final de cada uma das seções o quadro **'💡 Tradução para Leigos'**, permitindo que gestores, avaliadores e profissionais de saúde compreendam conceitos complexos de IA em linguagem acessível.

Como limitações conscientes, ressaltamos que o dataset UCI WDBC é didático e pequeno, não dispensando validação clínica multicêntrica futura.

Em suma, a Guardiã AI cumpre todos os requisitos do Hackathon, entregando um produto completo que une **Dados, Machine Learning, SHAP, RAG, LLM, Governança, API e Aplicação Web**, com a certeza de que a Inteligência Artificial deve somar forças ao profissional, assegurando que **a decisão final sempre permanecerá com uma pessoa responsável pelo atendimento**.

Muito obrigado a todos!"

---

## 📋 Checklist Pré-Gravação (Garanta o Vídeo Perfeito)

- [ ] **Ambiente Pronto:** Certifique-se de que o Streamlit está rodando em `localhost:8501` e a API em `localhost:8000`.
- [ ] **Credenciais:** Teste o login com `admin` e senha `TroqueEstaSenha123`.
- [ ] **Janelas Pré-Abertas no Navegador:**
  1. Aba 1: `http://localhost:8501` (Interface da Guardiã AI deslogada ou na tela de login).
  2. Aba 2: `http://localhost:8000/docs` (Swagger da API FastAPI).
  3. Aba 3: Visualizador do PDF do Relatório Técnico (`Relatorio_Tecnico_Guardia_AI.pdf` aberto nas figuras de arquitetura e "Tradução para Leigos").
- [ ] **Terminal Pronto:** Janela de terminal aberta na pasta do projeto com o comando `PYTHONPATH=src .venv/bin/pytest -v` pronto para ser disparado.
- [ ] **Casos de Teste Memorizados:**
  - Caso Maligno: `CASO-TRIAGEM-2026` com relato contendo CPF para mostrar o mascaramento de PII.
  - Pergunta no RAG: *"Qual a conduta para achado BI-RADS categoria 4?"*.
  - Homologação Médica: Digitar CRM e conduta para demonstrar o registro na auditoria.
- [ ] **Cronômetro:** Mantenha um cronômetro visível durante a gravação para cravar entre **14m 00s e 14m 50s**, garantindo conformidade com o teto de 15 minutos do edital.
