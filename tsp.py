import pygame
from pygame.locals import *
import random
import sys
import numpy as np
import os
import threading
from google import genai
from dotenv import load_dotenv

# Carrega as variáveis do .env
load_dotenv()

# pygame is used for visualization.

# ========================
# INICIALIZAÇÃO DO PYGAME
# ========================
pygame.init()
LARGURA, ALTURA = 900, 650
TELA = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Roteamento Inteligente – Saúde da Mulher")
clock = pygame.time.Clock()
FPS = 30

# ========================
# CORES POR PRIORIDADE
# ========================
BRANCO = (255, 255, 255)
PRETO = (0, 0, 0)
VERMELHO = (255, 50, 50)     # 1 - Emergência
LARANJA = (255, 150, 0)      # 2 - Violência
AZUL_CLARO = (100, 200, 255) # 3 - Hormonal
VERDE = (50, 200, 50)        # 4 - Pós-parto
CINZA = (200, 200, 200)
AMARELO = (255, 255, 0)
ROXO = (150, 0, 255)
AZUL = (50, 150, 255)

# ========================
# DADOS SINTÉTICOS E REGRAS
# ========================
# Prioridades restritas:
# 1 - Emergência obstétrica (prioridade máxima)
# 2 - Violência doméstica (com protocolos especiais)
# 3 - Medicamentos hormonais (temperatura controlada)
# 4 - Pós-parto (janelas de tempo)

pacientes = [
    {'id': 1, 'x': 150, 'y': 200, 'prioridade': 1, 'tipo': 'emergencia', 'tempo_max': 80},
    {'id': 2, 'x': 400, 'y': 100, 'prioridade': 4, 'tipo': 'pos_parto', 'janela': (20, 150)},
    {'id': 3, 'x': 600, 'y': 450, 'prioridade': 2, 'tipo': 'violencia'},
    {'id': 4, 'x': 250, 'y': 400, 'prioridade': 3, 'tipo': 'hormonal', 'tempo_max': 120},
    {'id': 5, 'x': 500, 'y': 300, 'prioridade': 1, 'tipo': 'emergencia', 'tempo_max': 60},
    {'id': 6, 'x': 700, 'y': 200, 'prioridade': 3, 'tipo': 'hormonal', 'tempo_max': 100},
    {'id': 7, 'x': 100, 'y': 500, 'prioridade': 2, 'tipo': 'violencia'},
    {'id': 8, 'x': 350, 'y': 250, 'prioridade': 4, 'tipo': 'pos_parto', 'janela': (50, 250)},
    {'id': 9, 'x': 750, 'y': 550, 'prioridade': 1, 'tipo': 'emergencia', 'tempo_max': 90},
    {'id': 10, 'x': 800, 'y': 100, 'prioridade': 3, 'tipo': 'hormonal', 'tempo_max': 150}
]

deposito = {'id': 0, 'x': 450, 'y': 580}

# Restrições adicionais (Capacidade do veículo e múltiplos veículos)
num_veiculos = 3
capacidade = 4

# ========================
# DISTÂNCIA
# ========================
def calcular_distancia(a, b):
    return np.sqrt((a['x'] - b['x'])**2 + (a['y'] - b['y'])**2)

# ========================
# FITNESS COM RESTRIÇÕES
# ========================
def fitness(cromossomo):
    rotas = []
    i = 0
    for v in range(num_veiculos):
        r = cromossomo[i:i + capacidade]
        rotas.append([x for x in r if x != -1])
        i += capacidade

    dist_total = 0
    penalidade = 0

    for rota in rotas:
        ponto = deposito
        tempo = 0
        ordem = 1

        for idp in rota:
            p = pacientes[idp - 1]
            d = calcular_distancia(ponto, p)
            dist_total += d
            tempo += d
            tipo = p['tipo']
            prioridade = p['prioridade']
            
            # Penalidade baseada na prioridade orgânica (quanto mais crítico, maior o peso do tempo esperado)
            # Prioridade 1 (Emergência) x200
            # Prioridade 2 (Violência) x100
            # Prioridade 3 (Hormonal) x50
            # Prioridade 4 (Pós-parto) x10
            if prioridade == 1:
                penalidade += tempo * 200
            elif prioridade == 2:
                penalidade += tempo * 100
            elif prioridade == 3:
                penalidade += tempo * 50
            elif prioridade == 4:
                penalidade += tempo * 10

            # ----------------
            # RESTRIÇÕES ESPECÍFICAS
            # ----------------

            # Emergência obstétrica
            if tipo == "emergencia":
                if 'tempo_max' in p and tempo > p['tempo_max']:
                    penalidade += 10000

            # Violência doméstica
            elif tipo == "violencia":
                # Protocolo: de preferência ser um dos 3 primeiros atendimentos na rota
                if ordem > 3:
                    penalidade += 3000

            # Medicamento hormonal
            elif tipo == "hormonal":
                # Temperatura controlada, limite de tempo até a entrega
                if 'tempo_max' in p and tempo > p['tempo_max']:
                    penalidade += 5000

            # Pós-parto com janela
            elif tipo == "pos_parto":
                if 'janela' in p:
                    ini, fim = p['janela']
                    if tempo < ini or tempo > fim:
                        penalidade += 4000

            ponto = p
            ordem += 1

        # Retorno ao depósito
        dist_total += calcular_distancia(ponto, deposito)

    return dist_total + penalidade

