import streamlit as st
import requests
import json
from io import BytesIO
from PIL import Image
import pandas as pd
import random
import os
import re
import urllib.parse
import base64
from datetime import datetime, timedelta, timezone
import streamlit.components.v1 as components
import gspread
from gspread_dataframe import get_as_dataframe, set_with_dataframe
import time
import random
import math




def sanitize_df(df):
    return df.fillna("").astype(str)

# Constantes
NOME_PLANILHA = "ChoppsLeague"
# CAMINHO_CREDENCIAL = "./credenciais/credenciais.json"

# Nomes de colunas padronizados
COL_DATA = "Data"
COL_NUM_PARTIDA = "Número da Partida"
COL_PLACAR_B = "Placar Borussia"
COL_GOLS_B = "Gols Borussia"
COL_PLACAR_I = "Placar Inter"
COL_GOLS_I = "Gols Inter"

EMAILS_ADMIN = ["matheusmoreirabr@hotmail.com", "lucasbotelho97@hotmail.com"]


st.set_page_config(page_title="Chopp's League", page_icon="🍻")


# -----------------------------------------
# Autenticação
# -----------------------------------------
def autenticar_gsheets():
    # Pega credenciais JSON da secret e converte pra dict
    cred_json_str = st.secrets["gsheets_cred"]
    cred_json = json.loads(cred_json_str)

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    creds = gspread.service_account_from_dict(cred_json, scopes=scope)
    return creds


# -----------------------------------------
# Inicialização: cria planilhas se não existirem
# -----------------------------------------
def init_data_gsheets():
    gc = autenticar_gsheets()
    sh = gc.open(NOME_PLANILHA)
    existentes = [ws.title for ws in sh.worksheets()]

    if "Usuarios" not in existentes:
        df_usuarios = pd.DataFrame(
            columns=[
                "email",
                "nome",
                "posicao",
                "nascimento",
                "telefone",
                "senha",
                "palavra_chave",
                "dica_palavra_chave",
                "tipo",
            ]
        )
        sh.add_worksheet(title="Usuarios", rows="100", cols="20")
        set_with_dataframe(sh.worksheet("Usuarios"), df_usuarios)

        if "Partidas" not in existentes:
            df_partidas = pd.DataFrame(
                columns=[
                    "Data",
                    "Número da Partida",
                    "Placar Borussia",
                    "Gols Borussia",
                    "Placar Inter",
                    "Gols Inter"
                ]
            )
        sh.add_worksheet(title="Partidas", rows="100", cols="20")
        set_with_dataframe(sh.worksheet("Partidas"), df_partidas)

    if "Jogadores" not in existentes:
        df_jogadores = pd.DataFrame(
            columns=[
                "Nome",
                "Time",
                "Gols",
                "Assistências",
                "Faltas",
                "Cartões Amarelos",
                "Cartões Vermelhos",
            ]
        )
        sh.add_worksheet(title="Jogadores", rows="100", cols="20")
        set_with_dataframe(sh.worksheet("Jogadores"), df_jogadores)

    if "Presenças" not in existentes:
        df_presencas = pd.DataFrame(
            columns=[
                "Data da partida",
                "Nº Partida",
                "Nome do Jogador",
                "Presença"  # Sim ou Não
            ]
        )
        sh.add_worksheet(title="Presenças", rows="100", cols="20")
        set_with_dataframe(sh.worksheet("Presenças"), df_presencas)


# -----------------------------------------
# Carregar dados das planilhas
# -----------------------------------------
def load_data_gsheets():
    gc = autenticar_gsheets()
    sh = gc.open(NOME_PLANILHA)

    # Lista das abas obrigatórias
    abas_necessarias = ["Partidas", "Jogadores", "Usuarios", "Presenças"]
    abas_existentes = [w.title for w in sh.worksheets()]

    # Cria as abas que estiverem faltando
    for aba in abas_necessarias:
        if aba not in abas_existentes:
            sh.add_worksheet(title=aba, rows=1000, cols=20)

    # Carrega os dados das abas
    partidas = get_as_dataframe(sh.worksheet("Partidas")).dropna(how="all")
    jogadores = get_as_dataframe(sh.worksheet("Jogadores")).dropna(how="all")
    usuarios_df = get_as_dataframe(sh.worksheet("Usuarios")).dropna(how="all")
    presencas = get_as_dataframe(sh.worksheet("Presenças")).dropna(how="all")

    # Converter para dicionário com e-mail como chave
    usuarios = {}
    if not usuarios_df.empty and "email" in usuarios_df.columns:
        for _, row in usuarios_df.iterrows():
            if pd.notna(row["email"]):
                usuarios[row["email"]] = row.drop(labels="email").to_dict()

    return partidas, jogadores, usuarios, presencas


# -----------------------------------------
# Salvar dados nas planilhas
# -----------------------------------------
def save_data_gsheets(partidas, jogadores, usuarios, presencas):
    gc = autenticar_gsheets()
    sh = gc.open(NOME_PLANILHA)

    # Sanitize
    partidas = sanitize_df(partidas)
    jogadores = sanitize_df(jogadores)
    presencas = sanitize_df(presencas)

    # Salvar partidas
    sheet_partidas = sh.worksheet("Partidas")
    sheet_partidas.clear()
    sheet_partidas.update([partidas.columns.tolist()] + partidas.values.tolist())

    # Salvar jogadores
    sheet_jogadores = sh.worksheet("Jogadores")
    sheet_jogadores.clear()
    sheet_jogadores.update([jogadores.columns.tolist()] + jogadores.values.tolist())

    # Salvar usuários
    sheet_usuarios = sh.worksheet("Usuarios")
    sheet_usuarios.clear()

    usuarios_df = pd.DataFrame.from_dict(usuarios, orient="index").reset_index()
    usuarios_df = usuarios_df.rename(columns={"index": "email"})

    if not usuarios_df.empty:
        usuarios_df = sanitize_df(usuarios_df)  # também sanitiza aqui
        sheet_usuarios.update([usuarios_df.columns.tolist()] + usuarios_df.values.tolist())

    # Salvar presenças
    sheet_presencas = sh.worksheet("Presenças")
    sheet_presencas.clear()
    sheet_presencas.update([presencas.columns.tolist()] + presencas.values.tolist())


# -----------------------------------------
# Abstrações para carregar/salvar
# -----------------------------------------
def load_data():
    return load_data_gsheets()
time.sleep(1)


def save_data(partidas, jogadores, usuarios, presencas):
    save_data_gsheets(partidas, jogadores, usuarios, presencas)


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
if "presencas" not in st.session_state:
    st.session_state.presencas = pd.DataFrame()

# Funções auxiliares


def email_valido(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)


def formatar_telefone(numero):
    numeros = re.sub(r"\D", "", numero)
    if len(numeros) == 11:
        return f"({numeros[:2]}) {numeros[2:7]}-{numeros[7:]}"
    return numero

    # --- TELA DE LOGIN / CADASTRO ---


