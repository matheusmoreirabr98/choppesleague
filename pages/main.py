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
            .input-personalizado {
        width: 100%;
        padding: 0.5rem;
        font-size: 16px;
        box-sizing: border-box;
        border-radius: 4px;
        border: 1px solid #ccc;
        background-color: white;
    }
    .input-personalizado {
        width: 100%;
        padding: 0.75rem 1rem;
        font-size: 1rem;
        border: none;
        border-radius: 0.5rem;
        background-color: #f0f2f6;
        box-shadow: inset 0 0 0 1px rgba(49, 51, 63, 0.1);
        font-family: inherit;
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
        st.markdown("<h1 style='font-size: 1.6rem;'>🔐 Login / Cadastro</h1>", unsafe_allow_html=True)
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
                        st.rerun()
                    else:
                        st.error("E-mail ou senha inválidos.")

            if not st.session_state.modo_recuperacao:
                if st.button("Esqueci minha senha"):
                    st.session_state.modo_recuperacao = True
                    st.rerun()

            if st.session_state.modo_recuperacao:
                st.markdown("<h3 style='margin-top: 1rem;'>🔁 Atualize sua senha</h3>", unsafe_allow_html=True)
                with st.form("form_esqueci"):
                        email = st.text_input("E-mail cadastrado", key="rec_email_final")
                        palavra_chave_rec = st.text_input("Palavra-chave", key="palavra_chave_rec_final")
                        nova_senha = st.text_input("Nova senha", type="password", key="nova_senha_final")
                        confirmar = st.form_submit_button("Atualizar senha")

                        if confirmar:
                            usuarios = st.session_state.usuarios
                            if email not in usuarios:
                                st.error("E-mail não encontrado.")
                            elif palavra_chave_rec != usuarios[email]["palavra_chave"]:
                                st.error("Palavra-chave incorreta.")
                            else:
                                usuarios[email]["senha"] = nova_senha
                                st.success("Senha atualizada com sucesso! Agora faça login.")
                                st.session_state.modo_recuperacao = False
                                st.rerun()

                if st.button("🔙 Voltar para login"):
                    st.session_state.modo_recuperacao = False
                    st.session_state.codigo_enviado = False
                    st.rerun()

        # CADASTRO
        elif aba == "Cadastro":
            with st.form("form_cadastro"):
                nome = st.text_input("Nome completo", key="cad_nome", placeholder="Digite seu nome completo", autocomplete="name")
                posicao = st.selectbox("Posição que joga", ["Linha", "Goleiro"], key="cad_pos")
                raw_nascimento = st.text_input("Data de nascimento (DD/MM/AAAA)", key="cad_nasc", placeholder="ddmmaaaa", autocomplete="bday")
                nascimento = re.sub(r'\D', '', raw_nascimento)
                if len(nascimento) >= 5:
                    nascimento = nascimento[:2] + '/' + nascimento[2:4] + ('/' + nascimento[4:8] if len(nascimento) > 4 else '')
                telefone = st.text_input("WhatsApp - Ex: 3199475512", key="cad_tel", placeholder="(DDD) número", autocomplete="tel")
                email = st.text_input("E-mail", key="cad_email", autocomplete="email")
                senha = st.text_input("Senha", type="password", key="cad_senha")
                palavra_chave = st.text_input("Palavra-chave (para recuperar a senha)", key="cad_palavra", help="Use algo que você consiga lembrar. Será necessária para redefinir sua senha no futuro.")
                submit = st.form_submit_button("Cadastrar")

                erros = []

                if submit:
                    if not nome or not posicao or not nascimento or not telefone or not email or not senha:
                        erros.append("⚠️ Todos os campos devem ser preenchidos.")
                    if not re.match(r'^\d{2}/\d{2}/\d{4}$', nascimento):
                        erros.append("📅 O campo 'Data de nascimento' deve estar no formato DD/MM/AAAA.")
                    if not telefone.isdigit():
                        erros.append("📞 O campo 'WhatsApp' deve conter apenas números.")
                    if not email_valido(email):
                        erros.append("✉️ O campo 'E-mail' deve conter um endereço válido (ex: nome@exemplo.com).")

                    if erros:
                        for erro in erros:
                            st.warning(erro)
                        submit = False

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
                            "palavra_chave": palavra_chave,
                            "tipo": tipo
                        }
                        st.success("Cadastro realizado! Agora faça login.")

