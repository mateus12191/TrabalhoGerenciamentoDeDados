import streamlit as st
from pyspark.sql import SparkSession 
import pandas as pd
import matplotlib.pyplot as plt
from st_clickable_images import clickable_images 
import plotly.express as px

try:
    from carregaImagens import carregaImagens, NOMES_UNIFICADOS
except ImportError:
    st.error("Arquivo 'carregaImagens.py' não encontrado. Verifique a estrutura.")
    NOMES_UNIFICADOS = {}
    def carregaImagens(times, nomes, imgs):
        pass


st.set_page_config(layout="wide", page_title="Brasileirão Analytics")
sp = SparkSession.builder.appName("Brasileirao").getOrCreate()

st.title("⚽ Análises do Brasileirão")


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

# Limpeza e Padronização dos Nomes
if not df.empty:
    df["time_mandante"] = df["time_mandante"].str.strip().replace(NOMES_UNIFICADOS)
    df["time_visitante"] = df["time_visitante"].str.strip().replace(NOMES_UNIFICADOS)

# Preparação das Imagens (Cache)
@st.cache_data
def preparar_imagens(times_unicos):
    l_nomes = []
    l_imgs = []
    try:
        carregaImagens(times_unicos, l_nomes, l_imgs)
    except:
        pass
    return l_nomes, l_imgs

lista_nomes = []
lista_imagens = []

if not df.empty:
    todos_times = pd.concat([df["time_mandante"], df["time_visitante"]]).unique()
    lista_nomes, lista_imagens = preparar_imagens(todos_times)

# =========================================================
# 2. FILTROS (SIDEBAR)
# =========================================================
st.sidebar.header("Filtros")

anos = ["Todos"] + sorted(df["ano_campeonato"].unique())
ano = st.sidebar.selectbox("Selecione o Ano", anos)

# --- NOVA LÓGICA DE SELEÇÃO (INCLUINDO "TODOS") ---
opcoes_foco = ("Todos", "Mandante", "Visitante")
opcao = st.sidebar.selectbox("Foco da Análise:", opcoes_foco)

# Filtra pelo ano primeiro (Global)
dfToFilter = df.copy()
if ano != "Todos":
    dfToFilter = dfToFilter[dfToFilter["ano_campeonato"] == ano]


def criar_dataframe_padronizado(df_orig, foco):
    lista_dfs = []
    
    colunas_base = ['ano_campeonato', 'rodada', 'data', 'estadio']
    # Verifica colunas opcionais
    tem_publico = 'publico' in df_orig.columns
    if tem_publico: colunas_base.append('publico')
    
    # 1. Processa MANDANTES
    if foco in ["Mandante", "Todos"]:
        df_m = df_orig.copy()
        df_m['time'] = df_m['time_mandante']
        df_m['gols_pro'] = df_m['gols_mandante']
        df_m['gols_contra'] = df_m['gols_visitante']
        df_m['tecnico'] = df_m.get('tecnico_mandante', None)
        
        # Lógica de Vitória Mandante
        df_m['resultado_final'] = df_m.apply(
            lambda x: 'V' if x['gols_mandante'] > x['gols_visitante'] else 
                     ('D' if x['gols_mandante'] < x['gols_visitante'] else 'E'), axis=1
        )
        lista_dfs.append(df_m[colunas_base + ['time', 'gols_pro', 'gols_contra', 'tecnico', 'resultado_final']])

    # 2. Processa VISITANTES
    if foco in ["Visitante", "Todos"]:
        df_v = df_orig.copy()
        df_v['time'] = df_v['time_visitante']
        df_v['gols_pro'] = df_v['gols_visitante']
        df_v['gols_contra'] = df_v['gols_mandante']
        df_v['tecnico'] = df_v.get('tecnico_visitante', None)
        
        # Lógica de Vitória Visitante (Invertida)
        df_v['resultado_final'] = df_v.apply(
            lambda x: 'V' if x['gols_visitante'] > x['gols_mandante'] else 
                     ('D' if x['gols_visitante'] < x['gols_mandante'] else 'E'), axis=1
        )
        lista_dfs.append(df_v[colunas_base + ['time', 'gols_pro', 'gols_contra', 'tecnico', 'resultado_final']])

    return pd.concat(lista_dfs).reset_index(drop=True)