# ========================
# OPERADORES GENÉTICOS
# ========================
def selecao_torneio(pop, fit):
    nova = []
    for _ in range(len(pop)):
        i, j = random.sample(range(len(pop)), 2)
        if fit[i] < fit[j]:
            nova.append(pop[i])
        else:
            nova.append(pop[j])
    return nova

def crossover_ox(p1, p2):
    size = len(p1)
    a, b = sorted(random.sample(range(size), 2))
    filho = [-1] * size
    filho[a:b] = p1[a:b]
    pos = b
    for g in p2:
        if g not in filho:
            if pos >= size:
                pos = 0
            filho[pos] = g
            pos += 1
    return filho

def mutacao_swap(c):
    c = c.copy()
    if random.random() < 0.2:
        i, j = random.sample(range(len(c)), 2)
        c[i], c[j] = c[j], c[i]
    return c

# ========================
# VISUALIZAÇÃO
# ========================
def desenhar_mapa(melhor_rota, geracao, fit):
    TELA.fill(BRANCO)

    for x in range(0, LARGURA, 50):
        pygame.draw.line(TELA, CINZA, (x, 0), (x, ALTURA), 1)
    for y in range(0, ALTURA, 50):
        pygame.draw.line(TELA, CINZA, (0, y), (LARGURA, y), 1)

    pygame.draw.circle(TELA, PRETO, (deposito['x'], deposito['y']), 15)
    pygame.draw.circle(TELA, AMARELO, (deposito['x'], deposito['y']), 12)

    fonte = pygame.font.Font(None, 22)
    TELA.blit(fonte.render("Base", True, PRETO), (deposito['x'] - 18, deposito['y'] - 30))

    for p in pacientes:
        if p['tipo'] == "emergencia":
            cor = VERMELHO
        elif p['tipo'] == "violencia":
            cor = LARANJA
        elif p['tipo'] == "hormonal":
            cor = AZUL_CLARO
        elif p['tipo'] == "pos_parto":
            cor = VERDE

        pygame.draw.circle(TELA, cor, (p['x'], p['y']), 12)
        pygame.draw.circle(TELA, PRETO, (p['x'], p['y']), 12, 1)

        txt = fonte.render(str(p['id']), True, PRETO)
        TELA.blit(txt, (p['x'] - 6, p['y'] - 8))

    if melhor_rota:
        cores_frota = [AZUL, ROXO, (255, 120, 120)]
        i = 0
        for v in range(num_veiculos):
            rota = melhor_rota[i:i + capacidade]
            rota = [x for x in rota if x != -1]
            if rota:
                p1 = deposito
                for r in rota:
                    p2 = pacientes[r - 1]
                    pygame.draw.line(TELA, cores_frota[v], (p1['x'], p1['y']), (p2['x'], p2['y']), 3)
                    p1 = p2
                pygame.draw.line(TELA, cores_frota[v], (p1['x'], p1['y']), (deposito['x'], deposito['y']), 3)
            i += capacidade

    info = pygame.font.Font(None, 24)
    TELA.blit(info.render(f"Geração: {geracao}", True, PRETO), (10, 10))
    TELA.blit(info.render(f"Fitness: {fit:.2f}", True, PRETO), (10, 35))

    legenda_y = 65
    TELA.blit(info.render("Vermelho: Emergência (Prio 1)", True, VERMELHO), (10, legenda_y))
    TELA.blit(info.render("Laranja: Violência (Prio 2)", True, LARANJA), (10, legenda_y + 25))
    TELA.blit(info.render("Azul Claro: Hormonal (Prio 3)", True, AZUL_CLARO), (10, legenda_y + 50))
    TELA.blit(info.render("Verde: Pós-parto (Prio 4)", True, VERDE), (10, legenda_y + 75))

    pygame.display.flip()

