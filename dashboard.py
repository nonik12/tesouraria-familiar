import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página para ocupar todo o ecrã
st.set_page_config(page_title="Tesouraria Familiar", layout="wide", page_icon="💎")

@st.cache_data(ttl=60)
def carregar_dados():
    sheet_id = "1cDp7JKM6TkAOqM1ET-6ZLbNBEBRwej206fb4CoI--UE"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    
    try:
        df = pd.read_csv(url)
    except:
        st.error("⚠️️ Erro a ligar à base de dados.")
        return pd.DataFrame()
        
    colunas_ignorar = ['Categoria / Item', 'Total Anual', 'TOTAL DE ENTRADAS']
    meses = [col for col in df.columns if col not in colunas_ignorar and 'Unnamed' not in str(col)]
    
    df_clean = df[['Categoria / Item'] + meses].copy().dropna(subset=['Categoria / Item'])
    grupos_conhecidos = ['CUSTOS ESSENCIAIS', 'HABITAÇÃO', 'TRANSPORTE E MOBILIDADE', 'SAÚDE DA FAMÍLIA', 'ALIMENTAÇÃO BÁSICA', 'MAURÍCIO', 'ESTILO DE VIDA E LAZER']
    linhas_ignorar = ['TOTAL DE ENTRADAS', 'RESULTADO DO MÊS', 'SALDO DO MÊS', 'SALDO ACUMULADO']
    
    dados_finais = []
    grupo_atual = "Outros"
    
    for _, row in df_clean.iterrows():
        item = row['Categoria / Item']
        if item in linhas_ignorar: continue
        if item in grupos_conhecidos:
            grupo_atual = item 
            continue
        
        for mes in meses:
            valor = row[mes]
            if pd.notna(valor) and str(valor).strip() not in ['', '0', '0.0']:
                try:
                    v_str = str(valor).replace('R$', '').replace('.', '').replace(',', '.').strip()
                    v_num = float(v_str)
                    if v_num != 0:
                        dados_finais.append({'Mês': str(mes), 'Grupo': grupo_atual, 'Categoria': item, 'Valor': v_num})
                except: pass 
                
    return pd.DataFrame(dados_finais)

df = carregar_dados()

# --- DESIGN DA INTERFACE ---
st.title("💎 Tesouraria Familiar")
st.markdown("Gestão inteligente do orçamento. Dados atualizados em tempo real.")

if not df.empty:
    # 1. Filtros no Topo (Escondidos num Expander)
    with st.expander("🔎 Configurar Filtros (Clique para expandir)"):
        col_f1, col_f2 = st.columns(2)
        meses_disponiveis = df['Mês'].unique().tolist()
        mes_selecionado = col_f1.multiselect("Meses Analisados:", meses_disponiveis, default=meses_disponiveis)
        
        grupos_disponiveis = df['Grupo'].unique().tolist()
        grupo_selecionado = col_f2.multiselect("Grupos de Despesa:", grupos_disponiveis, default=grupos_disponiveis)

    df_filtrado = df[(df['Mês'].isin(mes_selecionado)) & (df['Grupo'].isin(grupo_selecionado))]
    
    # 2. Cartões de Resumo Rápidos
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    c1.metric("💸 Total Gasto", f"R$ {df_filtrado['Valor'].sum():,.2f}")
    c2.metric("📅 Meses Visíveis", len(mes_selecionado))
    c3.metric("🏷️ Registos Ativos", len(df_filtrado))
    st.markdown("---")

    # 3. Organização por Separadores (Tabs)
    tab1, tab2 = st.tabs(["📈 Análise Visual", "📋 Base de Dados Detalhada"])

    with tab1:
        col_graf1, col_graf2 = st.columns(2)
        
        with col_graf1:
            st.markdown("### Onde gastamos mais?")
            df_grupo = df_filtrado.groupby('Grupo')['Valor'].sum().reset_index()
            fig_pie = px.pie(df_grupo, values='Valor', names='Grupo', hole=0.5, 
                             color_discrete_sequence=px.colors.qualitative.Pastel)
            # Melhoria no pop-up do gráfico e legenda abaixo
            fig_pie.update_traces(textposition='inside', textinfo='percent', hovertemplate="<b>%{label}</b><br>R$ %{value:,.2f}")
            fig_pie.update_layout(margin=dict(t=20, b=0, l=0, r=0), showlegend=True, legend=dict(orientation="h", y=-0.2))
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_graf2:
            st.markdown("### Evolução Temporal")
            df_mes = df_filtrado.groupby('Mês')['Valor'].sum().reset_index()
            fig_bar = px.bar(df_mes, x='Mês', y='Valor', text='Valor', 
                             color='Mês', color_discrete_sequence=px.colors.qualitative.Set2)
            # Gráfico mais limpo sem fundo e com dicas dinâmicas
            fig_bar.update_traces(texttemplate='R$ %{text:,.2f}', textposition='outside', hovertemplate="%{x}<br>R$ %{y:,.2f}")
            fig_bar.update_layout(xaxis_title="", yaxis_title="", showlegend=False, 
                                  plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=20, b=0, l=0, r=0))
            fig_bar.update_yaxes(showgrid=True, gridcolor='rgba(200, 200, 200, 0.2)')
            st.plotly_chart(fig_bar, use_container_width=True)

    with tab2:
        st.markdown("### Histórico de Movimentos")
        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
else:
    st.warning("Sem dados para apresentar.")
