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
import streamlit.components.v1 as components


st.set_page_config(page_title="Chopp's League", page_icon="🍻")

# CSS para centralizar e tornar responsiva a tela em diferentes dispositivos
st.markdown("""
    <div style="max-width: 400px; margin: auto;">
        <style>
            .main .block-container {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: flex-start;
                padding: 2rem 1rem;
                max-width: 100%;
                margin: auto;
                word-break: break-word;
                overflow-wrap: break-word;
            }

            @media only screen and (max-width: 600px) {
                .main .block-container {
                    padding: 1.5rem 1rem;
                    width: 100%;
                    max-width: 100vw;
                }
                textarea, input, select, button {
                    font-size: 16px !important;
                    width: 100% !important;
                    box-sizing: border-box;
                }
                label, .stMarkdown p {
                    font-size: 15px !important;
                    word-break: break-word;
                }
            }

            div.stForm button[kind="primary"] {
                display: block;
                margin-left: auto;
                margin-right: auto;
            }

            input[type="password"] {
                padding-right: 12px !important;
                box-sizing: border-box;
            }


            .senha-container {
                position: relative;
                width: 100%;
            }

            .senha-container input {
                width: 100%;
                padding: 10px;
                padding-right: 40px; /* espaço pro botão não sobrepor o texto */
                font-size: 16px;
                box-sizing: border-box;
            }

            .senha-toggle {
                position: absolute;
                top: 50%;
                right: 10px;
                transform: translateY(-50%);
                background: none;
                border: none;
                font-size: 18px;
                cursor: pointer;
                padding: 0;
                line-height: 1;
            }
        </style>
    </div>
""", unsafe_allow_html=True)


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
if "mostrar_senha_login" not in st.session_state:
    st.session_state.mostrar_senha_login = False

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
    aba = st.radio("Escolha uma opção:", ["Login", "Cadastro"], key="aba_login", horizontal=True)

    # LOGIN NORMAL OU RECUPERAÇÃO
    if aba == "Login":

        if not st.session_state.modo_recuperacao:

            with st.form("form_login"):
                email = st.text_input("E-mail", key="login_email")
                senha = st.text_input("Senha", type="password", key="login_senha")

                st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
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

            if st.button("Esqueci minha senha"):
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
            nascimento = st.text_input("Data de nascimento (DD/MM/AAAA)", key="cad_nasc", placeholder="dd/mm/aaaa")
            telefone = components.html('''
    <input type="tel" id="telefone_input" name="telefone" placeholder="(DDD) número"
           pattern="[0-9]*" inputmode="numeric" 
           style="width: 100%; padding: 0.5rem; font-size: 16px; box-sizing: border-box; border-radius: 4px; border: 1px solid #ccc;">
''', height=60)
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