# Gera o DataFrame Analítico baseado na escolha
df_analise = criar_dataframe_padronizado(dfToFilter, opcao)

# =========================================================
# 4. VISUALIZAÇÃO (USANDO df_analise)
# =========================================================
tab_geral, tab_times, tab_tecnicos, tab_sobre = st.tabs(["🌎 Visão Geral", "🔍 Por Time", "👨‍🏫 Técnicos", "ℹ️ Sobre"])

# ---------------------------------------------------------
# ABA 1: VISÃO GERAL
# ---------------------------------------------------------
with tab_geral:
    st.header(f"Panorama Geral - {ano} ({opcao})")
    
    col1, col2 = st.columns(2)
    
    # GRÁFICO: MÉDIA DE GOLS
    with col1:
        st.subheader("Média de Gols Marcados")
        # Agrupa pelo nome padronizado "time"
        media_gols = df_analise.groupby("time")["gols_pro"].mean().sort_values()

        if not media_gols.empty:
            fig, ax = plt.subplots(figsize=(10, 8))
            ax.barh(media_gols.index, media_gols.values, color="skyblue")
            ax.set_title(f"Média de Gols - {opcao}")
            ax.set_xlabel("Gols")
            st.pyplot(fig)
    
    # GRÁFICO: MÉDIA DE PÚBLICO
    with col2:
        if 'publico' in df_analise.columns:
            if ano == "Todos":
                st.subheader("Média de Público")
                publico_medio = df_analise[df_analise['publico'] > 0].groupby("time")['publico'].mean().sort_values()
                
                fig1, ax1 = plt.subplots(figsize=(10, 8))
                ax1.barh(publico_medio.index, publico_medio.values, color="salmon")
                ax1.set_title("Público Médio")
                st.pyplot(fig1)
            else:
                st.info("Selecione 'Todos' os anos para ver o ranking de público.")
        else:
            st.warning("Dados de público não encontrados.")

    st.divider()
    c3, c4 = st.columns(2)
    
    # GRÁFICOS DE RESULTADOS (AGORA USA A COLUNA PADRONIZADA 'resultado_final')
    with c3:
        st.subheader("Top Vitórias")
        vitorias = df_analise[df_analise["resultado_final"] == "V"].groupby("time")["resultado_final"].count().sort_values(ascending=False).head(10)
        fig2, ax2 = plt.subplots()
        ax2.bar(vitorias.index, vitorias.values, color='green')
        plt.xticks(rotation=45, ha='right')
        st.pyplot(fig2)

    with c4:
        st.subheader("Top Derrotas")
        derrotas = df_analise[df_analise["resultado_final"] == "D"].groupby("time")["resultado_final"].count().sort_values(ascending=False).head(10)
        fig3, ax3 = plt.subplots()
        ax3.bar(derrotas.index, derrotas.values, color='red')
        plt.xticks(rotation=45, ha='right')
        st.pyplot(fig3)

