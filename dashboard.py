import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Tesouraria Familiar", layout="wide", page_icon="📊")

@st.cache_data(ttl=60)
def carregar_dados():
    sheet_id = "1cDp7JKM6TkAOqM1ET-6ZLbNBEBRwej206fb4CoI--UE"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    
    try:
        df = pd.read_csv(url)
    except Exception as e:
        st.error("⚠️ Não foi possível ler a planilha. Verifique se o link está partilhado como 'Qualquer pessoa com o link'.")
        return pd.DataFrame()
        
    colunas_ignorar = ['Categoria / Item', 'Total Anual', 'TOTAL DE ENTRADAS']
    meses = [col for col in df.columns if col not in colunas_ignorar and 'Unnamed' not in str(col)]
    
    df_clean = df[['Categoria / Item'] + meses].copy()
    
    grupos_conhecidos = ['CUSTOS ESSENCIAIS', 'HABITAÇÃO', 'TRANSPORTE E MOBILIDADE', 
                         'SAÚDE DA FAMÍLIA', 'ALIMENTAÇÃO BÁSICA', 'MAURÍCIO', 'ESTILO DE VIDA E LAZER']
    linhas_ignorar = ['TOTAL DE ENTRADAS', 'RESULTADO DO MÊS', 'SALDO DO MÊS', 'SALDO ACUMULADO']
    
    df_clean = df_clean.dropna(subset=['Categoria / Item'])
    
    dados_finais = []
    grupo_atual = "Outros"
    
    for _, row in df_clean.iterrows():
        item = row['Categoria / Item']
        if item in linhas_ignorar:
            continue
        if item in grupos_conhecidos:
            grupo_atual = item 
            continue
        
        for mes in meses:
            valor = row[mes]
            if pd.notna(valor) and str(valor).strip() not in ['', '0', '0.0']:
                try:
                    if isinstance(valor, str):
                        valor_num = float(valor.replace('R$', '').replace('.', '').replace(',', '.').strip())
                    else:
                        valor_num = float(valor)
                        
                    if valor_num != 0:
                        dados_finais.append({
                            'Mês': str(mes),
                            'Grupo': grupo_atual,
                            'Categoria': item,
                            'Valor': valor_num
                        })
                except:
                    pass 
                
    return pd.DataFrame(dados_finais)

df = carregar_dados()

st.title("📊 Painel de Tesouraria Familiar")
st.markdown("---")

if df.empty:
    st.warning("Aguardando ligação à planilha...")
else:
    st.sidebar.header("Filtros Dinâmicos")
    meses_disponiveis = df['Mês'].unique().tolist()
    mes_selecionado = st.sidebar.multiselect("Selecione o(s) Mês(es):", meses_disponiveis, default=meses_disponiveis)
    
    grupos_disponiveis = df['Grupo'].unique().tolist()
    grupo_selecionado = st.sidebar.multiselect("Selecione o(s) Grupo(s):", grupos_disponiveis, default=grupos_disponiveis)
    
    df_filtrado = df[(df['Mês'].isin(mes_selecionado)) & (df['Grupo'].isin(grupo_selecionado))]
    
    total_gasto = df_filtrado['Valor'].sum()
    col1, col2 = st.columns(2)
    col1.metric("Total Gasto (Filtro Atual)", f"R$ {total_gasto:,.2f}")
    col2.metric("Nº de Registos", len(df_filtrado))
    
    st.markdown("---")
    
    col_graf1, col_graf2 = st.columns(2)
    
    with col_graf1:
        st.markdown("### 🎯 Distribuição por Grupo")
        if not df_filtrado.empty:
            df_grupo = df_filtrado.groupby('Grupo')['Valor'].sum().reset_index()
            fig_pie = px.pie(df_grupo, values='Valor', names='Grupo', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Sem dados para exibir.")
    
    with col_graf2:
        st.markdown("### 📈 Evolução Mensal")
        if not df_filtrado.empty:
            df_mes = df_filtrado.groupby('Mês')['Valor'].sum().reset_index()
            fig_bar = px.bar(df_mes, x='Mês', y='Valor', text='Valor', color='Mês', color_discrete_sequence=px.colors.qualitative.Set2)
            fig_bar.update_traces(texttemplate='R$ %{text:,.2f}', textposition='outside')
            fig_bar.update_layout(showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Sem dados para exibir.")
    
    st.markdown("---")
    st.markdown("### 📋 Tabela Detalhada de Despesas")
    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