def tela_login():

    st.markdown(
        "<h1 style='font-size: 1.6rem;'>🔐 Login / Cadastro</h1>",
        unsafe_allow_html=True,
    )
    aba = st.radio(
        "Escolha uma opção:", ["Login", "Cadastro"], key="aba_login", horizontal=True
    )

    partidas, jogadores, usuarios, presencas = load_data()  # ← lê os usuários direto da planilha

    # LOGIN
    if aba == "Login":
        if not st.session_state.modo_recuperacao:
            with st.form("form_login"):
                email = st.text_input("E-mail", key="login_email")
                senha = st.text_input("Senha", type="password", key="login_senha")
                st.markdown(
                    "<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True
                )
                submit = st.form_submit_button("Entrar")

            if submit:
                if email in usuarios and usuarios[email]["senha"] == senha:
                    st.session_state.usuario_logado = True
                    st.session_state.nome = usuarios[email]["nome"]
                    st.session_state.tipo_usuario = usuarios[email].get(
                        "tipo", "usuario"
                    )
                    st.session_state.email = email
                    st.session_state.pagina_atual = "🏠 Tela Principal"
                    st.rerun()
                else:
                    st.error("E-mail ou senha inválidos.")

        if not st.session_state.modo_recuperacao:
            if st.button("Esqueci minha senha"):
                st.session_state.modo_recuperacao = True
                st.rerun()

        if st.session_state.modo_recuperacao:
            st.markdown(
                "<h3 style='margin-top: 1rem;'>🔁 Atualize sua senha</h3>",
                unsafe_allow_html=True,
            )

            if st.button("🔙 Voltar para o login"):
                st.session_state.modo_recuperacao = False
                st.rerun()

            email = st.text_input("E-mail cadastrado", key="rec_email_final")

            if email in usuarios and usuarios[email].get("dica_palavra_chave"):
                st.info(f"💡 Dica: {usuarios[email]['dica_palavra_chave']}")

            with st.form("form_esqueci"):
                palavra_chave_rec = st.text_input(
                    "Palavra-chave", key="palavra_chave_rec_final"
                )
                nova_senha = st.text_input(
                    "Nova senha", type="password", key="nova_senha_final"
                )
                confirmar_nova_senha = st.text_input(
                    "Confirme a nova senha",
                    type="password",
                    key="conf_nova_senha_final",
                )
                confirmar = st.form_submit_button("Atualizar senha")

                if confirmar:
                    if email not in usuarios:
                        st.error("E-mail não encontrado.")
                    elif palavra_chave_rec != usuarios[email]["palavra_chave"]:
                        st.error("Palavra-chave incorreta.")
                    elif nova_senha != confirmar_nova_senha:
                        st.error("As novas senhas não coincidem.")
                    else:
                        # primeiro carrega os dados ATUALIZADOS da planilha
                        partidas, jogadores, usuarios, presencas = load_data()

                        # depois altera a senha na versão correta de `usuarios`
                        usuarios[email]["senha"] = nova_senha

                        # agora salva com a senha atualizada
                        save_data(partidas, jogadores, usuarios, presencas)
                        st.success("Senha atualizada com sucesso! Agora faça login.")
                        st.session_state.modo_recuperacao = False
                        st.rerun()

    # CADASTRO
    elif aba == "Cadastro":
        with st.form("form_cadastro"):
            nome = st.text_input(
                "Nome completo",
                key="cad_nome",
                placeholder="Digite seu nome completo",
                autocomplete="name",
            )
            posicao = st.selectbox(
                "Posição que joga", ["Linha", "Goleiro"], key="cad_pos"
            )
            raw_nascimento = st.text_input(
                "Data de nascimento (DD/MM/AAAA)",
                key="cad_nasc",
                placeholder="ddmmaaaa",
                autocomplete="bday",
            )
            nascimento = re.sub(r"\D", "", raw_nascimento)
            if len(nascimento) >= 5:
                nascimento = (
                    nascimento[:2]
                    + "/"
                    + nascimento[2:4]
                    + ("/" + nascimento[4:8] if len(nascimento) > 4 else "")
                )
            telefone = st.text_input(
                "WhatsApp - Ex: 3199475512",
                key="cad_tel",
                placeholder="(DDD) número",
                autocomplete="tel",
            )
            email = st.text_input(
                "E-mail", key="cad_email", autocomplete="email"
            ).lower()
            senha = st.text_input("Senha", type="password", key="cad_senha")
            confirmar_senha = st.text_input(
                "Confirme a senha", type="password", key="cad_conf_senha"
            )
            palavra_chave = st.text_input(
                "Palavra-chave (para recuperar a senha)",
                key="cad_palavra",
                help="Use algo que você consiga lembrar. Será necessária para redefinir sua senha no futuro.",
            )
            dica_palavra_chave = st.text_input(
                "Dica da palavra-chave",
                key="cad_dica",
                help="Será exibida para te ajudar a lembrar da palavra-chave, se necessário.",
            )
            submit = st.form_submit_button("Cadastrar")

            erros = []

            if submit:
                if (
                    not nome
                    or not posicao
                    or not nascimento
                    or not telefone
                    or not email
                    or not senha
                    or not confirmar_senha
                    or not palavra_chave
                    or not dica_palavra_chave
                ):
                    erros.append("⚠ Todos os campos devem ser preenchidos.")
                if not re.match(r"^\d{2}/\d{2}/\d{4}$", nascimento):
                    erros.append(
                        "📅 O campo 'Data de nascimento' deve estar no formato DD/MM/AAAA."
                    )
                if not telefone.isdigit():
                    erros.append("📞 O campo 'WhatsApp' deve conter apenas números.")
                if not email_valido(email):
                    erros.append(
                        "✉ O campo 'E-mail' deve conter um endereço válido (ex: nome@exemplo.com)."
                    )
                if senha != confirmar_senha:
                    erros.append("🔐 As senhas não coincidem.")

                if erros:
                    for erro in erros:
                        st.warning(erro)
                    submit = False

            if submit:
                if email in usuarios:
                    st.warning("Este e-mail já está cadastrado.")
                elif len(re.sub(r"\D", "", telefone)) != 11:
                    st.warning("Telefone deve conter 11 dígitos.")
                else:
                    usuarios[email] = {
                        "nome": nome,
                        "posicao": posicao,
                        "nascimento": str(nascimento),
                        "telefone": formatar_telefone(telefone),
                        "senha": senha,
                        "palavra_chave": palavra_chave,
                        "dica_palavra_chave": dica_palavra_chave,
                        "tipo": "admin" if email in EMAILS_ADMIN else "usuario",
                    }

                    # partidas, jogadores, usuarios, presencas = load_data()

                    save_data(partidas, jogadores, usuarios, presencas)

                    st.success("Cadastro realizado! Agora faça login.")


# BLOQUEIA TUDO SE NÃO ESTIVER LOGADO
if not st.session_state.usuario_logado:
    tela_login()