# ---------------------------------------------------------
# ABA 2: POR TIME
# ---------------------------------------------------------
with tab_times:
    st.header("Análise Detalhada por Clube")
    
    if 'img_key' not in st.session_state: st.session_state['img_key'] = 0

    if st.button("Limpar Seleção"):
        st.session_state['img_key'] += 1
        st.rerun()

    clicked_index = clickable_images(
        paths=lista_imagens, 
        titles=lista_nomes,
        div_style={"display": "flex", "justify-content": "center", "flex-wrap": "wrap", "background-color": "#f0f2f6", "padding": "10px", "border-radius": "10px"},
        img_style={"margin": "5px", "height": "50px", "object-fit": "contain", "cursor": "pointer", ":hover": {"transform": "scale(1.1)"}},
        key=f"image_div_{st.session_state['img_key']}" 
    )

    if clicked_index > -1:
        time_selecionado = lista_nomes[clicked_index]
        st.divider()
        st.markdown(f"### 📊 Estatísticas: **{time_selecionado}** ({opcao})")

        # Filtra no DF PADRONIZADO (Muito mais simples!)
        df_time = df_analise[df_analise['time'] == time_selecionado].copy()
        
        if df_time.empty:
            st.warning(f"Sem dados para {time_selecionado} neste filtro.")
        else:
            if ano == "Todos":
                coluna_agrupamento = "ano_campeonato"
                label_x = "Ano"
            else:
                coluna_agrupamento = "rodada"
                label_x = "Rodada"

            c_g, c_p = st.columns(2)
            
            with c_g:
                media_gols_time = df_time.groupby(coluna_agrupamento)["gols_pro"].mean().sort_index()
                fig_g, ax_g = plt.subplots(figsize=(8, 4))
                ax_g.plot(media_gols_time.index.astype(int), media_gols_time.values, marker="o", color="blue")
                ax_g.set_title("Média de Gols")
                ax_g.set_xlabel(label_x)
                ax_g.grid(True, alpha=0.3)
                st.pyplot(fig_g)

            with c_p:
                if 'publico' in df_time.columns:
                    media_pub_time = df_time[df_time['publico'] > 0].groupby(coluna_agrupamento)['publico'].mean().sort_index()
                    fig_p, ax_p = plt.subplots(figsize=(8, 4))
                    ax_p.plot(media_pub_time.index.astype(int), media_pub_time.values, marker="o", color="green")
                    ax_p.set_title("Média de Público")
                    ax_p.set_xlabel(label_x)
                    ax_p.grid(True, alpha=0.3)
                    st.pyplot(fig_p)

            # Evolução (Plotly)
            # Nota: Para evolução, mantemos o cálculo original que já considera o campeonato todo
            st.subheader("📈 Evolução no Campeonato")
            if ano != "Todos":
                # Filtra do DF original para pegar a posição independente de mandante/visitante
                df_pos = dfToFilter[(dfToFilter['time_mandante'] == time_selecionado) | (dfToFilter['time_visitante'] == time_selecionado)].copy()
                
                # Lógica para extrair a posição correta da linha
                def get_posicao(row):
                    if row['time_mandante'] == time_selecionado: return row['colocacao_mandante']
                    if row['time_visitante'] == time_selecionado: return row['colocacao_visitante']
                    return None
                
                if 'colocacao_mandante' in df_pos.columns:
                    df_pos['colocacao_real'] = df_pos.apply(get_posicao, axis=1)
                    df_pos = df_pos.sort_values('rodada').dropna(subset=['colocacao_real'])
                    
                    if not df_pos.empty:
                        fig_evo = px.line(df_pos, x="rodada", y="colocacao_real", markers=True, title=f"Posição por Rodada ({ano})")
                        fig_evo.update_yaxes(autorange="reversed", range=[21, 0])
                        st.plotly_chart(fig_evo, use_container_width=True)
                    else:
                        st.info("Dados de colocação indisponíveis.")
            else:
                st.info("Selecione um ano específico para ver o gráfico de evolução.")
    else:
        st.info("👆 Clique no escudo do time acima para ver detalhes.")

