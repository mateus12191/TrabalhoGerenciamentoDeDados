import streamlit as st
from pyspark.sql import SparkSession 

sp = SparkSession.builder.appName("Brasileirao").getOrCreate()


st.write("Testando")