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

# Cálculo da média de gols
media_gols = (
    df.groupby("time_mandante")["gols_mandante"]
    .mean()
    .sort_values()
)
# Caixa de seleção dos times
times = ["Todos"] + sorted(df["time_mandante"].unique())
time = st.selectbox("Selecione o time:", times)

# 1) Se NÃO escolher time
if time == "Todos":

    st.subheader("Média de gols por time mandante")

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(media_gols.index, media_gols.values)
    ax.set_xticklabels(media_gols.index, rotation=90)
    ax.set_title("Média de gols por time mandante")
    ax.set_xlabel("Time")
    ax.set_ylabel("Média de gols")

    st.pyplot(fig)

# 2) Se escolher um time
else:
    st.subheader(f"Média de gols do {time} como mandande por ano")

    # Média apenas do time selecionado
    media_ano = (
        df[df["time_mandante"] == time]
        .groupby("ano_campeonato")["gols_mandante"]
        .mean()
        .sort_index()
    )

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(media_ano.index, media_ano.values, marker="o")
    ax.set_title(f"Média de gols por ano — {time}")
    ax.set_xlabel("Ano")
    ax.set_ylabel("Média de gols")

    st.pyplot(fig)
