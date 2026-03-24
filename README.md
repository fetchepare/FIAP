# Roteamento Inteligente – Saúde da Mulher

Este projeto resolve um problema de roteamento de veículos focado em rotas de saúde da mulher utilizando Algoritmos Genéticos. O código adere rigorosamente às restrições definidas no PRD:

## Funcionalidades
- **Algoritmo Genético Customizado**: Otimização de rotas com cromossomos baseados em permutação, seleção por torneio, crossover OX e mutação de swap.
- **Priorização de Atendimento Obrigatória**:
  1. Emergências obstétricas (Prioridade Máxima)
  2. Violência doméstica 
  3. Medicamentos hormonais
  4. Atendimento pós-parto
- **Restrições Adicionais Implementadas**:
  - Capacidade do Veículo (Frota com 3 veículos)
  - Múltiplos Veículos / Problema de Roteamento de Veículos (VRP)
  - Janelas de tempo e tempos máximos de atendimento
- **Integração Simulada com LLM**: Ao final do processamento, o sistema gera o prompt ideal para criar um Manual de Instruções, um Roteiro de Visitas e um Sistema de Chat Contextualizado.
- **Interface Gráfica Pygame**: Visualização em tempo real das rotas com cores mapeadas para as prioridades.

## Instalação e Execução
Criar um arquivo .env na mesma pasta do arquivo "tsp.py" com o seguinte conteúdo: 
GEMINI_API_KEY=<<sua chave API do Gemini>>

Recomenda-se o uso de um ambiente virtual (venv):

```bash
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate no Windows
pip install -r requirements.txt
python tsp.py
```

## Controles
- Acompanhe a evolução do fitness no terminal e na tela gráfica.
- Pressione `ESC` ou feche a janela do Pygame a qualquer momento para abortar a simulação ou sair ao final.

