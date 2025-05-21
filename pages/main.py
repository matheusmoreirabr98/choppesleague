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
from datetime import datetime, timedelta, date

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

                # Centraliza o botão Entrar
                st.markdown("""
                    <style>
                    div.stButton > button:first-child {
                        display: block;
                        margin: 0 auto;
                    }
                    </style>
                """, unsafe_allow_html=True)

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

            # Botão "Esqueci minha senha" centralizado abaixo do formulário
            st.markdown("""
                <div style='text-align: center; margin-top: 1rem;'>
                    <form action="#" method="post">
                        <button onclick="window.parent.postMessage({type: 'streamlit:rerun'}, '*');" style='background: none; border: none; color: #1f77b4; text-decoration: underline; font-size: 15px; cursor: pointer;'>
                            Esqueci minha senha
                        </button>
                    </form>
                </div>
            """, unsafe_allow_html=True)

            if st.button("", key="btn_hidden_recovery", disabled=True):
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
else:
    st.title(st.session_state.pagina_atual)
    st.success(f"Bem-vindo, {st.session_state.nome}!")
    # aqui você pode chamar outras funções ou páginas, como tela_principal(), etc.