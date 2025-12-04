import streamlit as st
from pyspark.sql import SparkSession 
import pandas as pd
import matplotlib.pyplot as plt
from st_clickable_images import clickable_images 
from carregaImagens import carregaImagens, NOMES_UNIFICADOS

# Configuração da Sessão Spark
sp = SparkSession.builder.appName("Brasileirao").getOrCreate()

st.title("Análises do Brasileirão")

# --- 1. CARGA DE DADOS ---
@st.cache_resource
def load_data():
    # Mock para evitar erro se o arquivo não existir no meu ambiente de teste
    if not hasattr(load_data, "mock"): 
         return sp.read.option("header", True).option("inferSchema", True).csv("DatasetBrasileirao2003.csv")
    return None

@st.cache_data
def toPandas(_df_spark):
    return _df_spark.toPandas()

df_spark = load_data()
df = toPandas(df_spark)

# --- 2. LIMPEZA DOS NOMES ---
if not df.empty:
    # Unifica nomes (Ex: Santos FC -> Santos)
    df["time_mandante"] = df["time_mandante"].str.strip().replace(NOMES_UNIFICADOS)

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
    lista_nomes, lista_imagens = preparar_imagens(df["time_mandante"].unique())

# --- 4. FILTRO DE ANO ---
anos = ["Todos"] + sorted(df["ano_campeonato"].unique())
ano = st.sidebar.selectbox("Selecione o Ano", anos)

# Cria dataframe filtrado pelo ano (usado no gráfico geral)
dfToFilter = df.copy()
if ano != "Todos":
    dfToFilter = dfToFilter[dfToFilter["ano_campeonato"] == ano]

opcao = st.sidebar.selectbox("Escolha o tipo de time:", ("Mandante", "Visitante"))
# --- 6. Caixa de seleção dos times ---

if opcao == "Mandante":
    tipo = ("time_mandante", "gols_mandante")
    
else:
    tipo = ("time_visitante", "gols_visitante")

# --- 6. SELEÇÃO DE TIME (VISUAL) ---
st.write("---")
st.subheader("Selecione um time:")

# Inicializa chave para resetar imagens
if 'img_key' not in st.session_state:
    st.session_state['img_key'] = 0

# Botão de Reset
if st.button("Ver todos os times (Limpar seleção)"):
    st.session_state['img_key'] += 1
    st.rerun() 

# Componente Clickable Images
clicked_index = clickable_images(
    paths=lista_imagens, 
    titles=lista_nomes,
    div_style={
        "display": "flex", "justify-content": "center", "flex-wrap": "wrap",
        "background-color": "#f9f9f9", "padding": "10px", "border-radius": "10px"
    },
    img_style={
        "margin": "5px", "height": "60px", "object-fit": "contain", 
        "cursor": "pointer", ":hover": {"transform": "scale(1.1)"} 
    },
    key=f"image_div_{st.session_state['img_key']}" 
)

# Define qual time está selecionado
time_selecionado = "Todos"
if clicked_index > -1:
    time_selecionado = lista_nomes[clicked_index]
    st.markdown(f"**Time Selecionado:** {time_selecionado}")

# =========================================================
# LÓGICA DE PLOTAGEM
# =========================================================

# CENÁRIO 1: NENHUM TIME SELECIONADO (VISÃO GERAL)
if time_selecionado == "Todos":
    # media de gols de todos os times
    st.subheader(f"Média de gols por time {opcao} (Geral)")

    #Agrupa pelo time mandante ou visitante
    media_gols = (
    dfToFilter.groupby(tipo[0])[tipo[1]]
    .mean()
    .sort_values()
    )

    if not media_gols.empty:
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.bar(media_gols.index, media_gols.values)
        ax.set_xticklabels(media_gols.index, rotation=90)
        ax.set_title(f"Média de gols por time {opcao}")
        ax.set_xlabel("Time")
        ax.set_ylabel("Média de gols")

        st.pyplot(fig)

    # Média de publico
    if ano == "Todos":

        publico_medio = (dfToFilter[dfToFilter["publico"] > 0]
        .groupby(tipo[0])["publico"].
        mean()
        .sort_values())
        
        fig1, ax1 = plt.subplots(figsize=(12, 6))
        st.subheader(f"Média de publico por time {opcao}")
        ax1.bar(publico_medio.index, publico_medio.values)
        ax1.set_xticklabels(publico_medio.index, rotation=90)
        ax1.set_title(f"Público médio por time {opcao}")
        ax1.set_xlabel("Time")
        ax1.set_ylabel("Público médio")
        
        st.pyplot(fig1)

# CENÁRIO 2: TIME ESPECÍFICO SELECIONADO
else:
    st.subheader(f"Estatísticas: {time_selecionado} como {opcao}")
    
    # 1. Filtra apenas os jogos desse time como mandante
    df_time = df[df[tipo[0]] == time_selecionado].copy()

    # Se um ano específico foi escolhido lá em cima, filtramos também pelo ano
    if ano != "Todos":
        df_time = df_time[df_time["ano_campeonato"] == ano]

    if df_time.empty:
        st.warning(f"Sem dados para {time_selecionado} no filtro selecionado.")
        
    else:
        # --- DEFINIÇÃO DINÂMICA DO EIXO X ---
        # Se selecionou "Todos" os anos -> Eixo X é o ANO
        # Se selecionou um ano específico -> Eixo X é a RODADA
        if ano == "Todos":
            coluna_agrupamento = "ano_campeonato"
            label_x = "Ano"
        else:
            coluna_agrupamento = "rodada"
            label_x = "Rodada"

        # --- GRÁFICO 1: MÉDIA DE GOLS ---
        media_gols_time = (
            df_time.groupby(coluna_agrupamento)[tipo[1]]
            .mean()
            .sort_index()
        )
        
        fig, ax = plt.subplots(figsize=(12, 5))
        # astype(int) garante que o ano/rodada não apareça como 2003.0
        ax.plot(media_gols_time.index.astype(int), media_gols_time.values, marker="o", color="blue")
        ax.set_title(f"Média de Gols - {time_selecionado}")
        ax.set_xlabel(label_x)
        ax.set_ylabel("Média de Gols")
        ax.set_xticks(media_gols_time.index.astype(int)) # Força ticks inteiros
        st.pyplot(fig)

        # --- GRÁFICO 2: MÉDIA DE PÚBLICO ---
        # Verifica se existe coluna de publico antes de tentar plotar
        colunas_possiveis = ["publico", "publico_pagante"]
        coluna_publico = next((c for c in colunas_possiveis if c in df_time.columns), None)

        if coluna_publico:
            media_publico = (
                df_time[df_time[coluna_agrupamento] > 0.0]
                .groupby(coluna_agrupamento)[coluna_publico]
                .mean()
                .sort_index()
            )
            print(media_publico)
            st.subheader(f"Média de Público por {label_x}")
            fig1, ax1 = plt.subplots(figsize=(12, 5))
            ax1.plot(media_publico.index.astype(int), media_publico.values, marker="o", color="green")
            ax1.set_title(f"Público - {time_selecionado}")
            ax1.set_xlabel(label_x)
            ax1.set_ylabel("Público Médio")
            ax1.set_xticks(media_publico.index.astype(int)) # Força ticks inteiros
            st.pyplot(fig1)
        else:
            st.info("Dados de público não disponíveis neste dataset.")