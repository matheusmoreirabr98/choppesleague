import streamlit as st
import re
from PIL import Image

st.set_page_config(
    page_title="Cadastro/Login",
    page_icon="👤"
)

def formatar_telefone_9fixo(numero):
    if len(numero) == 11:
        return f"({numero[:2]}) {numero[2:7]}-{numero[7:]}"
    return numero

def tela_login():
    st.title("Acesso ao Sistema")

    if "usuario_logado" not in st.session_state:
        st.session_state["usuario_logado"] = False
    if "usuario_cadastrado" not in st.session_state:
        st.session_state["usuario_cadastrado"] = False

    aba = st.radio("Selecione uma opção:", ["🔐 Login", "📝 Cadastro"], key="aba_login")

    if aba == "📝 Cadastro":
        with st.form("form_cadastro"):
            nome = st.text_input("Nome completo")
            email = st.text_input("E-mail")
            senha = st.text_input("Senha", type="password")
            posicao = st.selectbox("Posição que joga", ["", "Linha", "Goleiro"])
            nascimento = st.date_input("Data de nascimento")
            telefone_input = st.text_input("Número de telefone (com DDD)")

            submit = st.form_submit_button("Cadastrar")

            if submit:
                numeros = re.sub(r'\D', '', telefone_input)[:11]
                if len(numeros) >= 3 and numeros[2] != '9':
                    numeros = numeros[:2] + '9' + numeros[2:]
                telefone_formatado = formatar_telefone_9fixo(numeros)

                if len(numeros) != 11:
                    st.warning("Número de telefone inválido. Deve conter exatamente 11 dígitos.")
                elif not nome or not email or not senha or not posicao:
                    st.warning("Preencha todos os campos.")
                else:
                    st.session_state["cadastro"] = {
                        "nome": nome,
                        "email": email,
                        "senha": senha,
                        "telefone": telefone_formatado,
                        "nascimento": nascimento,
                        "posicao": posicao
                    }
                    st.session_state["usuario_cadastrado"] = True
                    st.success("Cadastro realizado com sucesso! Agora faça login.")

    elif aba == "🔐 Login":
        with st.form("form_login", clear_on_submit=True):
            email_login = st.text_input("E-mail")
            senha_login = st.text_input("Senha", type="password")
            submit_login = st.form_submit_button("Entrar")

            if submit_login:
                cadastro = st.session_state.get("cadastro", {})
                if (
                    st.session_state["usuario_cadastrado"]
                    and email_login == cadastro.get("email")
                    and senha_login == cadastro.get("senha")
                ):
                    st.session_state["usuario_logado"] = True
                    st.session_state["nome"] = cadastro.get("nome")
                    st.session_state["telefone"] = cadastro.get("telefone", "")
                    st.session_state["email"] = cadastro.get("email", "")
                    st.success("✅ Login realizado com sucesso! Redirecionando...")

                    # Redirecionamento simulado
                    st.markdown("### 👉 Vá para o menu lateral e escolha uma das opções para começar.")
                else:
                    st.warning("E-mail ou senha incorretos.")

# Executa a função
tela_login()

# Menu lateral
with st.sidebar:
    try:
        image = Image.open("./imagens/logo.png")
        st.image(image, caption="Chopp's League", use_container_width=True)
    except:
        st.warning("Logo não encontrada.")
