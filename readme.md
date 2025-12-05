# ⚽ Brasileirão Analytics – Dashboard Interativo

## 🎯 Problema e Motivação  
Este projeto tem como objetivo analisar dados históricos do Campeonato Brasileiro (Série A) por meio de um dashboard interativo.  
A motivação é transformar um grande volume de dados em **informações visuais, intuitivas e úteis**, permitindo responder perguntas como:

- Quais times fizeram mais gols?  
- Quem tem o maior público médio?  
- Como um time evoluiu rodada a rodada no campeonato?  
- Qual o aproveitamento de cada clube (vitórias, empates, derrotas)?

O dashboard permite explorar tudo isso de forma simples e rápida.

---

## 🧰 Ferramentas Utilizadas

### 🔹 PySpark  
Usado para leitura e processamento inicial do dataset.  
Justificativa: melhor desempenho e facilidade para lidar com dados tabulares grandes.

### 🔹 Pandas  
Utilizado após converter o DataFrame Spark para operações estatísticas mais simples.  
Justificativa: flexibilidade e rapidez em manipulação de dados menores.

### 🔹 Streamlit  
Framework principal para construção da interface web.  
Justificativa: criação fácil de dashboards interativos, ideal para visualização de dados.

### 🔹 Matplotlib & Plotly  
Bibliotecas responsáveis pelos gráficos.  
- **Matplotlib** → gráficos mais simples (barras, linhas, médias)  
- **Plotly** → visualizações interativas (como evolução da posição do time ao longo das rodadas)

### 🔹 st_clickable_images  
Biblioteca auxiliar para tornar possível a seleção de times através dos **escudos** — melhorando a experiência do usuário.

---

## 📊 Resultados e Visualizações Geradas

### 🌎 Visão Geral  
Inclui gráficos que permitem comparar todos os times:
- Média de gols (mandante ou visitante)
- Público médio (para todos os anos)
- Quantidade de vitórias  
- Quantidade de derrotas  

Esses gráficos ajudam a entender o panorama geral do campeonato.

---

### 🔍 Por Time  
Ao clicar no escudo de um clube, são mostradas análises específicas:

- 📈 **Média de gols** por ano ou por rodada  
- 👥 **Média de público** do time como mandante  
- 🏆 **Evolução da colocação** rodada a rodada (linha interativa com Plotly)  
- 📊 **Aproveitamento** (vitórias, empates e derrotas) em formato de gráfico de barras  

Essa aba permite uma análise completa do desempenho do time escolhido.

---

### ℹ️ Sobre  
Resumo das tecnologias utilizadas e do propósito do dashboard.

---

## 📁 Estrutura do Projeto
