import streamlit as st
import requests
from io import BytesIO
from PIL import Image
import pandas as pd
import random
import os
import re
import urllib.parse
import base64
from datetime import datetime
from datetime import datetime, timedelta
from datetime import date





st.set_page_config(page_title="Chopp's League", page_icon="🍻")

# Sessões iniciais
if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = False
if "usuarios" not in st.session_state:
    st.session_state.usuarios = {}
if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = "login"
if "recuperacao_email" not in st.session_state:
    st.session_state.recuperacao_email = ""
if "codigo_recuperacao" not in st.session_state:
    st.session_state.codigo_recuperacao = ""
if "codigo_enviado" not in st.session_state:
    st.session_state.codigo_enviado = False
if "modo_recuperacao" not in st.session_state:
    st.session_state.modo_recuperacao = False

# Funções auxiliares
def email_valido(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def formatar_telefone(numero):
    numeros = re.sub(r'\D', '', numero)
    if len(numeros) == 11:
        return f"({numeros[:2]}) {numeros[2:7]}-{numeros[7:]}"
    return numero

# --- TELA DE LOGIN / CADASTRO ---
def tela_login():
    st.title("🔐 Login / Cadastro")
    aba = st.radio("Escolha uma opção:", ["Login", "Cadastro"], key="aba_login")

    # LOGIN NORMAL OU RECUPERAÇÃO
    if aba == "Login":

        if not st.session_state.modo_recuperacao:

            with st.form("form_login"):
                email = st.text_input("E-mail", key="login_email")
                senha = st.text_input("Senha", type="password", key="login_senha")
                submit = st.form_submit_button("Entrar")

                if submit:
                    usuarios = st.session_state.usuarios
                    if email in usuarios and usuarios[email]["senha"] == senha:
                        st.session_state.usuario_logado = True
                        st.session_state.nome = usuarios[email]["nome"]
                        st.session_state.tipo_usuario = usuarios[email].get("tipo", "usuario")
                        st.session_state.pagina_atual = "🏠 Tela Principal"
                        st.success("Login realizado com sucesso!")
                        st.experimental_rerun()
                    else:
                        st.error("E-mail ou senha inválidos.")

                # Botão centralizado: "Esqueci minha senha"
                st.markdown(
                    """
                    <div style="display: flex; justify-content: center; margin-top: 1rem;">
                        <button onclick="document.getElementById('fake-button').click()" 
                                style="background: none; border: none; color: #1f77b4; 
                                    text-decoration: underline; font-size: 15px; cursor: pointer;">
                            Esqueci minha senha
                        </button>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                st.markdown("""
                    <div id="hidden-button" style="display: none;">
                        <form action="#" method="post">
                            <button type="submit" name="fake-button">Fake</button>
                        </form>
                    </div>
                """, unsafe_allow_html=True)

                # Checa se o botão foi clicado com o nome correto
                if st.button("fake", key="fake-button"):
                    st.session_state.modo_recuperacao = True
                    st.experimental_rerun()

                else:
                    with st.form("form_esqueci"):
                        email = st.text_input("Digite seu e-mail", key="rec_email")
                        enviar = st.form_submit_button("Enviar código de recuperação")

                        if enviar:
                            if email in st.session_state.usuarios:
                                codigo = str(random.randint(100000, 999999))
                                st.session_state.recuperacao_email = email
                                st.session_state.codigo_recuperacao = codigo
                                st.session_state.codigo_enviado = True
                                st.success(f"Código enviado para o e-mail {email} (simulado: {codigo})")
                            else:
                                st.error("E-mail não encontrado.")

                    if st.session_state.codigo_enviado:
                        with st.form("form_codigo"):
                            codigo_digitado = st.text_input("Digite o código recebido", key="codigo_digitado")
                            nova_senha = st.text_input("Nova senha", type="password", key="nova_senha")
                            confirmar = st.form_submit_button("Atualizar senha")

                            if confirmar:
                                if codigo_digitado == st.session_state.codigo_recuperacao:
                                    email = st.session_state.recuperacao_email
                                    st.session_state.usuarios[email]["senha"] = nova_senha
                                    st.success("Senha atualizada com sucesso! Agora faça login.")
                                    # Limpa os dados temporários
                                    st.session_state.codigo_enviado = False
                                    st.session_state.codigo_recuperacao = ""
                                    st.session_state.recuperacao_email = ""
                                    st.session_state.modo_recuperacao = False
                                    st.session_state.pagina_atual = "login"
                                    st.experimental_rerun()
                                else:
                                    st.error("Código incorreto. Tente novamente.")

                    if st.button("🔙 Voltar para login"):
                        st.session_state.modo_recuperacao = False
                        st.session_state.codigo_enviado = False
                        st.experimental_rerun()

    # CADASTRO
    elif aba == "Cadastro":
        with st.form("form_cadastro"):
            nome = st.text_input("Nome completo", key="cad_nome")
            posicao = st.selectbox("Posição que joga", ["Linha", "Goleiro"], key="cad_pos")
            nascimento = st.date_input("Data de nascimento", value=date(2000, 1, 1), key="cad_nasc")
            telefone = st.text_input("Telefone (com DDD)", key="cad_tel")
            email = st.text_input("E-mail", key="cad_email")
            senha = st.text_input("Senha", type="password", key="cad_senha")
            submit = st.form_submit_button("Cadastrar")

            if submit:
                if not nome or not posicao or not telefone or not email or not senha:
                    st.warning("Preencha todos os campos.")
                elif posicao == "":
                    st.warning("Selecione a posição.")
                elif not email_valido(email):
                    st.warning("E-mail inválido.")
                elif email in st.session_state.usuarios:
                    st.warning("Este e-mail já está cadastrado.")
                elif len(re.sub(r'\D', '', telefone)) != 11:
                    st.warning("Telefone deve conter 11 dígitos.")
                else:
                    tipo = "admin" if email == "admin@teste.com" else "usuario"
                    st.session_state.usuarios[email] = {
                        "nome": nome,
                        "posicao": posicao,
                        "nascimento": str(nascimento),
                        "telefone": formatar_telefone(telefone),
                        "senha": senha,
                        "tipo": tipo
                    }
                    st.success("Cadastro realizado! Agora faça login.")
                    st.session_state.pagina_atual = "login"
                    st.experimental_rerun()

# BLOQUEIA TUDO SE NÃO ESTIVER LOGADO
if not st.session_state.usuario_logado:
    tela_login()
    st.stop()

    # --- SIDEBAR ---
    with st.sidebar:
        st.image("./imagens/logo.png", caption="Chopp's League", use_container_width=True)
        st.markdown(f"👤 Jogador: **{st.session_state.nome}**")

        st.markdown("---")

        if st.session_state.tipo_usuario == "admin":
            opcoes = [
                "🏠 Tela Principal",
                "📊 Registrar Partida",
                "👟 Estatísticas dos Jogadores",
                "🎲 Sorteio de Times",
                "✅ Confirmar Presença/Ausência",
                "🏅 Avaliação Pós-Jogo",
                "📸 Galeria de Momentos",
                "💬 Fórum",
                "📣 Comunicado à Gestão",
                "📜 Regras Choppe's League",
                "🚪 Sair"
            ]
        else:
            opcoes = [
                "🏠 Tela Principal",
                "👟 Estatísticas dos Jogadores",
                "✅ Confirmar Presença/Ausência",
                "🏅 Avaliação Pós-Jogo",
                "📸 Galeria de Momentos",
                "💬 Fórum",
                "📣 Comunicado à Gestão",
                "📜 Regras Choppe's League",
                "🚪 Sair"
            ]

        pagina_escolhida = st.selectbox("Navegar para:", opcoes, key="navegacao_sidebar", label_visibility="collapsed")
        st.session_state.pagina_atual = pagina_escolhida

        st.markdown("---")
        

    # --- Confirmação de logout ---
    # Inicializa controle de logout apenas uma vez
    if "confirmar_logout" not in st.session_state:
        st.session_state.confirmar_logout = False

    # FLAGS de ação
    logout_clicado = False
    cancelar_clicado = False
    confirmar_clicado = False

    # SIDEBAR - botão logout
    with st.sidebar:
        if not st.session_state.confirmar_logout:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🚪 Logout", key="botao_logout"):
                    st.session_state.confirmar_logout = True
                    logout_clicado = True
        else:
            st.warning("Tem certeza que deseja sair?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("❌ Cancelar", key="cancelar_logout", use_container_width=True):
                    st.session_state.confirmar_logout = False
                    cancelar_clicado = True
            with col2:
                if st.button("✅ Confirmar", key="confirmar_logout_btn", use_container_width=True):
                    usuarios = st.session_state.get("usuarios", {})
                    st.session_state.clear()
                    st.session_state.usuario_logado = False
                    st.session_state.usuarios = usuarios
                    st.session_state.pagina_atual = "login"
                    confirmar_clicado = True

    st.markdown("---")