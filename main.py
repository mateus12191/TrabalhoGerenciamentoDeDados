import streamlit as st
from pyspark.sql import SparkSession 
import pandas as pd
import matplotlib.pyplot as plt
from st_clickable_images import clickable_images 
from carregaImagens import carregaImagens, NOMES_UNIFICADOS

# Configuração da Sessão Spark
sp = SparkSession.builder.appName("Brasileirao").getOrCreate()

st.title("Análises do Brasileirão")


@st.cache_resource
def load_data():
  
    if not hasattr(load_data, "mock"): 
         return sp.read.option("header", True).option("inferSchema", True).csv("DatasetBrasileirao2003.csv")
    return None

@st.cache_data
def toPandas(_df_spark):
    return _df_spark.toPandas()

df_spark = load_data()
df = toPandas(df_spark)


if not df.empty:
    df["time_mandante"] = df["time_mandante"].str.strip().replace(NOMES_UNIFICADOS)


@st.cache_data
def preparar_imagens(times_unicos):
    l_nomes = []
    l_imgs = []
    carregaImagens(times_unicos, l_nomes, l_imgs)
    return l_nomes, l_imgs

lista_nomes = []
lista_imagens = []

if not df.empty:
    # Passamos os times já limpos e unificados
    lista_nomes, lista_imagens = preparar_imagens(df["time_mandante"].unique())

# --- 4. FILTROS ---
anos = ["Todos"] + sorted(df["ano_campeonato"].unique())
ano = st.selectbox("Selecione o Ano", anos)

dfToFilter = df.copy()
if ano != "Todos":
    dfToFilter = dfToFilter[dfToFilter["ano_campeonato"] == ano]


media_gols = (
    dfToFilter.groupby("time_mandante")["gols_mandante"]
    .mean()
    .sort_values()
)

st.write("---")
st.subheader("Selecione um time:")


if 'img_key' not in st.session_state:
    st.session_state['img_key'] = 0


if st.button("Ver todos os times (Limpar seleção)"):
    st.session_state['img_key'] += 1
    st.rerun() 


clicked_index = clickable_images(
    paths=lista_imagens, 
    titles=lista_nomes,
    div_style={
        "display": "flex",
        "justify-content": "center",
        "flex-wrap": "wrap",
        "background-color": "#f9f9f9",
        "padding": "10px",
        "border-radius": "10px"
    },
    img_style={
        "margin": "5px",
        "height": "60px",  
        "object-fit": "contain", 
        "cursor": "pointer",
        ":hover": {"transform": "scale(1.1)"} 
    },
    key=f"image_div_{st.session_state['img_key']}" 
)


time_selecionado = "Todos"

if clicked_index > -1:
    time_selecionado = lista_nomes[clicked_index]
    st.markdown(f"**Time Selecionado:** {time_selecionado}")



if time_selecionado == "Todos":
    st.subheader("Média de gols por time mandante")
    
    if not media_gols.empty:
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.bar(media_gols.index, media_gols.values)
        ax.set_xticklabels(media_gols.index, rotation=90)
        ax.set_title("Média de gols por time mandante")
        ax.set_xlabel("Time")
        ax.set_ylabel("Média de gols")
        st.pyplot(fig)

else:
    st.subheader(f"Média de gols do {time_selecionado} como mandante por ano")


    media_ano = (
        df[df["time_mandante"] == time_selecionado]
        .groupby("ano_campeonato")["gols_mandante"]
        .mean()
        .sort_index()
    )

    if not media_ano.empty:
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(media_ano.index.astype(str), media_ano.values, marker="o")
        ax.set_title(f"Média de gols por ano — {time_selecionado}")
        ax.set_xlabel("Ano")
        ax.set_ylabel("Média de gols")
        st.pyplot(fig)
    else:
        st.warning(f"Sem dados para {time_selecionado}")