import streamlit as st
from pyspark.sql import SparkSession 
import pandas as pd
import matplotlib.pyplot as plt
from st_clickable_images import clickable_images 
from carregaImagens import carregaImagens, NOMES_UNIFICADOS
import plotly.express as px

# Configuração da Página
st.set_page_config(layout="wide", page_title="Brasileirão Analytics")

# Configuração da Sessão Spark
sp = SparkSession.builder.appName("Brasileirao").getOrCreate()

st.title("⚽ Análises do Brasileirão")

# --- 1. CARGA DE DADOS ---
@st.cache_resource
def load_data():
    if not hasattr(load_data, "mock"): 
         return sp.read.option("header", True).option("inferSchema", True).csv("DatasetBrasileirao2003.csv")
    return None

@st.cache_data
def toPandas(_df_spark):
    if _df_spark:
        return _df_spark.toPandas()
    return pd.DataFrame() 

df_spark = load_data()
df = toPandas(df_spark)

# --- 2. LIMPEZA DOS NOMES ---
if not df.empty:
    df["time_mandante"] = df["time_mandante"].str.strip().replace(NOMES_UNIFICADOS)
    df["time_visitante"] = df["time_visitante"].str.strip().replace(NOMES_UNIFICADOS)

# --- 3. IMAGENS (CACHEADA) ---
@st.cache_data
def preparar_imagens(times_unicos):
    l_nomes = []
    l_imgs = []
    carregaImagens(times_unicos, l_nomes, l_imgs)
    return l_nomes, l_imgs

lista_nomes = []
lista_imagens = []

if not df.empty:
    # Pega times unicos (tanto mandante quanto visitante para garantir todos)
    todos_times = pd.concat([df["time_mandante"], df["time_visitante"]]).unique()
    lista_nomes, lista_imagens = preparar_imagens(todos_times)

# --- 4. FILTROS GLOBAIS (SIDEBAR) ---
st.sidebar.header("Filtros")
anos = ["Todos"] + sorted(df["ano_campeonato"].unique())
ano = st.sidebar.selectbox("Selecione o Ano", anos)

opcao = st.sidebar.selectbox("Foco da Análise:", ("Mandante", "Visitante"))

if opcao == "Mandante":
    tipo = ("time_mandante", "gols_mandante")
else:
    tipo = ("time_visitante", "gols_visitante")

# Cria dataframe filtrado pelo ano (usado globalmente)
dfToFilter = df.copy()
if ano != "Todos":
    dfToFilter = dfToFilter[dfToFilter["ano_campeonato"] == ano]

# =========================================================
# ESTRUTURA DE ABAS
# =========================================================
tab_geral, tab_times, tab_sobre = st.tabs(["🌎 Visão Geral", "🔍 Por Time", "ℹ️ Sobre"])

# ---------------------------------------------------------
# ABA 1: VISÃO GERAL (Gráficos de todos os times)
# ---------------------------------------------------------
with tab_geral:
    st.header(f"Panorama Geral - {ano}")
    
    col1, col2 = st.columns(2)
    
    # GRÁFICO 1: MÉDIA DE GOLS
    with col1:
        st.subheader(f"Média de gols ({opcao})")
        media_gols = (
            dfToFilter.groupby(tipo[0])[tipo[1]]
            .mean()
            .sort_values()
        )

        if not media_gols.empty:
            fig, ax = plt.subplots(figsize=(10, 8)) # Ajustei tamanho
            ax.barh(media_gols.index, media_gols.values, color="skyblue") # Mudei para barh (horizontal) fica melhor pra ler nomes
            ax.set_title(f"Média de Gols")
            ax.set_xlabel("Gols")
            st.pyplot(fig)
    
    # GRÁFICO 2: MÉDIA DE PÚBLICO
    with col2:
        if ano == "Todos":
            st.subheader(f"Média de Público ({opcao})")
            publico_medio = (
                dfToFilter[dfToFilter["publico"] > 0]
                .groupby(tipo[0])["publico"]
                .mean()
                .sort_values()
            )
            
            fig1, ax1 = plt.subplots(figsize=(10, 8))
            ax1.barh(publico_medio.index, publico_medio.values, color="salmon")
            ax1.set_title(f"Público Médio")
            ax1.set_xlabel("Pessoas")
            st.pyplot(fig1)
        else:
            st.info("Selecione 'Todos' os anos para ver o ranking geral de público.")

