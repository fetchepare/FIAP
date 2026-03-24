"""
Sistema de Roteamento Inteligente para Saúde da Mulher
Interface com Streamlit
"""

import streamlit as st
import random
import numpy as np
import pandas as pd
import plotly.graph_objects as go
# Configuração da página 
st.set_page_config(
    page_title="Roteamento Inteligente - Saúde da Mulher",
    page_icon="🚑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========================
# CORES POR PRIORIDADE
# ========================
CORES = {
    1: "#FF3232",  # Emergência - Vermelho
    2: "#FF9600",  # Violência - Laranja
    3: "#64C8FF",  # Hormonal - Azul Claro
    4: "#32C832",  # Pós-parto - Verde
}

NOMES_PRIORIDADE = {
    1: "Emergência Obstétrica",
    2: "Violência Doméstica",
    3: "Medicamentos Hormonais",
    4: "Pós-parto"
}

# ========================
# DADOS SINTÉTICOS
# ========================
pacientes = [
    {'id': 1, 'x': 150, 'y': 200, 'prioridade': 1, 'tipo': 'emergencia', 'nome': 'Maria Silva', 'tempo_max': 80},
    {'id': 2, 'x': 400, 'y': 100, 'prioridade': 4, 'tipo': 'pos_parto', 'nome': 'Ana Oliveira', 'janela': (20, 150)},
    {'id': 3, 'x': 600, 'y': 450, 'prioridade': 2, 'tipo': 'violencia', 'nome': 'Carla Souza'},
    {'id': 4, 'x': 250, 'y': 400, 'prioridade': 3, 'tipo': 'hormonal', 'nome': 'Beatriz Lima', 'tempo_max': 120},
    {'id': 5, 'x': 500, 'y': 300, 'prioridade': 1, 'tipo': 'emergencia', 'nome': 'Fernanda Costa', 'tempo_max': 60},
    {'id': 6, 'x': 700, 'y': 200, 'prioridade': 3, 'tipo': 'hormonal', 'nome': 'Patrícia Rocha', 'tempo_max': 100},
    {'id': 7, 'x': 100, 'y': 500, 'prioridade': 2, 'tipo': 'violencia', 'nome': 'Roberta Alves'},
    {'id': 8, 'x': 350, 'y': 250, 'prioridade': 4, 'tipo': 'pos_parto', 'nome': 'Juliana Mendes', 'janela': (50, 250)},
    {'id': 9, 'x': 750, 'y': 550, 'prioridade': 1, 'tipo': 'emergencia', 'nome': 'Tatiana Ferreira', 'tempo_max': 90},
    {'id': 10, 'x': 800, 'y': 100, 'prioridade': 3, 'tipo': 'hormonal', 'nome': 'Renata Cardoso', 'tempo_max': 150}
]

deposito = {'id': 0, 'x': 450, 'y': 580, 'nome': 'Base Central'}

# Parâmetros
num_veiculos = 3
capacidade = 4
distancia_max_por_veiculo = 800

# ========================
# FUNÇÕES DE DISTÂNCIA E FITNESS
# ========================
def calcular_distancia(a, b):
    return np.sqrt((a['x'] - b['x'])**2 + (a['y'] - b['y'])**2)

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
        distancia_veiculo = 0

        for idp in rota:
            p = pacientes[idp - 1]
            d = calcular_distancia(ponto, p)
            dist_total += d
            distancia_veiculo += d
            tempo += d
            tipo = p['tipo']
            prioridade = p['prioridade']
            
            if prioridade == 1:
                penalidade += tempo * 200
            elif prioridade == 2:
                penalidade += tempo * 100
            elif prioridade == 3:
                penalidade += tempo * 50
            elif prioridade == 4:
                penalidade += tempo * 10

            if tipo == "emergencia":
                if 'tempo_max' in p and tempo > p['tempo_max']:
                    penalidade += 10000
            elif tipo == "violencia":
                if ordem > 3:
                    penalidade += 3000
            elif tipo == "hormonal":
                if 'tempo_max' in p and tempo > p['tempo_max']:
                    penalidade += 5000
            elif tipo == "pos_parto":
                if 'janela' in p:
                    ini, fim = p['janela']
                    if tempo < ini or tempo > fim:
                        penalidade += 4000

            ponto = p
            ordem += 1

        dist_retorno = calcular_distancia(ponto, deposito)
        distancia_veiculo += dist_retorno
        dist_total += dist_retorno

        if distancia_veiculo > distancia_max_por_veiculo:
            penalidade += 5000 * (distancia_veiculo - distancia_max_por_veiculo)

    return dist_total + penalidade

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

def algoritmo_genetico(progress_callback=None):
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
    historico = []

    for g in range(geracoes):
        fits = [fitness(p) for p in pop]
        min_fit = min(fits)

        if min_fit < melhor_fit:
            melhor_fit = min_fit
            melhor = pop[fits.index(min_fit)]
        
        historico.append(melhor_fit)

        if progress_callback:
            progress_callback(g, geracoes, melhor_fit)

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

    return melhor, melhor_fit, historico

def desenhar_rotas(melhor_rota):
    """Cria um mapa interativo com as rotas otimizadas"""
    fig = go.Figure()
    
    cores_frota = ['#1f77b4', '#ff7f0e', '#2ca02c']
    i = 0
    
    for v in range(num_veiculos):
        rota = melhor_rota[i:i + capacidade]
        rota = [x for x in rota if x != -1]
        
        if rota:
            coords_x = [deposito['x']]
            coords_y = [deposito['y']]
            
            for idp in rota:
                p = pacientes[idp - 1]
                coords_x.append(p['x'])
                coords_y.append(p['y'])
            
            coords_x.append(deposito['x'])
            coords_y.append(deposito['y'])
            
            fig.add_trace(go.Scatter(
                x=coords_x, y=coords_y,
                mode='lines+markers',
                name=f'Veículo {v+1}',
                line=dict(color=cores_frota[v], width=3),
                marker=dict(size=8, symbol='circle')
            ))
        
        i += capacidade
    
    for p in pacientes:
        fig.add_trace(go.Scatter(
            x=[p['x']], y=[p['y']],
            mode='markers+text',
            name=f"{NOMES_PRIORIDADE[p['prioridade']]}",
            marker=dict(size=15, color=CORES[p['prioridade']], symbol='circle', line=dict(width=2, color='black')),
            text=[f"{p['id']}"],
            textposition="middle center",
            textfont=dict(color="white", size=12),
            hovertext=f"<b>{p['nome']}</b><br>ID: {p['id']}<br>{NOMES_PRIORIDADE[p['prioridade']]}",
            hoverinfo='text'
        ))
    
    fig.add_trace(go.Scatter(
        x=[deposito['x']], y=[deposito['y']],
        mode='markers+text',
        name='Base',
        marker=dict(size=20, color='gold', symbol='star', line=dict(width=2, color='black')),
        text=['BASE'],
        textposition="top center",
        textfont=dict(color="black", size=12)
    ))
    
    fig.update_layout(
        title='Mapa de Rotas Otimizadas',
        xaxis=dict(title='Coordenada X', range=[0, 900], showgrid=True),
        yaxis=dict(title='Coordenada Y', range=[0, 650], showgrid=True),
        hovermode='closest',
        plot_bgcolor='white',
        width=900,
        height=650
    )
    
    return fig

def analisar_rotas(melhor_rota):
    """Gera análise detalhada das rotas"""
    analise = []
    i = 0
    
    for v in range(num_veiculos):
        rota = melhor_rota[i:i + capacidade]
        rota = [x for x in rota if x != -1]
        
        if rota:
            distancia_total = 0
            ponto = deposito
            
            for idp in rota:
                p = pacientes[idp - 1]
                d = calcular_distancia(ponto, p)
                distancia_total += d
                ponto = p
            
            distancia_total += calcular_distancia(ponto, deposito)
            
            analise.append({
                'veiculo': v + 1,
                'pacientes': [p['id'] for p in [pacientes[id-1] for id in rota]],
                'nomes': [p['nome'] for p in [pacientes[id-1] for id in rota]],
                'prioridades': [p['prioridade'] for p in [pacientes[id-1] for id in rota]],
                'distancia_total': distancia_total,
                'num_pacientes': len(rota)
            })
        
        i += capacidade
    
    return analise

# ========================
# INTERFACE STREAMLIT
# ========================
def main():
    # Sidebar
    with st.sidebar:
        st.title("🚑 Roteamento Inteligente")
        st.markdown("### Saúde da Mulher")
        st.markdown("---")
        
        st.markdown("#### Parâmetros")
        st.metric("Veículos", num_veiculos)
        st.metric("Capacidade/Veículo", capacidade)
        st.metric("Distância Máxima", f"{distancia_max_por_veiculo}")
        
        st.markdown("---")
        st.markdown("#### Prioridades")
        for prio, nome in NOMES_PRIORIDADE.items():
            st.markdown(f"🔴 **{prio}** - {nome}")
        
        st.markdown("---")
        executar_btn = st.button("🚀 Executar Otimização", type="primary", use_container_width=True)
    
    # Título
    st.title("🏥 Sistema de Roteamento Inteligente")
    st.markdown("### Otimização de Atendimentos para Saúde da Mulher")
    st.markdown("---")
    
    # Execução (Calcula antes de renderizar as abas)
    if executar_btn:
        with st.spinner("🔄 Executando Algoritmo Genético..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def update_progress(g, total, fitness_val):
                progress = (g + 1) / total
                progress_bar.progress(progress)
                status_text.text(f"Geração {g+1}/{total} - Fitness: {fitness_val:.2f}")
            
            melhor_rota, melhor_fit, historico = algoritmo_genetico(update_progress)
            analise = analisar_rotas(melhor_rota)
            
            st.session_state['melhor_rota'] = melhor_rota
            st.session_state['melhor_fit'] = melhor_fit
            st.session_state['historico'] = historico
            st.session_state['analise'] = analise
            
            progress_bar.empty()
            status_text.empty()
            st.success("✅ Otimização concluída!")

    # Abas
    tab1, tab2, tab3 = st.tabs(["🗺️ Mapa de Rotas", "📈 Evolução", "📋 Análise"])
    
    with tab1:
        if 'melhor_rota' in st.session_state:
            fig = desenhar_rotas(st.session_state['melhor_rota'])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Clique em 'Executar Otimização' no menu lateral.")
    
    with tab2:
        if 'historico' in st.session_state:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=list(range(len(st.session_state['historico']))),
                y=st.session_state['historico'],
                mode='lines',
                name='Fitness',
                line=dict(color='red', width=2)
            ))
            fig.update_layout(
                title='Evolução do Fitness',
                xaxis_title='Geração',
                yaxis_title='Fitness',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Gerações", len(st.session_state['historico']))
            with col2:
                st.metric("Fitness Inicial", f"{st.session_state['historico'][0]:.2f}")
            with col3:
                st.metric("Fitness Final", f"{st.session_state['historico'][-1]:.2f}")
        else:
            st.info("Execute a otimização primeiro.")
    
    with tab3:
        if 'analise' in st.session_state:
            for item in st.session_state['analise']:
                with st.expander(f"🚚 Veículo {item['veiculo']} - {item['num_pacientes']} pacientes | {item['distancia_total']:.1f} unidades"):
                    df = pd.DataFrame({
                        'ID': item['pacientes'],
                        'Nome': item['nomes'],
                        'Prioridade': item['prioridades']
                    })
                    st.dataframe(df, use_container_width=True)
        else:
            st.info("Execute a otimização primeiro.")

if __name__ == "__main__":
    main()