# ---------------------------------------------------------
# ABA 3: TÉCNICOS
# ---------------------------------------------------------
with tab_tecnicos:
    st.header(f"Análise de Técnicos ({opcao})")
    
    # Usa a coluna 'tecnico' padronizada do df_analise
    if 'tecnico' in df_analise.columns and df_analise['tecnico'].notna().any():
        
        # Agrupamento simplificado
        df_tec = df_analise.groupby('tecnico').agg(
            jogos=('resultado_final', 'count'),
            vitorias=('resultado_final', lambda x: (x == 'V').sum()),
            derrotas=('resultado_final', lambda x: (x == 'D').sum())
        ).reset_index()
        
        df_tec['aproveitamento_vitorias'] = (df_tec['vitorias'] / df_tec['jogos']) * 100
        
        min_jogos = st.slider("Mínimo de jogos para análise", 1, 38, 5)
        df_tec_filtered = df_tec[df_tec['jogos'] >= min_jogos].sort_values('vitorias', ascending=False)
        
        c_t1, c_t2 = st.columns([2, 1])
        
        with c_t1:
            st.subheader("Top Técnicos por Vitórias")
            fig_t, ax_t = plt.subplots(figsize=(10, 6))
            top_tec = df_tec_filtered.head(10)
            ax_t.barh(top_tec['tecnico'], top_tec['vitorias'], color='purple')
            ax_t.set_xlabel("Vitórias")
            ax_t.invert_yaxis() 
            st.pyplot(fig_t)
            
        with c_t2:
            st.subheader("Dados Detalhados")
            st.dataframe(
                df_tec_filtered[['tecnico', 'jogos', 'vitorias', 'aproveitamento_vitorias']]
                .style.format({'aproveitamento_vitorias': '{:.1f}%'}),
                use_container_width=True,
                hide_index=True
            )
    else:
        st.warning(f"Não foram encontrados dados de técnicos para o filtro selecionado.")

# ---------------------------------------------------------
# ABA 4: SOBRE
# ---------------------------------------------------------
with tab_sobre:
    st.header("Sobre o Projeto")
    st.write("""
        **Brasileirão Analytics**
        🎯 Problema e Motivação
Este projeto tem como objetivo analisar dados históricos do Campeonato Brasileiro (Série A) por meio de um dashboard interativo.
A motivação é transformar um grande volume de dados em informações visuais, intuitivas e úteis, permitindo responder perguntas como:

Quais times fizeram mais gols?
Quem tem o maior público médio?
Como um time evoluiu rodada a rodada no campeonato?
Qual o aproveitamento de cada clube (vitórias, empates, derrotas)?
O dashboard permite explorar tudo isso de forma simples e rápida.

🧰 Ferramentas Utilizadas
🔹 PySpark
Usado para leitura e processamento inicial do dataset.
Justificativa: melhor desempenho e facilidade para lidar com dados tabulares grandes.

🔹 Pandas
Utilizado após converter o DataFrame Spark para operações estatísticas mais simples.
Justificativa: flexibilidade e rapidez em manipulação de dados menores.

🔹 Streamlit
Framework principal para construção da interface web.
Justificativa: criação fácil de dashboards interativos, ideal para visualização de dados.

🔹 Matplotlib & Plotly
Bibliotecas responsáveis pelos gráficos.

Matplotlib → gráficos mais simples (barras, linhas, médias)
Plotly → visualizações interativas (como evolução da posição do time ao longo das rodadas)
🔹 st_clickable_images
Biblioteca auxiliar para tornar possível a seleção de times através dos escudos — melhorando a experiência do usuário.

📊 Resultados e Visualizações Geradas
🌎 Visão Geral
Inclui gráficos que permitem comparar todos os times:

Média de gols (mandante ou visitante)
Público médio (para todos os anos)
Quantidade de vitórias
Quantidade de derrotas
Esses gráficos ajudam a entender o panorama geral do campeonato.

🔍 Por Time
Ao clicar no escudo de um clube, são mostradas análises específicas:

📈 Média de gols por ano ou por rodada
👥 Média de público do time como mandante
🏆 Evolução da colocação rodada a rodada (linha interativa com Plotly)
📊 Aproveitamento (vitórias, empates e derrotas) em formato de gráfico de barras
Essa aba permite uma análise completa do desempenho do time escolhido.
    """)