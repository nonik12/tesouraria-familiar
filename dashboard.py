import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="Tesouraria Familiar", layout="wide", page_icon="💎")

# --- SISTEMA DE LOGIN ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.markdown("### 🔒 Acesso Restrito")
        st.markdown("Insira a palavra-passe para aceder à Tesouraria Familiar.")
        senha = st.text_input("Palavra-passe:", type="password")
        if st.button("Entrar"):
            # Verifica a senha que guardámos nos Segredos
            if senha == st.secrets["senha_segura"]:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ Senha incorreta.")
        return False
    return True

# --- SÓ CARREGA SE A SENHA FOR CORRETA ---
if check_password():
    
    # 1. Carregar Despesas Diárias (Primeira Aba)
    @st.cache_data(ttl=60)
    def carregar_dados():
        sheet_id = "1cDp7JKM6TkAOqM1ET-6ZLbNBEBRwej206fb4CoI--UE"
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        try:
            df = pd.read_csv(url)
        except: return pd.DataFrame()
            
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
                        v_num = float(str(valor).replace('R$', '').replace('.', '').replace(',', '.').strip())
                        if v_num != 0: dados_finais.append({'Mês': str(mes), 'Grupo': grupo_atual, 'Categoria': item, 'Valor': v_num})
                    except: pass 
        return pd.DataFrame(dados_finais)

    # 2. Carregar Cofre e Objetivos (Aba com GID 123456)
    @st.cache_data(ttl=60)
    def carregar_cofre():
        sheet_id = "1cDp7JKM6TkAOqM1ET-6ZLbNBEBRwej206fb4CoI--UE"
        gid = "123456" 
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
        
        try:
            df_c = pd.read_csv(url, header=None, names=['A', 'B', 'C', 'D', 'E', 'F'])
        except: return 0, 0, pd.DataFrame()
            
        reserva_alvo = 0
        reserva_saldo = 0
        objetivos = []
        lendo_objetivos = False
        
        for idx, row in df_c.iterrows():
            col_a = str(row['A']).strip()
            
            if col_a == 'Alvo da Reserva':
                try: reserva_alvo = float(row['B'])
                except: pass
            elif col_a == 'Saldo Atual' and not lendo_objetivos:
                try: reserva_saldo = float(row['B'])
                except: pass
            elif col_a == 'Objetivos':
                lendo_objetivos = True
                continue
                
            if lendo_objetivos and pd.notna(row['A']) and col_a not in ['', 'nan']:
                try:
                    obj_nome = col_a
                    obj_alvo = float(row['C']) if pd.notna(row['C']) else 0
                    obj_saldo = float(row['D']) if pd.notna(row['D']) else 0
                    if obj_alvo > 0:
                        objetivos.append({'Objetivo': obj_nome, 'Alvo': obj_alvo, 'Saldo': obj_saldo})
                except: pass
                
        return reserva_alvo, reserva_saldo, pd.DataFrame(objetivos)

    # Executa a leitura
    df = carregar_dados()
    r_alvo, r_saldo, df_objetivos = carregar_cofre()

    st.title("💎 Tesouraria Familiar")
    
    if not df.empty:
        # Agora temos 3 Separadores!
        tab1, tab2, tab3 = st.tabs(["📈 Despesas", "🏦 Cofre e Metas", "📋 Base de Dados"])

        # Aba 1: Gráficos de Despesas (Mantém-se igual)
        with tab1:
            with st.expander("🔎 Configurar Filtros"):
                c_f1, c_f2 = st.columns(2)
                meses_disp = df['Mês'].unique().tolist()
                mes_sel = c_f1.multiselect("Meses:", meses_disp, default=meses_disp)
                grupos_disp = df['Grupo'].unique().tolist()
                grupo_sel = c_f2.multiselect("Grupos:", grupos_disp, default=grupos_disp)

            df_filt = df[(df['Mês'].isin(mes_sel)) & (df['Grupo'].isin(grupo_sel))]
            
            st.markdown("---")
            c1, c2, c3 = st.columns(3)
            c1.metric("💸 Total Gasto", f"R$ {df_filt['Valor'].sum():,.2f}")
            c2.metric("📅 Meses Visíveis", len(mes_sel))
            c3.metric("🏷️ Registos Ativos", len(df_filt))
            st.markdown("---")

            col_g1, col_g2 = st.columns(2)
            with col_g1:
                if not df_filt.empty:
                    df_g = df_filt.groupby('Grupo')['Valor'].sum().reset_index()
                    fig_p = px.pie(df_g, values='Valor', names='Grupo', hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
                    fig_p.update_traces(textposition='inside', textinfo='percent', hovertemplate="<b>%{label}</b><br>R$ %{value:,.2f}")
                    fig_p.update_layout(margin=dict(t=20, b=0, l=0, r=0), legend=dict(orientation="h", y=-0.2))
                    st.plotly_chart(fig_p, use_container_width=True)
            with col_g2:
                if not df_filt.empty:
                    df_m = df_filt.groupby('Mês')['Valor'].sum().reset_index()
                    fig_b = px.bar(df_m, x='Mês', y='Valor', text='Valor', color='Mês', color_discrete_sequence=px.colors.qualitative.Set2)
                    fig_b.update_traces(texttemplate='R$ %{text:,.2f}', textposition='outside', hovertemplate="%{x}<br>R$ %{y:,.2f}")
                    fig_b.update_layout(xaxis_title="", yaxis_title="", showlegend=False, plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=20, b=0, l=0, r=0))
                    fig_b.update_yaxes(showgrid=True, gridcolor='rgba(200, 200, 200, 0.2)')
                    st.plotly_chart(fig_b, use_container_width=True)

        # Aba 2: O Novo Cofre e Metas
        with tab2:
            st.markdown("### 🛡️ Reserva de Emergência")
            if r_alvo > 0:
                prog_reserva = min(r_saldo / r_alvo, 1.0)
                st.progress(prog_reserva)
                st.write(f"**Progresso:** {prog_reserva*100:.1f}% — (R$ {r_saldo:,.2f} de R$ {r_alvo:,.2f})")
            else:
                st.info("Atualize os valores do Alvo e Saldo da Reserva na planilha para ver a barra de progresso.")
                
            st.markdown("---")
            st.markdown("### ✈️ Objetivos e Sonhos")
            if not df_objetivos.empty:
                for _, obj in df_objetivos.iterrows():
                    prog_obj = min(obj['Saldo'] / obj['Alvo'], 1.0)
                    st.markdown(f"**{obj['Objetivo']}**")
                    st.progress(prog_obj)
                    st.write(f"R$ {obj['Saldo']:,.2f} de R$ {obj['Alvo']:,.2f} ({prog_obj*100:.1f}%)")
                    st.markdown("<br>", unsafe_allow_html=True) # Espaço extra entre os objetivos
            else:
                st.info("Ainda não tem objetivos a decorrer. Adicione-os à planilha!")

        # Aba 3: Tabela de Registos
        with tab3:
            st.markdown("### Histórico Completo")
            st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.warning("Sem dados para apresentar.")