# ---------------------------------------------------------
# ABA 2: POR TIME (Seleção + Detalhes)
# ---------------------------------------------------------
with tab_times:
    st.header("Análise Detalhada por Clube")
    
    # 1. SELETOR DE IMAGENS
    if 'img_key' not in st.session_state:
        st.session_state['img_key'] = 0

    if st.button("Limpar Seleção"):
        st.session_state['img_key'] += 1
        st.rerun()

    clicked_index = clickable_images(
        paths=lista_imagens, 
        titles=lista_nomes,
        div_style={
            "display": "flex", "justify-content": "center", "flex-wrap": "wrap",
            "background-color": "#f0f2f6", "padding": "10px", "border-radius": "10px"
        },
        img_style={
            "margin": "5px", "height": "50px", "object-fit": "contain", 
            "cursor": "pointer", ":hover": {"transform": "scale(1.1)"} 
        },
        key=f"image_div_{st.session_state['img_key']}" 
    )

    # 2. LÓGICA DE EXIBIÇÃO DO TIME
    if clicked_index > -1:
        time_selecionado = lista_nomes[clicked_index]
        st.divider()
        st.markdown(f"### 📊 Estatísticas do **{time_selecionado}**")

        # Filtra apenas jogos do time selecionado
        df_time = df[df[tipo[0]] == time_selecionado].copy()
        if ano != "Todos":
            df_time = df_time[df_time["ano_campeonato"] == ano]

        if df_time.empty:
            st.warning(f"Sem dados para {time_selecionado} com os filtros atuais.")
        else:
            # Definição do Eixo X
            if ano == "Todos":
                coluna_agrupamento = "ano_campeonato"
                label_x = "Ano"
            else:
                coluna_agrupamento = "rodada"
                label_x = "Rodada"

            # --- PLOTS DE MATPLOTLIB (Gols e Público) ---
            c1, c2 = st.columns(2)
            
            with c1:
                # GOLS
                media_gols_time = df_time.groupby(coluna_agrupamento)[tipo[1]].mean().sort_index()
                fig_g, ax_g = plt.subplots(figsize=(8, 4))
                ax_g.plot(media_gols_time.index.astype(int), media_gols_time.values, marker="o", color="blue")
                ax_g.set_title("Média de Gols")
                ax_g.set_xlabel(label_x)
                ax_g.grid(True, alpha=0.3)
                st.pyplot(fig_g)

            with c2:
                # PÚBLICO
                colunas_possiveis = ["publico", "publico_pagante"]
                coluna_publico = next((c for c in colunas_possiveis if c in df_time.columns), None)
                
                if coluna_publico:
                    media_publico = df_time[df_time[coluna_agrupamento] > 0].groupby(coluna_agrupamento)[coluna_publico].mean().sort_index()
                    fig_p, ax_p = plt.subplots(figsize=(8, 4))
                    ax_p.plot(media_publico.index.astype(int), media_publico.values, marker="o", color="green")
                    ax_p.set_title("Média de Público")
                    ax_p.set_xlabel(label_x)
                    ax_p.grid(True, alpha=0.3)
                    st.pyplot(fig_p)
                else:
                    st.info("Dados de público indisponíveis.")

      
            st.subheader("📈 Trajetória no Campeonato")
            
            if ano != "Todos":
        
                df_home = dfToFilter[dfToFilter["time_mandante"] == time_selecionado][["rodada", "colocacao_mandante"]].rename(columns={"colocacao_mandante": "colocacao"})
                df_away = dfToFilter[dfToFilter["time_visitante"] == time_selecionado][["rodada", "colocacao_visitante"]].rename(columns={"colocacao_visitante": "colocacao"})
                
                df_full_season = pd.concat([df_home, df_away]).sort_values("rodada")
                
                if not df_full_season.empty:
                    fig_evo = px.line(
                        df_full_season, 
                        x="rodada", 
                        y="colocacao", 
                        markers=True,
                        title=f"Evolução da Posição - {time_selecionado} ({ano})"
                    )
                  
                    fig_evo.update_yaxes(autorange="reversed", range=[21, 0]) 
                    st.plotly_chart(fig_evo, use_container_width=True)
                else:
                    st.warning("Dados de colocação não encontrados para este time neste ano.")
            else:
                st.info("Selecione um ano específico para ver a evolução rodada a rodada.")

    else:
        st.info("👆 Clique em um escudo acima para ver as estatísticas.")

# ---------------------------------------------------------
# ABA 3: SOBRE
# ---------------------------------------------------------
with tab_sobre:
    st.header("Sobre o Dashboard")
    st.write("""
        Este dashboard utiliza dados históricos do Campeonato Brasileiro (Série A).
        Tecnologias utilizadas:
        - **PySpark**: Processamento de dados
        - **Streamlit**: Interface Web
        - **Pandas/Matplotlib/Plotly**: Visualização
    """)