# ========================
# ALGORITMO GENÉTICO
# ========================
def algoritmo_genetico():
    tamanho_cromossomo = num_veiculos * capacidade
    num_p = len(pacientes)
    pop_size = 100
    geracoes = 300
    pop = []

    for _ in range(pop_size):
        c = list(range(1, num_p + 1))
        random.shuffle(c)
        while len(c) < tamanho_cromossomo:
            c.append(-1)
        pop.append(c[:tamanho_cromossomo])

    melhor = None
    melhor_fit = float('inf')

    for g in range(geracoes):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        fits = [fitness(p) for p in pop]
        min_fit = min(fits)

        if min_fit < melhor_fit:
            melhor_fit = min_fit
            melhor = pop[fits.index(min_fit)]

        if g % 5 == 0:
            desenhar_mapa(melhor, g, melhor_fit)
            clock.tick(FPS)

        sel = selecao_torneio(pop, fits)
        nova_pop = []

        for i in range(0, len(sel), 2):
            p1 = sel[i]
            p2 = sel[(i + 1) % len(sel)]
            f1 = crossover_ox(p1, p2)
            f2 = crossover_ox(p2, p1)
            nova_pop.append(mutacao_swap(f1))
            nova_pop.append(mutacao_swap(f2))

        pop = nova_pop[:pop_size]

    return melhor, melhor_fit

# ========================
# INTEGRAÇÃO COM LLMs
# ========================

# ========================
# INTEGRAÇÃO COM LLMs
# ========================
def gerar_recursos_llm(melhor_rota, pacientes_dados, deposito_pos):
    """
    Gera o manual de instruções usando a LLM pré-treinada (Google GenAI API)
    """
    import os
    from google import genai
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("\n" + "="*60)
        print("AVISO: Chave da API do Gemini não encontrada!")
        print("Configure a variável de ambiente 'GEMINI_API_KEY' com a sua chave")
        print("para executar a integração com o modelo.")
        print("="*60)
        return None

    client = genai.Client(api_key=api_key)

    prompt = "Você é um assistente de IA focado na logística de atendimento para saúde da mulher.\n"
    prompt += "Abaixo está o resultado otimizado do algoritmo de roteamento:\n"
    
    i = 0
    for v in range(num_veiculos):
        rota = melhor_rota[i:i + capacidade]
        rota = [x for x in rota if x != -1]
        
        if len(rota) > 0:
            prompt += f"\nVeículo {v + 1}:\n"
            ponto_atual = deposito_pos
            tempo_acumulado = 0
            
            for idp in rota:
                p = pacientes_dados[idp - 1]
                d = calcular_distancia(ponto_atual, p)
                tempo_acumulado += d
                prompt += f"- Parada ID {p['id']} ({p['tipo'].upper()}) | Prioridade: {p['prioridade']} | Distância Acumulada: {tempo_acumulado:.1f}\n"
                ponto_atual = p
        i += capacidade

    prompt += "\nCom base nos dados fornecidos, por favor, gere o seguinte recurso essencial:\n"
    prompt += "**Manual de instruções para a equipe de transporte**: com base na sequência de pontos otimizada, a LLM deve gerar um documento que funcione como um manual prático que a equipe teria em mãos durante o percurso. Este manual deve conter instruções específicas e sensíveis ao contexto para cada tipo de atendimento na rota. Defina quais instruções são apropriadas para cada tipo de situação, considerando as particularidades da saúde da mulher e os diferentes contextos de atendimento.\n"

    print("\n" + "="*60)
    print("INTEGRAÇÃO COM LLM - GERANDO MANUAL DE INSTRUÇÕES...")
    print("="*60)
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        print("\nRESPOSTA DO GEMINI:\n")
        print(response.text)
        print("="*60)
        
        with open("manual_instrucoes.md", "w", encoding="utf-8") as f:
            f.write(response.text)
        print("\n-> O manual gerado foi salvo no arquivo 'manual_instrucoes.md'")
            
        return response.text
        
    except Exception as e:
        print("\nErro ao chamar a API do Gemini:", e)
        print("="*60)
        return None

# ========================
# MAIN
# ========================
def main():
    print("Iniciando otimização genética das rotas médicas...")
    melhor_rota, fit = algoritmo_genetico()

    print("\nMelhor rota (índices):", melhor_rota)
    print(f"Fitness Final (Distância + Penalidades): {fit:.2f}")

    print("\n============================================================")
    print("MAPA GERADO COM SUCESSO!")
    print("Visualize as rotas no mapa que abriu em uma nova janela.")
    print("-> FECHE a janela do mapa para INICIAR A GERAÇÃO DO MANUAL.")
    print("============================================================")
    
    rodando = True
    while rodando:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                rodando = False
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    rodando = False
        desenhar_mapa(melhor_rota, "FINAL", fit)
        clock.tick(FPS)

    pygame.quit()
    
    gerar_recursos_llm(melhor_rota, pacientes, deposito)

if __name__ == "__main__":
    main()
