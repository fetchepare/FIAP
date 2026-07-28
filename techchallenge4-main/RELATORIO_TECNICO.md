# Relatório Técnico — Tech Challenge Fase 4
## Sistema de IA Multimodal para Saúde e Segurança da Mulher

Este relatório técnico detalha a especificação da solução de IA multimodal desenvolvida, descrevendo o fluxo de dados, a arquitetura de modelos, a fusão tardia (late fusion) implementada, e os resultados empíricos obtidos na validação dos cenários.

---

## 1. Descrição do fluxo multimodal

A arquitetura adota uma abordagem de late fusion (fusão tardia). Cada modalidade física de dados é processada de modo autônomo por modelos isolados antes de alimentar a camada de fusão.

O fluxo unificado de dados ocorre da seguinte forma:

1. **Entrada de dados**: Vídeo da consulta ou procedimento cirúrgico, gravação de áudio do relato da paciente, e os sinais vitais coletados em tempo real (PA, BCF) ou registros de prescrições.
2. **Análise de vídeo**: Processado a cada 30 frames pelo detector YOLOv8 customizado (para instrumentação ou áreas críticas), segmentação cromática HSV (para quantificação de sangramento), e MediaPipe (para mapeamento de postura de autoproteção e evitação visual).
3. **Análise de áudio**: O sinal de áudio passa pela transcrição para texto em português via API de Speech-to-Text (Google Cloud Speech). O texto resultante alimenta o modelo de Processamento de Linguagem Natural (Azure AI Language - Text Analytics for Health) para detecção de entidades clínicas. Em paralelo, a prosódia do áudio é extraída com `librosa` (pitch, entonação, jitter e pausas).
4. **Análise de sinais vitais**: Analisado contra limiares baseados em diretrizes obstétricas nacionais para detecção de anomalias (como hipertensão gestacional e sofrimento fetal agudo).
5. **Motor de fusão multimodal**: Recebe os scores independentes e calcula um score ponderado de risco para cada uma das categorias:
   - *Saúde materna*
   - *Complicação cirúrgica*
   - *Violência doméstica*
   - *Saúde psicológica*
   - *Anomalia ginecológica*
6. **Despacho de alertas**: Se o risco global da fusão for avaliado como **Alto** ou **Crítico**, a solução despacha notificações por e-mail (via Azure Communication Services) e alertas em tempo real no painel para as equipes especializadas associadas.

---

## 2. Modelos de IA aplicados por modalidade

### 2.1 Análise de vídeo
* **YOLOv8 (Ultralytics)**: Carrega um modelo pré-treinado customizado para detecção de pinças ginecológicas, espéculos, bisturis, e órgãos críticos (útero, ovário, mamas). Auxilia na marcação automática de trechos com intercorrências cirúrgicas.
* **Segmentação HSV**: Algoritmo que mascara e quantifica a proporção de pixels vermelhos no frame (indicando volume relativo de sangramento).
* **MediaPipe Landmark Detection**: Mapeia vetores espaciais da paciente para capturar indicadores faciais (tensão facial, frequência de piscadas) e corporais (retração de tronco, ombros elevados indicando dor ou medo).

### 2.2 Análise de áudio
* **Speech-to-Text (Google Cloud)**: Mapeia o áudio em texto.
* **Azure AI Language (Text Analytics for Health)**: Analisa semanticamente a transcrição em busca de conceitos médicos (ex.: "dor", "depressão", "sangramento", "medo") para alimentar as regras de risco.
* **Classificador vocal de risco**: Um classificador linear que mapeia parâmetros prosódicos (energia vocal, jitter, velocidade de fala e pausas) a estados emocionais e cognitivos (ansiedade gestacional, sintomas vocais de depressão perinatal e trauma).

### 2.3 Análise de sinais vitais
* **Detector determinístico**: Valida se a pressão diastólica e sistólica violam limites de hipertensão gestacional severa (≥ 160/110 mmHg) ou indicam tendências crescentes consecutivas (aumento de 15 mmHg de forma persistente). Valida batimentos cardíacos fetais abaixo de 110 bpm ou acima de 160 bpm. Monitora dosagem hormonal prescrita comparada a limites máximos tolerados.

---

## 3. Resultados obtidos e casos clínicos validados

A solução foi validada com 5 cenários clínicos pré-populados:

| Paciente | Contexto | Sinais Vitais | Áudio / Texto | Vídeo | Risco Geral | Alertas Gerados |
|---|---|---|---|---|---|---|
| **Maria Silva** | Pré-Natal | PA com subida progressiva e proteinúria leve | Ansiedade expressa e taquilalia | Não aplicável | **Alto** (Maternal) | Alerta de suspeita de pré-eclâmpsia para obstetrícia de plantão |
| **Ana Costa** | Pós-Parto | Normotensa (PA 111/72 mmHg) | Sintomas graves de depressão e tom vocal monótono | Não aplicável | **Alto** (Psicológico) | Alerta encaminhado para Psicologia Perinatal |
| **Julia Santos** | Triagem Violência | Sinais estáveis | Relato de medo ("Tenho medo dele, ele controla tudo") | Linguagem corporal de autoproteção e evitação | **Alto** (Violência Doméstica) | Alerta para Serviço Social e Psicologia |
| **Carla Oliveira**| Consulta Ginec. | Estável, usando estradiol regulado | Normal | Sem anomalias | **Baixo** | Nenhum |
| **Patricia Lima** | Cirurgia / Pré-Natal| PA Crítica (165/112 mmHg) + Sofrimento fetal agudo (BCF 95 bpm) | Sem gravação | Sangramento anômalo detectado no vídeo cirúrgico (score 0.22) | **Crítico** | Despacho imediato de e-mail e alerta crítico no painel clínico |

---

## 4. Conclusão

A arquitetura desenvolvida:
1. Processa áudio, vídeo e sinais vitais individualmente e de forma fundida.
2. Adota YOLOv8 para detecção de objetos/estruturas médicas.
3. Classifica riscos específicos da saúde e segurança feminina de forma sensível (depressão pós-parto, ansiedade, violência doméstica, fadiga hormonal, pré-eclâmpsia).
4. É integrado a serviços em nuvem gerenciados (Azure AI Language e Azure Communication Services).
5. Mantém fallbacks inteligentes (modo demo) na ausência de chaves de nuvem ou pacotes locais complexos, garantindo a exibição e funcionalidade total do painel de monitoramento.
