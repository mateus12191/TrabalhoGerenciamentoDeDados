import streamlit as st
from pyspark.sql import SparkSession 
import pandas as pd
import matplotlib.pyplot as plt

sp = SparkSession.builder.appName("Brasileirao").getOrCreate()

st.title("Análises do Brasileirão")

@st.cache_resource
def load_data():
    df = (
        sp.read
        .option("header", True)
        .option("inferSchema", True)
        .csv("DatasetBrasileirao2003.csv")
    )
    return df

@st.cache_data
def toPandas():
    return df_spark.toPandas()

df_spark = load_data()

df = toPandas()
dfToFilter = df

anos = ["Todos"] + sorted(df["ano_campeonato"].unique())
ano = st.sidebar.selectbox("Selecione o Ano",anos)

if ano == "Todos":
   dfToFilter = df

else:
    dfToFilter = dfToFilter[dfToFilter["ano_campeonato"]==ano]

# Mandante ou visistante
opcao = st.sidebar.selectbox("Escolha o tipo de time:", ("Mandante", "Visitante"))

# Caixa de seleção dos times
if opcao == "Mandante":
    tipo = ("time_mandante", "gols_mandante")
    
else:
    tipo = ("time_visitante", "gols_visitante")

times = ["Todos"] + sorted(df[tipo[0]].unique())
time = st.sidebar.selectbox("Selecione o time:", times)

# Cálculo da média de gols

media_gols = (
    dfToFilter.groupby(tipo[0])[tipo[1]]
    .mean()
    .sort_values()
)

# Escolhendo o Ano








# 1) Se NÃO escolher time
if time == "Todos":

    st.subheader(f"Média de gols por time {opcao}")

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(media_gols.index, media_gols.values)
    ax.set_xticklabels(media_gols.index, rotation=90)
    ax.set_title(f"Média de gols por time {opcao}")
    ax.set_xlabel("Time")
    ax.set_ylabel("Média de gols")

    st.pyplot(fig)

# 2) Se escolher um time
else:
    st.subheader(f"Média de gols do {time} como {opcao} por ano")

    # Média apenas do time selecionado
    media_ano = (
        df[df[tipo[0]] == time]
        .groupby("ano_campeonato")[tipo[1]]
        .mean()
        .sort_index()
    )

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(media_ano.index, media_ano.values, marker="o")
    ax.set_title(f"Média de gols por ano — {time}")
    ax.set_xlabel("Ano")
    ax.set_ylabel("Média de gols")

    st.pyplot(fig)