# BLOQUEIA TUDO SE NÃO ESTIVER LOGADO
if not st.session_state.usuario_logado:
    tela_login()
else:




    # SIDEBAR
    with st.sidebar:
        st.image("./imagens/logo.png", use_container_width=True)
        st.markdown("---")
        st.markdown(f"👟 Jogador: **{st.session_state.nome}**")

        # Botão de Meu Perfil (altera a página)
        if st.button("👤 Meu Perfil", use_container_width=True):
            st.session_state.pagina_atual = "👤 Meu Perfil"

        # Botão de Logout
        if 'confirmar_logout' not in st.session_state:
            st.session_state.confirmar_logout = False

        if st.session_state.usuario_logado:
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.confirmar_logout = True

        if st.session_state.confirmar_logout:
            st.warning("Tem certeza que deseja sair?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("❌ Cancelar", use_container_width=True):
                    st.session_state.confirmar_logout = False
            with col2:
                if st.button("✅ Confirmar", use_container_width=True):
                    usuarios = st.session_state.get("usuarios", {})
                    st.session_state.clear()
                    st.session_state.usuario_logado = False
                    st.session_state.usuarios = usuarios
                    st.session_state.pagina_atual = "login"
                    st.rerun()

        st.markdown("---")

        # Navegação principal
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
            ]

        pagina_escolhida = st.selectbox("Navegar para:", opcoes, key="navegacao_sidebar", label_visibility="collapsed")
        st.session_state.pagina_atual = pagina_escolhida

    # --- CONTEÚDO PRINCIPAL ---

    if st.session_state.pagina_atual == "🏠 Tela Principal":
        st.success(f"Bem-vindo, {st.session_state.nome}!")

    elif st.session_state.pagina_atual == "👤 Meu Perfil":
        st.title("👤 Meu Perfil")

        tipo_usuario = st.session_state.get("tipo_usuario", "Usuário")
        nome = st.session_state.get("nome", "Nome não encontrado")
        email = st.session_state.get("login_email") or next(
            (e for e, u in st.session_state.usuarios.items() if u["nome"] == nome), None
        )

        usuarios = st.session_state.get("usuarios", {})
        if not nome or not email or email not in usuarios:
            st.error("Usuário não identificado ou sessão inválida.")
            st.stop()
            st.rerun()

        usuario = usuarios[email]

        with st.container():
            st.markdown(f"""
            <div style="text-align: left; padding: 20px;">
                <h3>📋 Informações Cadastradas</h3>
                <div style="font-size: 18px; line-height: 1.6;">
                    <p><strong>Nome completo:</strong> {usuario['nome']}</p>
                    <p><strong>Posição:</strong> {usuario['posicao']}</p>
                    <p><strong>Data de nascimento:</strong> {usuario['nascimento']}</p>
                    <p><strong>Telefone:</strong> {usuario['telefone']}</p>
                    <p><strong>E-mail:</strong> {email}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<hr style='border: 1px solid #ddd;'>", unsafe_allow_html=True)

            st.subheader("🔑 Atualizar senha e palavra-chave")
            with st.form("form_atualizar_senha"):
                nova_senha = st.text_input("Nova senha", type="password")
                nova_palavra_chave = st.text_input("Nova palavra-chave")
                confirmar = st.form_submit_button("Atualizar")

            if confirmar:
                if nova_senha:
                    usuario["senha"] = nova_senha
                if nova_palavra_chave:
                    usuario["palavra_chave"] = nova_palavra_chave
                st.success("Informações atualizadas com sucesso!")

            st.markdown("<hr style='border: 1px solid #ddd;'>", unsafe_allow_html=True)
            if st.button("🔙 Voltar para Tela Principal"):
                st.session_state.pagina_atual = "🏠 Tela Principal"
                st.rerun()