else:

    if "tipo_usuario" not in st.session_state:
        st.session_state.tipo_usuario = "usuario"

    if "presencas_confirmadas" not in st.session_state:
        st.session_state.presencas_confirmadas = {}

    # --- SIDEBAR --- (imagem e nome apenas)
    with st.sidebar:
        st.image("./imagens/logo.png", width=200)
        st.markdown("")
        st.markdown(f"👟 Jogador: **{st.session_state.nome}**")
        st.markdown("")

    if st.session_state.tipo_usuario == "admin":
        opcoes = [
            "🏠 Tela Principal",
            "👤 Meu Perfil",
            "📊 Registrar Partida",
            "👟 Estatísticas dos Jogadores",
            "🎲 Sorteio de Times",
            "✅ Confirmar Presença/Ausência",
            "🏅 Avaliação Pós-Jogo",
            "📸 Galeria de Momentos",
            "💬 Fórum",
            "📣 Comunicado à Gestão",
            "📜 Regras Chopp's League",
        ]
    else:
        opcoes = [
            "🏠 Tela Principal",
            "👤 Meu Perfil",
            "👟 Estatísticas dos Jogadores",
            "✅ Confirmar Presença/Ausência",
            "🏅 Avaliação Pós-Jogo",
            "📸 Galeria de Momentos",
            "💬 Fórum",
            "📣 Comunicado à Gestão",
            "📜 Regras Chopp's League",
        ]

    # garante que sempre selecionamos uma opção válida da lista
    pagina_ativa = st.session_state.pagina_atual

    # exibimos o selectbox sempre — inclusive no perfil
    pagina_escolhida = st.selectbox(
        "",  # label obrigatória
        opcoes,
        index=opcoes.index(pagina_ativa) if pagina_ativa in opcoes else 0,
        key="menu_topo",
    )

    # só atualiza a página se a escolhida for diferente
    # e se ela for uma das opções válidas
    if pagina_escolhida != st.session_state.pagina_atual and pagina_escolhida in opcoes:
        st.session_state.pagina_atual = pagina_escolhida
        st.rerun()

    # --- Confirmação de logout ---
    # Inicializa controle de logout apenas uma vez
    if "confirmar_logout" not in st.session_state:
        st.session_state.confirmar_logout = False

    # FLAGS de ação
    logout_clicado = False
    cancelar_clicado = False
    confirmar_clicado = False

    with st.sidebar:
        # Botão "Meu Perfil" centralizado (opcional)
        st.button("👤 Meu Perfil", use_container_width=True, on_click=lambda: st.session_state.update(pagina_atual="👤 Meu Perfil"))
        st.write("")
        
        # Botão "Logout" ocupando toda a largura
        if not st.session_state.get("confirmar_logout", False):
            st.button("🚪 Logout", use_container_width=True, key="botao_logout", on_click=lambda: st.session_state.update(confirmar_logout=True))
            st.write("")
        else:
            st.warning("Tem certeza que deseja sair?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button(
                    "❌ Cancelar", key="cancelar_logout", use_container_width=True
                ):
                    st.session_state.confirmar_logout = False
                    st.rerun()
            with col2:
                if st.button(
                    "✅ Confirmar", key="confirmar_logout_btn", use_container_width=True
                ):
                    usuarios = st.session_state.get("usuarios", {})
                    st.session_state.clear()
                    st.session_state.usuario_logado = False
                    st.session_state.usuarios = usuarios
                    st.session_state.pagina_atual = "login"
                    st.rerun()

    # Essas chamadas precisam estar fora do `with`
    if logout_clicado or cancelar_clicado or confirmar_clicado:
        st.rerun()

    # --- ROTEADOR ---
    def tela_principal():
        pass

    def registrar_partidas(p):
        return p

    def tela_jogadores(j):
        return j

    def tela_sorteio():
        pass

    def tela_presenca_login():
        pass

    def tela_avaliacao_pos_jogo():
        pass

    def tela_galeria_momentos():
        pass

    def tela_forum():
        pass

    def tela_comunicado():
        pass

    def tela_regras():
        pass

    partidas = st.session_state.get("partidas", [])
    jogadores = st.session_state.get("jogadores", [])

    pag = st.session_state.pagina_atual

    def tela_meu_perfil():
        _, _, usuarios, _ = load_data()
        st.session_state.usuarios = usuarios
        usuario = usuarios.get(st.session_state.email, {})

        st.markdown("### 📋 Informações Cadastrais")
        nome = usuario.get("nome", "")
        posicao = usuario.get("posicao", "")
        nascimento = usuario.get("nascimento", "")

        st.markdown(f"- **Nome:** {nome}")
        st.markdown(f"- **Posição:** {posicao}")
        st.markdown(f"- **Data de Nascimento:** {nascimento}")

        # Removido o input duplicado de telefone/email aqui

        st.markdown("---")
        st.markdown("### 🔐 Atualizar Dados")

        with st.form("form_perfil"):
            telefone = st.text_input(
                "📱 Telefone", value=usuario.get("telefone", ""), key="perfil_telefone"
            )
            email = st.text_input(
                "✉️ E-mail", value=st.session_state.email, key="perfil_email"
            )

            senha_atual = st.text_input(
                "Senha atual", type="password", key="perfil_senha_atual"
            )
            nova_senha = st.text_input(
                "Nova senha", type="password", key="perfil_nova_senha"
            )
            conf_nova_senha = st.text_input(
                "Confirmar nova senha", type="password", key="perfil_conf_nova_senha"
            )
            nova_palavra_chave = st.text_input(
                "Nova palavra-chave (recuperação)", key="perfil_palavra"
            )
            nova_dica = st.text_input("Nova dica da palavra-chave", key="perfil_dica")

            salvar = st.form_submit_button("💾 Salvar alterações", use_container_width=True)

        if st.session_state.get("atualizacao_sucesso"):
            st.success("✅ Informações atualizadas com sucesso!")
            del st.session_state.atualizacao_sucesso  # remove a flag após exibir

        if salvar:
            partidas, jogadores, usuarios, presencas = load_data()
            email_antigo = st.session_state.email

            if senha_atual != usuarios[email_antigo]["senha"]:
                st.error("❌ Senha atual incorreta.")
            elif nova_senha != conf_nova_senha:
                st.error("❌ As novas senhas não coincidem.")
            elif not nova_palavra_chave or not nova_dica:
                st.error("❌ A palavra-chave e a dica devem ser preenchidas.")
            else:
                usuarios[email_antigo]["telefone"] = telefone
                usuarios[email_antigo]["senha"] = nova_senha
                usuarios[email_antigo]["palavra_chave"] = nova_palavra_chave
                usuarios[email_antigo]["dica_palavra_chave"] = nova_dica

                # Atualiza o e-mail, se mudou
                if email != email_antigo:
                    usuarios[email] = usuarios.pop(email_antigo)
                    st.session_state.email = email

                save_data_gsheets(partidas, jogadores, usuarios, presencas)

                st.success("✅ Informações atualizadas com sucesso!")
                for campo in [
                    "perfil_senha_atual",
                    "perfil_nova_senha",
                    "perfil_conf_nova_senha",
                    "perfil_palavra",
                    "perfil_dica",
                ]:
                    if campo in st.session_state:
                        del st.session_state[campo]

                st.session_state.atualizacao_sucesso = True
                st.rerun()

    # Exibe as páginas conforme tipo
    if pag == "🏠 Tela Principal":
        tela_principal()
    elif pag == "📊 Registrar Partida" and st.session_state.tipo_usuario == "admin":
        registrar_partidas(partidas)
    elif pag == "👟 Estatísticas dos Jogadores":
        jogadores = tela_jogadores(jogadores)
    elif pag == "🎲 Sorteio de Times" and st.session_state.tipo_usuario == "admin":
        tela_sorteio()
    elif pag == "✅ Confirmar Presença/Ausência":
        tela_presenca_login()
    elif pag == "🏅 Avaliação Pós-Jogo":
        tela_avaliacao_pos_jogo()
    elif pag == "📸 Galeria de Momentos":
        tela_galeria_momentos()
    elif pag == "💬 Fórum":
        tela_forum()
    elif pag == "📣 Comunicado à Gestão":
        tela_comunicado()
    elif pag == "📜 Regras Chopp's League":
        tela_regras()
    elif pag == "🚪 Sair":
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

    # Música ambiente (apenas se logado)
    if st.session_state.usuario_logado:
        st.markdown(
            """
            <style>
                [data-testid="stSidebar"] {
                    width: 250px !important;
                }

                /* Corrige o conteúdo principal para não ser cortado */
                [data-testid="stSidebarContent"] {
                    width: 250px !important;
                }
            </style>
            """,
            unsafe_allow_html=True,
        )

        def tocar_musica_sidebar():
            caminho_musica = "audio/musica.mp3"
            if os.path.exists(caminho_musica):
                with open(caminho_musica, "rb") as f:
                    audio_bytes = f.read()
                audio_base64 = base64.b64encode(audio_bytes).decode()
                st.sidebar.markdown(
                    f"""
                    <style>
                        audio::-webkit-media-controls-timeline {{
                            display: none !important;
                        }}
                        audio::-webkit-media-controls-current-time-display,
                        audio::-webkit-media-controls-time-remaining-display {{
                            display: none !important;
                        }}
                    </style>
                    <div style="text-align: center;">
                        <p style='font-weight: bold;'>🎵 Música Ambiente</p>
                        </audio>
                    </div>

                    <div style="text-align: right;">
                        <audio controls style="width: 60%;">
                            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                            Seu navegador não suporta áudio.
                        </audio>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.sidebar.warning("🔇 Música não encontrada.")

        tocar_musica_sidebar()

    # Arquivos CSV
    FILE_PARTIDAS = "partidas.csv"
    FILE_JOGADORES = "jogadores.csv"

    def init_data():
        if not os.path.exists(FILE_PARTIDAS):
            df = pd.DataFrame(
                columns=[
                    "Data",
                    "Número da Partida",
                    "Placar Borussia",
                    "Gols Borussia",
                    "Assistências Borussia",
                    "Placar Inter",
                    "Gols Inter",
                    "Assistências Inter",
                ]
            )
            df.to_csv(FILE_PARTIDAS, index=False)

        if not os.path.exists(FILE_JOGADORES):
            df = pd.DataFrame(
                columns=[
                    "Nome",
                    "Time",
                    "Gols",
                    "Assistências",
                    "Faltas",
                    "Cartões Amarelos",
                    "Cartões Vermelhos",
                ]
            )
            df.to_csv(FILE_JOGADORES, index=False)

    def save_data(partidas, jogadores, usuarios):
        save_data_gsheets(partidas, jogadores, usuarios, presencas=[])

    # Carrega dados com segurança
    def load_data_safe():
        try:
            partidas = pd.read_csv(FILE_PARTIDAS)
        except:
            partidas = pd.DataFrame([...])

        try:
            jogadores = pd.read_csv(FILE_JOGADORES)
        except:
            jogadores = pd.DataFrame([...])

        return partidas, jogadores

    partidas, jogadores = load_data_safe()

    # Tela Principal
    def imagem_base64(path, legenda):
        if os.path.exists(path):
            img = Image.open(path)
            img = img.resize((200, 200))
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            return f"""
                <div style="text-align: center; min-width: 20px;">
                    <img src="data:image/png;base64,{img_base64}" width="80">
                    <p style="margin-top: 0.5rem; font-weight: bold;">{legenda}</p>
                </div>
            """
        return f"<div style='text-align: center;'>Imagem não encontrada: {path}</div>"

 

       # ✅ Tela principal com os escudos lado a lado e "X" no meio
    def tela_principal(partidas=None, jogadores=None):
        if "dados_gsheets" not in st.session_state:
            st.session_state["dados_gsheets"] = load_data()

        partidas, jogadores, _, _ = st.session_state["dados_gsheets"]
        st.markdown(
            "<h5 style='text-align: center; font-weight: bold;'>Bem-vindo à Chopp's League! 🍻</h5>",
            unsafe_allow_html=True,
        )
        st.markdown("---")

        # Remove partidas sem placares
        partidas = partidas.dropna(subset=[COL_GOLS_B, COL_GOLS_I], how='all')

        # Função para contar nomes válidos de goleadores
        def contar_gols(celula):
            if pd.isna(celula) or celula.strip().lower() in ["", "ninguém marcou"]:
                return 0
            return len([nome.strip() for nome in celula.split(",") if nome.strip()])

        # Aplica contagem de gols
        partidas["Gols_B"] = partidas[COL_GOLS_B].apply(contar_gols)
        partidas["Gols_I"] = partidas[COL_GOLS_I].apply(contar_gols)


        partidas_validas = partidas.dropna(subset=["Número da Partida"])
        total_partidas = len(partidas_validas)
        
        # Contagem
        total_partidas = len(partidas)
        gols_borussia = partidas["Gols_B"].sum()
        gols_inter = partidas["Gols_I"].sum()
        borussia_vitorias = (partidas["Gols_B"] > partidas["Gols_I"]).sum()
        inter_vitorias = (partidas["Gols_I"] > partidas["Gols_B"]).sum()
        empates = (partidas["Gols_B"] == partidas["Gols_I"]).sum()

        # Imagens dos escudos
        escudo_borussia = imagem_base64("imagens/escudo_borussia.png", "Borussia")
        escudo_inter = imagem_base64("imagens/escudo_inter.png", "Inter")

        # Layout dos escudos
        st.markdown(
            f"""
                <div style="
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    gap: 50px;
                    flex-wrap: nowrap;
                ">
                    {escudo_borussia}
                <div style="font-size: 60px; font-weight: bold; line-height: 1;">⚔️</div>
                    {escudo_inter}
                </div>
            """,
            unsafe_allow_html=True,
        )

        # Estatísticas abaixo
        st.markdown(
            f"""
            <div style="text-align: center; margin-top: 2rem;">
                <p style="font-size: 20px; font-weight: bold;">
                    📊 Total de Partidas: {total_partidas}
                </p>
        </div>
        """,
        unsafe_allow_html=True,
        )
            
        st.markdown(
            f"""
            <div style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 50px;
                margin-top: 20px;
                flex-wrap: wrap;
            ">
            <div style="text-align: right; min-width: 100px;">
                <p style="font-size: 25px;">
                    {borussia_vitorias} - 🏆<br>
                    {gols_borussia} - ⚽
                </p>
            </div>

            <div style="text-align: center; min-width: 5px;">
                <p style="font-size: 25px;">
                    🤝<br>
                    {empates}
                </p>
            </div>

            <div style="text-align: left; min-width: 100px;">
                <p style="font-size: 25px;">
                    {inter_vitorias} - 🏆<br>
                    {gols_inter} - ⚽
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )







    # Tela de registro das partidas
    def registrar_partidas():
        st.markdown("<h5 style='text-align: center; font-weight: bold;'>Registrar Estatísticas da Partida</h5>", unsafe_allow_html=True)
        st.markdown("---")

        # carrega os dados do session_state ou do GSheets
        if "dados_gsheets" not in st.session_state:
            st.session_state["dados_gsheets"] = load_data()
        partidas, jogadores, usuarios, presencas = st.session_state["dados_gsheets"]
        presencas.rename(columns={
            "Nome do Jogador": "Nome",
            "Data da partida": "DataPartida"
        }, inplace=True)

        # 🟢 inicializa form_id para controle dos multiselects
        if "form_id" not in st.session_state:
            st.session_state["form_id"] = 0

        # garante que colunas estejam no formato correto
        if not partidas.empty:
            partidas["Data"] = pd.to_datetime(partidas["Data"], dayfirst=True, errors='coerce').dt.date
            presencas["DataPartida"] = pd.to_datetime(presencas["DataPartida"], errors="coerce").dt.date
            # Detecta automaticamente a coluna de presença e padroniza
            coluna_presenca = None
            for col in presencas.columns:
                if col.strip().lower() == "presença":
                    coluna_presenca = col
                    break

            if coluna_presenca:
                presencas.rename(columns={coluna_presenca: "Presença"}, inplace=True)
                presencas["Presença"] = presencas["Presença"].astype(str).str.strip().str.lower()
            else:
                st.error("❌ Coluna 'Presença' não encontrada na planilha. Verifique o nome exato.")
                st.stop()

        # seleção de data da partida
        data = st.date_input("📅 Data da partida")

        # define número da nova partida com base nas partidas da mesma data
        partidas_do_dia = partidas[partidas["Data"] == data]
        numero_partida = len(partidas_do_dia) + 1

        # filtra jogadores presentes
        jogadores_presentes_data = presencas[
            (presencas["DataPartida"] == data) & (presencas["Presença"] == "sim")
        ]["Nome"].tolist()

        if not jogadores_presentes_data:
            st.warning("⚠️ Nenhum jogador confirmou presença para esta data.")
            return

        jogadores_originais = jogadores_presentes_data

        col1, col2 = st.columns(2)

        with col1:
            lista_borussia = ["Ninguém marcou"] + jogadores_originais
            gols_borussia = st.multiselect(
                "Goleadores (Borussia)",
                options=lista_borussia,
                default=[],
                max_selections=2,
                key=f"gols_borussia_{st.session_state['form_id']}",
                help="Máximo 2 jogadores"
            )
            if "Ninguém marcou" in gols_borussia and len(gols_borussia) > 1:
                st.warning("Não é permitido selecionar jogadores junto com 'Ninguém marcou'.")
                gols_borussia = ["Ninguém marcou"]
                st.session_state["gols_borussia"] = ["Ninguém marcou"]

            placar_borussia = 0 if "Ninguém marcou" in gols_borussia else len(gols_borussia)

        with col2:
            jogadores_indisponiveis = set(gols_borussia)
            lista_inter = ["Ninguém marcou"] + [j for j in jogadores_originais if j not in jogadores_indisponiveis]
            gols_inter = st.multiselect(
                "Goleadores (Inter)",
                options=lista_inter,
                default=[],
                max_selections=2,
                key=f"gols_inter_{st.session_state['form_id']}",
                help="Máximo 2 jogadores"
            )
            if "Ninguém marcou" in gols_inter and len(gols_inter) > 1:
                st.warning("Não é permitido selecionar jogadores junto com 'Ninguém marcou'.")
                gols_inter = ["Ninguém marcou"]
                st.session_state["gols_inter"] = ["Ninguém marcou"]

            placar_inter = 0 if "Ninguém marcou" in gols_inter else len(gols_inter)

            if placar_borussia == 2 and placar_inter == 2:
                st.error("Empate em 2x2 não é permitido. Ajuste os goleadores.")

            escudo_borussia = imagem_base64("imagens/escudo_borussia.png", "Borussia")
            escudo_inter = imagem_base64("imagens/escudo_inter.png", "Inter")

        st.markdown(f"<h5 style='text-align: center; font-weight: bold;'>Resultado da Partida: #{numero_partida}</h5><br>", unsafe_allow_html=True)
        st.markdown(
            f"""
                <div style="display: flex; justify-content: center; align-items: right; gap: 50px; flex-wrap: nowrap;">
                    {escudo_borussia}
                <div style="font-size: 60px; font-weight: bold; line-height: 1;">⚔️</div>
                    {escudo_inter}
                </div>
            """, unsafe_allow_html=True
        )
        st.markdown(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: left; gap: 50px; margin-top: 20px; flex-wrap: wrap;">
            <div style="text-align: right; min-width: 70px;"><p style="font-size: 30px;">{placar_borussia}</p></div>
            <div style="text-align: center; min-width: 70px;"><p style="font-size: 30px;"></p></div>
            <div style="text-align: left; min-width: 70px;"><p style="font-size: 30px;">{placar_inter}</p></div>
            """, unsafe_allow_html=True
        )

        if st.button("Registrar"):
            nova = {
                "Data": data.strftime("%d/%m/%Y"),
                "Número da Partida": numero_partida,
                "Placar Borussia": placar_borussia,
                "Gols Borussia": ", ".join(gols_borussia),
                "Placar Inter": placar_inter,
                "Gols Inter": ", ".join(gols_inter),
            }

            partidas = pd.concat([partidas, pd.DataFrame([nova])], ignore_index=True)

            partidas_limpo = partidas.fillna("").astype(str)
            jogadores_limpo = jogadores.fillna("").astype(str)
            presencas_limpo = presencas.fillna("").astype(str)

            save_data_gsheets(partidas_limpo, jogadores_limpo, usuarios, presencas_limpo)
            st.success("✅ Partida registrada com sucesso!")
            time.sleep(2)

            st.session_state["dados_gsheets"] = (partidas, jogadores, usuarios, presencas)
            st.session_state["form_id"] += 1
            st.rerun()

        st.markdown("---")
        st.markdown("<h5 style='text-align: center; font-weight: bold;'>✏️ Editar ou Excluir Partida Registrada</h5>", unsafe_allow_html=True)


        if not partidas.empty:
            opcoes = [
                f"#{row['Número da Partida']} – {row['Data']} – Borussia {row['Placar Borussia']} x {row['Placar Inter']} Inter"
                for _, row in partidas.iterrows()
            ]
            partida_escolhida = st.selectbox("Selecione a partida:", opcoes)
            index = opcoes.index(partida_escolhida)
            row = partidas.iloc[index]

            # inicializa flag se ainda não existir
            if "mostrar_edicao_partida" not in st.session_state:
                st.session_state.mostrar_edicao_partida = False

            col1, col2 = st.columns([1, 1])  # Largura adequada para os botões
            with col1:
                if st.button("✏️ Editar Partida", use_container_width=True):
                    st.session_state.mostrar_edicao_partida = True

            with col2:
                if st.button("🗑️ Excluir Partida", use_container_width=True):
                    partidas = partidas.drop(partidas.index[index]).reset_index(drop=True)

                    # Renumera as partidas
                    partidas["Data_Ordenada"] = pd.to_datetime(partidas["Data"], dayfirst=True, errors="coerce")
                    partidas = partidas.sort_values(by=["Data_Ordenada", "Número da Partida"]).reset_index(drop=True)
                    partidas["Número da Partida"] = partidas.groupby("Data_Ordenada").cumcount() + 1
                    partidas.drop(columns=["Data_Ordenada"], inplace=True)

                    jogadores, usuarios, presencas = st.session_state["dados_gsheets"][1:]
                    save_data_gsheets(partidas, jogadores, usuarios, presencas)
                    st.session_state["dados_gsheets"] = (partidas, jogadores, usuarios, presencas)

                    st.success("🗑️ Partida excluída com sucesso!")
                    time.sleep(2)
                    st.rerun()

            if st.session_state.mostrar_edicao_partida:
                with st.form("form_edicao_partida"):
                    nova_data = st.date_input("📅 Data da partida", value=pd.to_datetime(row["Data"], dayfirst=True))

                    novo_placar_borussia = st.number_input("Placar Borussia", value=int(row["Placar Borussia"]), min_value=0, max_value=2)
                    novo_gols_borussia = st.text_input("Goleadores Borussia", value=row["Gols Borussia"])
                    novo_placar_inter = st.number_input("Placar Inter", value=int(row["Placar Inter"]), min_value=0, max_value=2)
                    novo_gols_inter = st.text_input("Goleadores Inter", value=row["Gols Inter"])

                    col1, col2 = st.columns([1, 1])  # Largura adequada para os botões
                    with col1:
                        salvar = st.form_submit_button("💾 Salvar Alterações")
                    with col2:
                        cancelar = st.form_submit_button("❌ Cancelar Edição")

                if salvar:
                    partidas.at[index, "Data"] = nova_data.strftime("%d/%m/%Y") if pd.notnull(nova_data) else ""
                    partidas.at[index, "Placar Borussia"] = int(novo_placar_borussia)
                    partidas.at[index, "Gols Borussia"] = novo_gols_borussia
                    partidas.at[index, "Placar Inter"] = int(novo_placar_inter)
                    partidas.at[index, "Gols Inter"] = novo_gols_inter

                    # renumera as partidas
                    partidas["Data_Ordenada"] = pd.to_datetime(partidas["Data"], dayfirst=True)
                    partidas = partidas.sort_values(by="Data_Ordenada").reset_index(drop=True)
                    partidas["Número da Partida"] = partidas.groupby("Data_Ordenada").cumcount() + 1
                    partidas.drop(columns=["Data_Ordenada"], inplace=True)

                    jogadores, usuarios, presencas = st.session_state["dados_gsheets"][1:]
                    save_data_gsheets(partidas, jogadores, usuarios, presencas)
                    st.session_state["dados_gsheets"] = (partidas, jogadores, usuarios, presencas)

                    st.success("✅ Partida editada com sucesso!")
                    time.sleep(2)
                    st.session_state.mostrar_edicao_partida = False
                    st.rerun()

                elif cancelar:
                    st.session_state.mostrar_edicao_partida = False
                    st.rerun()
        else:
            st.info("Nenhuma partida registrada ainda.")
        st.markdown("---")
        st.markdown("<h5 style='text-align: center; font-weight: bold;'>📋 Histórico de Partidas Registradas</h5>", unsafe_allow_html=True)


        if "Gols Borussia" in partidas.columns and "Gols Inter" in partidas.columns:
            partidas = partidas.dropna(subset=["Gols Borussia", "Gols Inter"])

            # Resto do seu código segue aqui
        else:
            st.warning("⚠️ Ainda não há partidas registradas com gols.")
            return

        # Limpa dados incompletos
        partidas = partidas.dropna(subset=["Data", "Número da Partida"]).reset_index(drop=True)

        # Estilo para reduzir a altura da célula
        st.markdown(
            """
            <style>
            div[data-testid="stDataFrame"] td {
                padding-top: 2px !important;
                padding-bottom: 2px !important;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        # Configura DataFrame com índice começando de 1
        partidas = partidas.dropna(subset=["Data", "Número da Partida"]).reset_index(drop=True)
        partidas.index = partidas.index + 1
        partidas.index.name = "#"

        # Exibe com colunas ajustadas e célula mais compacta
        st.dataframe(partidas, use_container_width=True, hide_index=False)







    # Estatisticas dos jogadores
    def tela_presenca_login():
        _, _, usuarios_atualizados, _ = load_data()
        st.session_state["usuarios"] = usuarios_atualizados

        gc = autenticar_gsheets()
        sh = gc.open(NOME_PLANILHA)
        aba_presencas = sh.worksheet("Presenças")
        df_atualizado = get_as_dataframe(aba_presencas).dropna(how="all")

        presencas_dict = {}
        if "Email" in df_atualizado.columns and "Nome" in df_atualizado.columns and "Presença" in df_atualizado.columns:
            for _, row in df_atualizado.iterrows():
                presencas_dict[row["Email"]] = {
                    "nome": row["Nome"],
                    "presenca": "sim" if row["Presença"].strip().lower() == "sim" else "nao",
                    "motivo": row.get("Motivo", ""),
                }

            st.session_state["presencas_confirmadas"] = presencas_dict

        nome = st.session_state.get("nome", "usuário")
        usuarios = st.session_state.get("usuarios", {})
        email = st.session_state.get("email", "")

        # só carrega se ainda não estiver no session_state e não estiver mudando de ideia
        if "presenca_confirmada" not in st.session_state and not st.session_state.get("mudando_ideia", False):
            presenca_jogador = presencas_dict.get(email)
            if presenca_jogador:
                st.session_state["presenca_confirmada"] = presenca_jogador["presenca"]
                if presenca_jogador["presenca"] == "nao":
                    st.session_state["motivo"] = presenca_jogador.get("motivo", "")

        posicao = usuarios.get(email, {}).get("posicao", "Linha")

        agora = datetime.now()
        hoje = agora.weekday()
        dias_para_quinta = (3 - hoje) % 7
        proxima_quinta = agora + timedelta(days=dias_para_quinta)
        horario_partida = proxima_quinta.replace(hour=20, minute=0, second=0, microsecond=0)
        data_display = horario_partida.strftime("%d/%m/%Y às %Hh")

        st.markdown(
            f"<p style='font-size:18px; font-weight:bold; text-align:center;'>📅 Próxima partida: {data_display}</p>",
            unsafe_allow_html=True,
        )

        dias_para_quarta = (2 - hoje) % 7
        proxima_quarta = agora + timedelta(days=dias_para_quarta)
        prazo_limite = proxima_quarta.replace(hour=22, minute=0, second=0, microsecond=0)
        passou_do_prazo = agora > prazo_limite

        # só agora verifica se a resposta já foi enviada
        resposta_enviada = "presenca_confirmada" in st.session_state

        if passou_do_prazo:
            st.warning("⚠️ O prazo para confirmar presença ou ausência é toda **quarta-feira até às 22h**.")

        if resposta_enviada:
            status = st.session_state["presenca_confirmada"]
            if status == "sim":
                st.success(f"{nome}, sua **presença** foi confirmada com sucesso! ✅")
            else:
                motivo = st.session_state.get("motivo", "não informado")
                st.success(f"{nome}, sua **ausência** foi registrada com o motivo: **{motivo}** ❌")

        else:
            presenca = st.radio("Você vai comparecer?", ["✅ Sim", "❌ Não"], horizontal=True)
            motivo = ""
            motivo_outros = ""

            if presenca == "❌ Não":
                motivo = st.selectbox(
                    "Qual o motivo da ausência?",
                    ["Saúde", "Trabalho", "Compromisso acadêmico", "Viagem", "Problemas pessoais", "Lesão", "Outros"],
                )
                if motivo == "Outros":
                    motivo_outros = st.text_area("Descreva o motivo")

            if st.button("Enviar resposta"):
                st.session_state.pop("mudando_ideia", None)
                if presenca == "❌ Não" and motivo == "Outros" and not motivo_outros.strip():
                    st.warning("Descreva o motivo da ausência.")
                else:
                    fuso_utc_minus_3 = timezone(timedelta(hours=-3))
                    data_envio = datetime.now(fuso_utc_minus_3).strftime("%d/%m/%Y %H:%M:%S")
                    data_partida = horario_partida.date()

                    justificativa = motivo_outros.strip() if (presenca == "❌ Não" and motivo == "Outros") else (motivo if presenca == "❌ Não" else "")

                    nova_linha = {
                        "Nome": nome,
                        "Email": email,
                        "Posição": posicao,
                        "Presença": "Sim" if presenca == "✅ Sim" else "Não",
                        "DataPartida": data_partida.strftime("%Y-%m-%d"),
                        "Data": data_envio,
                        "Motivo": justificativa,
                    }

                    df_presencas = get_as_dataframe(aba_presencas).dropna(how="all")
                    df_presencas = pd.concat([df_presencas, pd.DataFrame([nova_linha])], ignore_index=True)
                    set_with_dataframe(aba_presencas, df_presencas)

                    st.session_state["presenca_confirmada"] = "sim" if presenca == "✅ Sim" else "nao"
                    if presenca == "❌ Não":
                        st.session_state["motivo"] = justificativa

                    # atualiza dicionário
                    df_atualizado = get_as_dataframe(aba_presencas).dropna(how="all")
                    presencas_dict = {}
                    for _, row in df_atualizado.iterrows():
                        presencas_dict[row["Email"]] = {
                            "nome": row["Nome"],
                            "presenca": "sim" if row["Presença"] == "Sim" else "nao",
                            "motivo": row.get("Motivo", ""),
                        }

                    st.session_state["presencas_confirmadas"] = presencas_dict
                    st.success("✅ Presença registrada com sucesso!")
                    st.rerun()

                # 🔁 Botão para mudar de ideia
                if st.button("🔁 Mudar de ideia"):
                    st.session_state.pop("presenca_confirmada", None)
                    st.session_state.pop("motivo", None)
                    st.session_state["mudando_ideia"] = True  # ← impede recarregar a info da planilha
                st.rerun()

        # ✅ Lista de presença sempre visível após as opções
        presencas = st.session_state.get("presencas_confirmadas", {})
        todos_usuarios = st.session_state.get("usuarios", {})

        linhas_html = ""
        confirmados = 0
        linha_confirmados = 0
        goleiros_confirmados = 0

        for email, dados_usuario in sorted(todos_usuarios.items(), key=lambda x: x[1]["nome"]):
            nome = dados_usuario["nome"]
            posicao = dados_usuario.get("posicao", "Linha")
            status = "❓"
            motivo = ""

            if email in presencas:
                presenca_info = presencas[email]
                if presenca_info.get("presenca") == "sim":
                    status = "✅"
                    confirmados += 1
                    if posicao and "goleiro" in posicao.strip().lower():
                        goleiros_confirmados += 1
                    else:
                        linha_confirmados += 1
                elif presenca_info.get("presenca") == "nao":
                    status = "❌"
                    motivo = presenca_info.get("motivo", "")

            # monta linha com posição
            if status == "❌" and motivo:
                linhas_html += f"<li>{status} {nome} ({posicao}) — <em>{motivo}</em></li>"
            else:
                linhas_html += f"<li>{status} {nome} ({posicao})</li>"

        st.markdown(
            f"""
            <div style="text-align: center; margin-top: 2rem;">
                <h6 style="text-align: center;">
                    📋 Presença da Semana — Confirmados: {confirmados}  
                    <br>👟 Jogadores de Linha: {linha_confirmados}  
                    <br>🧤 Goleiros: {goleiros_confirmados}
                </h6>
                <ul style="list-style-type: none; padding: 0; font-size: 1rem; line-height: 1.6;">
                    {linhas_html}
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )







    # Tela de sorteio

    def tela_sorteio():
        st.title("🎲 Sorteio de Times")
        st.markdown("Selecione a data da partida para sortear os times.")

        if "dados_gsheets" not in st.session_state:
            st.session_state["dados_gsheets"] = load_data()
        _, _, usuarios, presencas = st.session_state["dados_gsheets"]

        # Escolha da data
        data_partida = st.date_input("📅 Data da Partida")
        data_partida = pd.to_datetime(data_partida).date()

        # Converte coluna para datetime e filtra os confirmados
        presencas["DataPartida"] = pd.to_datetime(presencas["DataPartida"], errors="coerce").dt.date
        confirmados = presencas[
            (presencas["DataPartida"] == data_partida) &
            (presencas["Presença"].str.lower() == "sim")
        ]

        # Lista ordenada pela ordem na planilha
        nomes_confirmados = confirmados["Nome"].tolist()

        if len(nomes_confirmados) <= 15:
            st.warning("⚠️ É necessário pelo menos 15 jogadores confirmados para realizar o sorteio.")
            return

        if st.button("🎯 Sortear Times") or "times_sorteados" not in st.session_state:
            # Divide entre goleiros e linha, sem considerar ordem de confirmação
            goleiros = []
            linha = []

            for nome in nomes_confirmados:
                for email, dados in usuarios.items():
                    if dados["nome"] == nome:
                        if "goleiro" in dados.get("posicao", "").strip().lower():
                            goleiros.append(nome)
                        else:
                            linha.append(nome)
                        break

            # Embaralha tudo
            random.shuffle(goleiros)
            random.shuffle(linha)

            times = [[] for _ in range(2)]  # Time 1 e Time 2
            jogadores_restantes = linha.copy()
            goleiros_disponiveis = goleiros.copy()

            # Distribui goleiros para os dois primeiros times
            if goleiros_disponiveis:
                if len(goleiros_disponiveis) >= 1:
                    times[0].append(goleiros_disponiveis.pop(0))
                if len(goleiros_disponiveis) >= 1:
                    times[1].append(goleiros_disponiveis.pop(0))

            # Preencher os dois primeiros times com jogadores de linha
            for i in range(2):
                max_jogadores = 6 if any("goleiro" in usuario.lower() for usuario in times[i]) else 5
                while len(times[i]) < max_jogadores and jogadores_restantes:
                    times[i].append(jogadores_restantes.pop(0))

            # Criar mais times, se necessário
            while jogadores_restantes or goleiros_disponiveis:
                novo_time = []

                if goleiros_disponiveis:
                    novo_time.append(goleiros_disponiveis.pop(0))
                    max_jogadores = 6
                else:
                    max_jogadores = 5

                while len(novo_time) < max_jogadores and jogadores_restantes:
                    novo_time.append(jogadores_restantes.pop(0))

                times.append(novo_time)

            st.session_state.times_sorteados = times

            # Exibir os times
            cores = ["🟡", "🔵", "🟢", "🟣", "🟠", "🔴"]

            for i, time in enumerate(times, 1):
                cor = cores[(i - 1) % len(cores)]
                st.markdown(f"### {cor} Time {i}")
                for jogador in time:
                    st.markdown(f"- {jogador}")
                st.markdown("---")



        



    def tela_avaliacao_pos_jogo():
        FILE_VOTOS = "votacao.csv"

        # Cria arquivo de votos se não existir
        if not os.path.exists(FILE_VOTOS):
            df_votos = pd.DataFrame(columns=["Votante", "Craque", "Pereba", "Goleiro", "DataRodada"])
            df_votos.to_csv(FILE_VOTOS, index=False)

        df_votos = pd.read_csv(FILE_VOTOS)

        # Garante a coluna DataRodada
        if "DataRodada" not in df_votos.columns:
            df_votos["DataRodada"] = ""

        usuarios = st.session_state.get("usuarios", {})
        presencas = st.session_state.get("dados_gsheets", [])[3]

        # Determina a data da quinta-feira da semana atual (rodada)
        agora = datetime.now()
        hoje = agora.weekday()
        dias_para_quinta = (3 - hoje) % 7
        data_rodada = (agora + timedelta(days=dias_para_quinta)).date()

        # Data da quinta-feira da rodada (próxima ou atual)
        dias_para_quinta = (3 - hoje) % 7
        proxima_quinta = agora + timedelta(days=dias_para_quinta)
        data_rodada = proxima_quinta.date()

        # quarta-feira anterior à próxima quinta
        prazo_limite = proxima_quinta - timedelta(days=1)
        prazo_limite = prazo_limite.replace(hour=22, minute=0, second=0, microsecond=0)

        # Filtra jogadores que confirmaram presença para a rodada
        presencas["DataPartida"] = pd.to_datetime(presencas["DataPartida"], errors="coerce").dt.date
        confirmados = presencas[
            (presencas["DataPartida"] == data_rodada) &
            (presencas["Presença"].str.lower() == "sim")
        ]
        jogadores_presentes = confirmados["Nome"].tolist()
        st.session_state["jogadores_presentes"] = jogadores_presentes

        # Separa goleiros e jogadores de linha
        goleiros = []
        linha = []
        for j in jogadores_presentes:
            for _, info in usuarios.items():
                if info["nome"] == j:
                    if info.get("posicao", "Linha").strip().lower() == "goleiro":
                        goleiros.append(j)
                    else:
                        linha.append(j)
                    break

        st.markdown("<h5 style='font-weight: bold;'>😎 Tá na hora do veredito!</h5>", unsafe_allow_html=True)
        st.markdown("Vote no **craque**, **pereba** e **melhor goleiro** da rodada 🏆🥴🧤")

        votante = st.session_state.get("nome", "usuário")
        linha = [j for j in linha if j != votante]
        goleiros = [g for g in goleiros if g != votante]

        ja_votou = not df_votos[
            (df_votos["Votante"] == votante) & (df_votos["DataRodada"] == str(data_rodada))
        ].empty
            
        if not ja_votou:
            if votante not in jogadores_presentes:
                st.warning("⚠️ Apenas jogadores que confirmaram presença na rodada podem votar.")
                return


        with st.form("votacao_form"):
            # opções com placeholder
            craque_opcoes = ["-- Selecione --"] + linha
            craque = st.selectbox("⭐ Craque da rodada", options=craque_opcoes, index=0, key="select_craque")

            pereba = None
            if craque != "-- Selecione --":
                pereba_opcoes = ["-- Selecione --"] + [j for j in linha if j != craque]
                pereba = st.selectbox(
                    "🥴 Pereba da rodada",
                    options=pereba_opcoes,
                    index=0,
                    key="select_pereba"
                )
            else:
                st.info("👆 Selecione o craque antes de votar no pereba.")

            goleiro_opcoes = ["-- Selecione --"] + goleiros
            goleiro = st.selectbox("🧤 Melhor goleiro", options=goleiro_opcoes, index=0, key="select_goleiro")

            submit = st.form_submit_button("Votar")

            if submit:
                if (
                    craque == "-- Selecione --"
                    or pereba == "-- Selecione --"
                    or goleiro == "-- Selecione --"
                ):
                    st.error("⚠️ Preencha todas as categorias antes de votar.")
                elif craque == pereba:
                    st.error("⚠️ O craque e o pereba devem ser jogadores diferentes.")
                else:
                    novo_voto = pd.DataFrame([{
                        "Votante": votante,
                        "Craque": craque,
                        "Pereba": pereba,
                        "Goleiro": goleiro,
                        "DataRodada": str(data_rodada)
                    }])
                    df_votos = pd.concat([df_votos, novo_voto], ignore_index=True)
                    df_votos.to_csv(FILE_VOTOS, index=False)
                    st.success("✅ Voto registrado com sucesso!")
                    st.rerun()


        

        # Exibir resultados da rodada atual
        if ja_votou:
            df_votos_rodada = df_votos[df_votos["DataRodada"] == str(data_rodada)]

            def gerar_html_podio(serie, titulo, icone):
                df = serie.value_counts().reset_index()
                df.columns = ["Jogador", "Votos"]
                podium_colors = ["#FFD700", "#C0C0C0", "#CD7F32"]
                podium_labels = ["🥇", "🥈", "🥉"]

                podium_html = f"<h3 style='margin-bottom: 20px;'>{icone} {titulo}</h3>"
                podium_html += "<div style='display: flex; justify-content: center; align-items: end; gap: 40px;'>"

                top_votos = df["Votos"].unique()[:3]

                for i, votos in enumerate(top_votos):
                    jogadores_empate = df[df["Votos"] == votos]["Jogador"].tolist()
                    nomes = "<br>".join(jogadores_empate)
                    podium_html += (
                        "<div style='text-align: center;'>"
                        f"<div style='background-color: {podium_colors[i]};"
                        f"padding: 10px 15px;"
                        f"border-radius: 8px;"
                        f"font-weight: bold;"
                        f"font-size: 18px;"
                        f"min-width: 100px;"
                        f"box-shadow: 2px 2px 5px #aaa;"
                        f"text-align: center;'>"
                        f"{podium_labels[i]}<br>{nomes}<br>{votos} voto(s)"
                        "</div></div>"
                    )

                podium_html += "</div>"
                return podium_html

            st.markdown(gerar_html_podio(df_votos_rodada["Craque"], "Craque da Chopp's League (Top 3)", "🏆"), unsafe_allow_html=True)
            st.markdown(gerar_html_podio(df_votos_rodada["Pereba"], "Pereba da Chopp's League (Top 3)", "🐢"), unsafe_allow_html=True)
            st.markdown(gerar_html_podio(df_votos_rodada["Goleiro"], "Melhor Goleiro da Rodada (Top 3)", "🧤"), unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

            # Opção de apagar votos da rodada - acesso restrito
            email_autorizado = "matheusmoreirabr@hotmail.com"
            email_usuario = st.session_state.get("email", "")

            if email_usuario.lower() == email_autorizado:
                with st.expander("⚠️ Apagar votos da rodada atual"):
                    st.markdown("Esta ação irá remover **todos os votos registrados** para a rodada atual. Não poderá ser desfeita.")
                    if st.button("🗑️ Apagar votos desta rodada"):
                        df_votos = df_votos[df_votos["DataRodada"] != str(data_rodada)]
                        df_votos.to_csv(FILE_VOTOS, index=False)
                        st.success("✅ Votos da rodada apagados com sucesso. Recarregue a página para atualizar.")
                        # Mostra botão para recarregar
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("🔄 Recarregar página"):
                            st.rerun()

    # Midias
    def tela_galeria_momentos():
        st.title("📸 Galeria de Momentos da Chopp's League")

        st.markdown(
            "Veja os melhores registros da Chopp's League: gols, resenhas e lembranças 🍻⚽"
        )

        # --- TÓPICOS DA GALERIA ---
        topicos = {
            "🏖️ Confraternizações": "midia/confraternizacoes",
            "🔥 Jogadas Bonitas": "midia/jogadas_bonitas",
            "😂 Lances Engraçados": "midia/lances_engracados",
            "🥅 Gols Incríveis": "midia/gols_incriveis",
            "🎉 Bastidores & Zoações": "midia/bastidores",
        }

        for titulo, pasta in topicos.items():
            st.markdown(f"### {titulo}")

            if not os.path.exists(pasta):
                st.info("Nenhum conteúdo disponível ainda.")
                continue

            arquivos = sorted(os.listdir(pasta))
            imagens = [
                a for a in arquivos if a.lower().endswith((".png", ".jpg", ".jpeg"))
            ]
            videos = [
                a for a in arquivos if a.lower().endswith((".mp4", ".mov", ".webm"))
            ]

            col1, col2 = st.columns(2)

            with col1:
                for img in imagens:
                    st.image(
                        os.path.join(pasta, img), caption=img, use_container_width=True
                    )

            with col2:
                for vid in videos:
                    st.video(os.path.join(pasta, vid))

            st.markdown("---")

    # Fórum
    def tela_forum():
        FILE_FORUM = "forum.csv"

        # Cria o arquivo se não existir
        if not os.path.exists(FILE_FORUM):
            df_forum = pd.DataFrame(columns=["Autor", "Mensagem", "DataHora"])
            df_forum.to_csv(FILE_FORUM, index=False)

        # Carrega os dados existentes
        df_forum = pd.read_csv(FILE_FORUM)

        st.title("💬 Fórum")
        nome = st.session_state.get("nome", "Anônimo")

        # --- Campo para novo comentário ---
        with st.form("form_comentario"):
            st.markdown(f"Escreva algo, **{nome}**:")
            mensagem = st.text_area(
                "Mensagem",
                placeholder="Digite seu comentário aqui...",
                max_chars=500,
                label_visibility="collapsed",
            )
            enviar = st.form_submit_button("Enviar")

            if enviar:
                if mensagem.strip() == "":
                    st.warning("O comentário não pode estar vazio.")
                else:
                    novo = pd.DataFrame(
                        [
                            {
                                "Autor": nome,
                                "Mensagem": mensagem.strip(),
                                "DataHora": datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                            }
                        ]
                    )
                    df_forum = pd.concat([df_forum, novo], ignore_index=True)
                    df_forum.to_csv(FILE_FORUM, index=False)
                    st.success("Comentário publicado!")

        # --- Exibe comentários existentes (mais recentes primeiro) ---
        st.markdown("### 🖊️ Comentários recentes")

        if df_forum.empty:
            st.info("Ainda não há comentários. Seja o primeiro a escrever! 🤙")
        else:
            # Ordena por data decrescente
            df_forum["DataHora"] = pd.to_datetime(df_forum["DataHora"])
            df_forum = df_forum.sort_values(by="DataHora", ascending=False)

            for _, row in df_forum.iterrows():
                st.markdown(
                    f"""
                <div style='border:1px solid #ddd; border-radius:8px; padding:10px; margin-bottom:10px; background-color: #f9f9f9;'>
                    <strong>{row['Autor']}</strong> <span style='color:gray; font-size:12px;'>({row['DataHora'].strftime('%d/%m/%Y %H:%M')})</span>
                    <div style='margin-top:5px;'>{row['Mensagem']}</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

    # Tela de mensagem a gestão
    def tela_comunicado():
        st.title("📣 Comunicado à Gestão")

        nome = st.session_state.get("nome", "usuário")
        telefone = st.session_state.get("telefone", "não informado")
        email = st.session_state.get("email", "não informado")

        st.markdown(
            f"""
            <p>Use o espaço abaixo para enviar um comunicado à organização. 
            Assim que você clicar em <strong>Enviar via WhatsApp</strong>, a mensagem será aberta no aplicativo do WhatsApp com seus dados preenchidos.</p>
        """,
            unsafe_allow_html=True,
        )

        mensagem = st.text_area(
            "✉️ Sua mensagem",
            height=150,
            placeholder="Digite aqui sua sugestão, reclamação ou comunicado...",
        )

        if st.button("📤 Enviar via WhatsApp"):
            if not mensagem.strip():
                st.warning("Digite uma mensagem antes de enviar.")
            else:
                numero_destino = "5531991159656"  # Brasil + DDD + número
                texto = f"""Olá, aqui é {nome}!

    Telefone: {telefone}
    Email: {email}

    📣 Comunicado:
    {mensagem}
    """
                texto_codificado = urllib.parse.quote(texto)
                link = f"https://wa.me/{numero_destino}?text={texto_codificado}"
                st.success(
                    "Clique no botão abaixo para abrir o WhatsApp com sua mensagem:"
                )
                st.markdown(f"[📲 Abrir WhatsApp]({link})", unsafe_allow_html=True)

    # Tela das Regras
    def tela_regras():
        st.markdown(
            "<h1 style='font-size:23px;'>🛑 Regras Oficiais</h1>",
            unsafe_allow_html=True,
        )
        st.markdown("---")

        def subtitulo(txt):
            st.markdown(
                f'<h3 style="font-size:20px; margin-top: 1em;">{txt}</h3>',
                unsafe_allow_html=True,
            )

        subtitulo("✅ 1. Confirmação de Presença")
        st.markdown(
            """
        - Os jogadores devem confirmar presença **até as 22h de quarta-feira**.
        - Quem não confirmar no prazo **não poderá jogar**.
        - A partida só será confirmada se houver, no mínimo, 15 jogadores confirmados.
        """
        )

        subtitulo("⌛ 2. Tempo de Jogo e Rodízio")
        st.markdown(
            """
        - Cada partida terá duração de **7 minutos ou até 2 gols**, o que ocorrer primeiro.
        - O **time que entra joga pelo empate**:
            - Se empatar, o **time vencedor da partida anterior sai**.
            - Se perder, o **time que entrou sai normalmente**.
        """
        )

        subtitulo("👕 3. Uniforme Obrigatório")
        st.markdown(
            """
        - É obrigatório comparecer com o uniforme padrão completo:
            - Camisa do **Borussia Dortmund**
            - Camisa da **Inter de Milão**
            - **Calção preto**
            - **Meião preto**
        - Jogadores sem o uniforme completo **não poderão jogar**.
        """
        )

        subtitulo("💰 4. Mensalidade e Pagamento")
        st.markdown(
            """
        - A mensalidade deve ser paga **até o dia 10 de cada mês**.
        - **Jogadores inadimplentes não poderão jogar até quitar sua dívida**.
        - **Goleiros são isentos da mensalidade**, mas devem pagar **o uniforme**.
        """
        )

        subtitulo("💸 5. Contribuição para o Caixa")
        st.markdown(
            """
        - Todos os jogadores, incluindo goleiros, devem contribuir com **R$20,00 adicionais**.
        - O valor será utilizado exclusivamente para:
            - **Materiais esportivos** (bolas, bomba de encher bola, etc.)
            - **Itens médicos** (Gelol, faixa, esparadrapo, gelo, etc.)
            - **Água**
            - **Confraternizações** ou outras necessidades da Chopp's League
        """
        )

        subtitulo("📅 6. Comprometimento")
        st.markdown(
            """
        - Ao confirmar presença, o jogador assume o compromisso de comparecer.
        - **Faltas não justificadas** podem resultar em **suspensão da próxima rodada**.
        """
        )

        subtitulo("⚠️ 7. Comportamento")
        st.markdown(
            """
        - Discussões, brigas ou qualquer tipo de agressividade resultam em **suspensão automática da próxima rodada**.
        - Em caso de reincidência, o jogador poderá ser **banido temporariamente ou definitivamente**, conforme decisão da gestão.
        """
        )

        subtitulo("🧤 8. Goleiros e Rodízio")
        st.markdown(
            """
        - Na ausência de goleiro fixo, haverá **rodízio entre os jogadores de linha** para cobrir o gol.
        """
        )

        subtitulo("🔊 9. Arbitragem")
        st.markdown(
            """
        - **Um jogador que estiver de fora durante a rodada será o responsável por apitar a partida.**  
        **Todos devem respeitar as decisões de arbitragem feitas por jogadores designados.**
            """
        )

        subtitulo("🔐 10. Responsabilidade")
        st.markdown(
            """
        - Comprometimento com **pagamentos, presença e respeito** é essencial para manter a organização.
        - **Quem não estiver em dia com os compromissos não joga.**
        """
        )

        subtitulo("⭐ 11. Avaliação Pós-Jogo: Péreba e Craque")
        st.markdown(
            """
        - Após cada partida, será feita uma votação divertida para eleger:
            - **⭐ Craque**: jogador com a melhor performance.
            - **🐢 Péreba**: jogador com a pior performance da rodada.
            - **🧤 Paredão:** goleiro com a melhor atuação defensiva da rodada.
        - A votação é **exclusiva para quem confirmou presença e jogou na partida do dia**.
        - Somente jogadores presentes poderão votar.
        - A finalidade é **uma brincadeira para animar o grupo e fortalecer o espírito da Chopp's League**.
        - Os resultados serão divulgados para descontração na tela **'Avaliação pós-jogo'**.
        """
        )

    # Inicialização de sessão
    if "pagina_atual" not in st.session_state:
        st.session_state.pagina_atual = "login"

    if "nome" not in st.session_state:
        st.session_state.nome = "usuário"

    # Dados fictícios para partidas
    if "partidas" not in st.session_state:
        st.session_state.partidas = pd.DataFrame(
            columns=[
                "Data",
                "Número da Partida",
                "Placar Borussia",
                "Gols Borussia",
                "Placar Inter",
                "Gols Inter",
            ]
        )

    partidas = st.session_state.partidas

    # Roteador de páginas
    if st.session_state.pagina_atual == "🏠 Tela Principal":
        tela_principal(partidas, jogadores)
    elif st.session_state.pagina_atual == "👤 Meu Perfil":
        tela_meu_perfil()
    elif st.session_state.pagina_atual == "📊 Registrar Partida":
        registrar_partidas()
    elif st.session_state.pagina_atual == "👟 Estatísticas dos Jogadores":
        jogadores = tela_jogadores(jogadores)
    elif st.session_state.pagina_atual == "🎲 Sorteio de Times":
        tela_sorteio()
    elif st.session_state.pagina_atual == "✅ Confirmar Presença/Ausência":
        tela_presenca_login()
    elif st.session_state.pagina_atual == "🏅 Avaliação Pós-Jogo":
        tela_avaliacao_pos_jogo()
    elif st.session_state.pagina_atual == "📸 Galeria de Momentos":
        tela_galeria_momentos()
    elif st.session_state.pagina_atual == "💬 Fórum":
        tela_forum()
    elif st.session_state.pagina_atual == "📣 Comunicado à Gestão":
        tela_comunicado()
    elif st.session_state.pagina_atual == "📜 Regras Chopp's League":
        tela_regras()
