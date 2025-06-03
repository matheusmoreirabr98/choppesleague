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


    if "Avaliação Pós-Jogo" not in existentes:
        df_avaliacao = pd.DataFrame(columns=["Votante", "Craque", "Pereba", "Goleiro", "DataRodada"])
        sh.add_worksheet(title="Avaliação Pós-Jogo", rows="100", cols="20")
        set_with_dataframe(sh.worksheet("Avaliação Pós-Jogo"), df_avaliacao)

    if "Mensalidades" not in existentes:
        df_mensalidades = pd.DataFrame(columns=["Email", "Nome", "Mês", "Pago"])  # ou personalize as colunas
        sh.add_worksheet(title="Mensalidades", rows="100", cols="20")
        set_with_dataframe(sh.worksheet("Mensalidades"), df_mensalidades)

    if "Transparência" not in existentes:
        df_transparencia = pd.DataFrame(columns=["Data", "Tipo", "Descrição", "Valor", "Responsável"])
        sh.add_worksheet(title="Transparência", rows="100", cols="20")
        set_with_dataframe(sh.worksheet("Transparência"), df_transparencia)

# -----------------------------------------
# Carregar dados das planilhas
# -----------------------------------------
def load_data_gsheets():
    gc = autenticar_gsheets()
    sh = gc.open(NOME_PLANILHA)

    # Lista das abas obrigatórias
    abas_necessarias = [
        "Partidas", "Jogadores", "Usuarios", "Presenças",
        "Avaliação Pós-Jogo", "Mensalidades", "Transparência"
    ]    
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
    avaliacao = get_as_dataframe(sh.worksheet("Avaliação Pós-Jogo")).dropna(how="all")
    mensalidades = get_as_dataframe(sh.worksheet("Mensalidades")).dropna(how="all")
    transparencia = get_as_dataframe(sh.worksheet("Transparência")).dropna(how="all")

    # Converter para dicionário com e-mail como chave
    usuarios = {}
    if not usuarios_df.empty and "email" in usuarios_df.columns:
        for _, row in usuarios_df.iterrows():
            if pd.notna(row["email"]):
                usuarios[row["email"]] = row.drop(labels="email").to_dict()

    return partidas, jogadores, usuarios, presencas, avaliacao, mensalidades, transparencia


# -----------------------------------------
# Salvar dados nas planilhas
# -----------------------------------------
def save_data_gsheets(partidas, jogadores, usuarios, presencas, avaliacao, mensalidades, transparencia):
    gc = autenticar_gsheets()
    sh = gc.open(NOME_PLANILHA)

    # Sanitize
    partidas = sanitize_df(partidas)
    jogadores = sanitize_df(jogadores)
    presencas = sanitize_df(presencas)
    avaliacao = sanitize_df(avaliacao)
    mensalidades = sanitize_df(mensalidades)
    transparencia = sanitize_df(transparencia)

    # Salvar partidas
    sheet = sh.worksheet("Partidas")
    sheet.clear()
    sheet.update([partidas.columns.tolist()] + partidas.values.tolist())

    # Salvar jogadores
    sheet = sh.worksheet("Jogadores")
    sheet.clear()
    sheet.update([jogadores.columns.tolist()] + jogadores.values.tolist())

    # Salvar usuários
    sheet = sh.worksheet("Usuarios")
    sheet.clear()
    usuarios_df = pd.DataFrame.from_dict(usuarios, orient="index").reset_index().rename(columns={"index": "email"})
    usuarios_df = sanitize_df(usuarios_df)
    sheet.update([usuarios_df.columns.tolist()] + usuarios_df.values.tolist())

    # Salvar presenças
    sheet = sh.worksheet("Presenças")
    sheet.clear()
    sheet.update([presencas.columns.tolist()] + presencas.values.tolist())

    # Salvar avaliação pós-jogo
    sheet = sh.worksheet("Avaliação Pós-Jogo")
    sheet.clear()
    sheet.update([avaliacao.columns.tolist()] + avaliacao.values.tolist())

    # Salvar mensalidades
    sheet = sh.worksheet("Mensalidades")
    sheet.clear()
    sheet.update([mensalidades.columns.tolist()] + mensalidades.values.tolist())

    # Salvar transparência
    sheet = sh.worksheet("Transparência")
    sheet.clear()
    sheet.update([transparencia.columns.tolist()] + transparencia.values.tolist())


# -----------------------------------------
# Abstrações para carregar/salvar
# -----------------------------------------
def load_data():
    return load_data_gsheets()
time.sleep(1)


def save_data(partidas, jogadores, usuarios, presencas, avaliacao, mensalidades, transparencia):
    save_data_gsheets(partidas, jogadores, usuarios, presencas, avaliacao, mensalidades, transparencia)


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
        "<h1 style='font-size: 1.6rem; text-align: center;'>🔐 Login / Cadastro</h1>",
        unsafe_allow_html=True,
    )
    aba = st.radio(
        "Escolha uma opção:", ["Login", "Cadastro"], key="aba_login", horizontal=True
    )

    partidas, jogadores, usuarios, presencas, avaliacao, mensalidades, transparencia = load_data()  # ← lê os usuários direto da planilha

    # LOGIN
    if aba == "Login":
        if not st.session_state.modo_recuperacao:
            with st.form("form_login"):
                email = st.text_input("E-mail", key="login_email")
                senha = st.text_input("Senha", type="password", key="login_senha")
                st.markdown(
                    "<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True
                )
                submit = st.form_submit_button("Entrar", use_container_width=True)

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
            if st.button("Esqueci minha senha", use_container_width=True):
                st.session_state.modo_recuperacao = True
                st.rerun()

        if st.session_state.modo_recuperacao:
            st.markdown(
                "<h3 style='margin-top: 1rem;'>🔁 Atualize sua senha</h3>",
                unsafe_allow_html=True,
            )

            if st.button("🔙 Voltar para o login", use_container_width=True):
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
                confirmar = st.form_submit_button("Atualizar senha", use_container_width=True)

                if confirmar:
                    if email not in usuarios:
                        st.error("E-mail não encontrado.")
                    elif palavra_chave_rec != usuarios[email]["palavra_chave"]:
                        st.error("Palavra-chave incorreta.")
                    elif nova_senha != confirmar_nova_senha:
                        st.error("As novas senhas não coincidem.")
                    else:
                        # primeiro carrega os dados ATUALIZADOS da planilha
                        partidas, jogadores, usuarios, presencas, avaliacao, mensalidades, transparencia = load_data()

                        # depois altera a senha na versão correta de `usuarios`
                        usuarios[email]["senha"] = nova_senha

                        # agora salva com a senha atualizada
                        save_data(partidas, jogadores, usuarios, presencas, avaliacao, mensalidades, transparencia)
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
            submit = st.form_submit_button("Cadastrar", use_container_width=True)

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

                    save_data(partidas, jogadores, usuarios, presencas, avaliacao, mensalidades, transparencia)

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
            "💰 Controle da Mensalidade",
            "🏦 Portal da Transparência",
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
            "🏦 Portal da Transparência",
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

    def tela_pagamento_mensalidade():
        pass

    def tela_portal_transparencia():
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
        _, _, usuarios, _, _, _, _ = load_data()
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
            partidas, jogadores, usuarios, presencas, avaliacao, mensalidades, transparencia = load_data()
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

                save_data_gsheets(partidas, jogadores, usuarios, presencas, avaliacao, mensalidades, transparencia)

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
    elif pag == "💰 Controle da Mensalidade":
        tela_pagamento_mensalidade()
    elif pag == "🏦 Portal da Transparência":
        tela_portal_transparencia()
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

    def save_data(partidas, jogadores, usuarios, presencas, avaliacao, mensalidades, transparencia):
        save_data_gsheets(partidas, jogadores, usuarios, presencas, avaliacao, mensalidades, transparencia=[])

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

        partidas, jogadores, _, _, _, _, _ = st.session_state["dados_gsheets"]
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
            <div style="text-align: center; min-width: 100px;">
                <p style="font-size: 25px;">
                    🏆 - {borussia_vitorias}<br>
                    ⚽ - {gols_borussia}
                </p>
            </div>

            <div style="text-align: center; min-width: 5px;">
                <p style="font-size: 25px;">
                    🤝<br>
                    {empates}
                </p>
            </div>

            <div style="text-align: center; min-width: 100px;">
                <p style="font-size: 25px;">
                    {inter_vitorias} - 🏆<br>
                    {gols_inter} - ⚽
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )







    # Tela de registro das partidas
# Tela de registro das partidas
    def registrar_partidas():
        st.markdown("<h5 style='text-align: center; font-weight: bold;'>Registrar Estatísticas da Partida</h5>", unsafe_allow_html=True)
        st.markdown("---")

        if "dados_gsheets" not in st.session_state:
            st.session_state["dados_gsheets"] = load_data()
        partidas, jogadores, usuarios, presencas, avaliacao, mensalidades, transparencia = st.session_state["dados_gsheets"]
        presencas.rename(columns={"Nome do Jogador": "Nome", "Data da partida": "DataPartida"}, inplace=True)

        if "form_id" not in st.session_state:
            st.session_state["form_id"] = 0

        # garante a existência da coluna "Data" mesmo com DataFrame vazio
        if "Data" not in partidas.columns:
            partidas["Data"] = pd.NaT

        if not partidas.empty:
            partidas["Data"] = pd.to_datetime(partidas["Data"], dayfirst=True, errors='coerce').dt.date
            presencas["DataPartida"] = pd.to_datetime(presencas["DataPartida"], errors="coerce").dt.date
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

        data = st.date_input("📅 Data da partida")
        partidas_do_dia = partidas[partidas["Data"] == data]
        numero_partida = len(partidas_do_dia) + 1

        jogadores_presentes_data = presencas[(presencas["DataPartida"] == data) & (presencas["Presença"] == "sim")]["Nome"].tolist()

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
            if not gols_borussia:
                gols_borussia = ["Ninguém marcou"]
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
            if not gols_inter:
                gols_inter = ["Ninguém marcou"]
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

        if st.button("Registrar", use_container_width=True):
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
            avaliacao_limpo = avaliacao.fillna("").astype(str)
            mensalidades_limpo = mensalidades.fillna("").astype(str)
            transparencia_limpo = transparencia.fillna("").astype(str)

            save_data_gsheets(partidas_limpo, jogadores_limpo, usuarios, presencas_limpo, avaliacao_limpo, mensalidades_limpo, transparencia_limpo)
            st.success("✅ Partida registrada com sucesso!")
            time.sleep(2)

            st.session_state["dados_gsheets"] = (partidas, jogadores, usuarios, presencas, avaliacao, mensalidades, transparencia)
            st.session_state["form_id"] += 1
            st.rerun()

        st.markdown("---")
        st.markdown("<h5 style='text-align: center; font-weight: bold;'>📋 Histórico de Partidas Registradas</h5>", unsafe_allow_html=True)

        if "Data" in partidas.columns and "Número da Partida" in partidas.columns:
            partidas = partidas.dropna(subset=["Data", "Número da Partida"]).reset_index(drop=True)
            partidas.index = partidas.index + 1
            partidas.index.name = "#"
            colunas_exibidas = ["Data", "Número da Partida", "Placar Borussia", "Placar Inter"]
            st.dataframe(partidas[colunas_exibidas], use_container_width=True, hide_index=False)

            # Botão para excluir todas as partidas (apenas para email autorizado)
            if st.session_state.get("email") == "matheusmoreirabr@hotmail.com":
                if st.button("🗑️ Excluir todas as partidas", use_container_width=True):
                    partidas = partidas.iloc[0:0]  # limpa todas as linhas
                    save_data_gsheets(partidas, jogadores, usuarios, presencas, avaliacao, mensalidades, transparencia)
                    st.success("Todas as partidas foram excluídas com sucesso!")
                    st.session_state["dados_gsheets"] = (partidas, jogadores, usuarios, presencas, avaliacao, mensalidades, transparencia)
                    st.rerun()
        else:
            st.warning("⚠️ Ainda não há partidas registradas válidas.")






    # Estatisticas dos jogadores
    def tela_jogadores():
        st.title("\U0001F45F Estatísticas dos Jogadores")

        if "dados_gsheets" not in st.session_state:
            st.session_state["dados_gsheets"] = load_data()

        dados = st.session_state["dados_gsheets"]
        partidas, jogadores_data, usuarios, presencas, avaliacao, mensalidades, _ = dados

        df_votos = pd.read_csv("votacao.csv") if os.path.exists("votacao.csv") else pd.DataFrame(columns=["Craque", "Pereba", "Goleiro", "DataRodada"])

        mes_referencia = datetime.now().strftime("%m/%Y")

        estatisticas = []
        for email, usuario in usuarios.items():
            nome = usuario["nome"]
            posicao = usuario.get("posicao", "Linha")

            gols_total = sum(nome in str(g).split(", ") for g in pd.concat([
                partidas["Gols Borussia"].fillna(""),
                partidas["Gols Inter"].fillna("")
            ]))

            craques = df_votos["Craque"].tolist().count(nome) if posicao.lower() == "linha" else "-"
            perebas = df_votos["Pereba"].tolist().count(nome) if posicao.lower() == "linha" else "-"
            paredoes = df_votos["Goleiro"].tolist().count(nome) if posicao.lower() == "goleiro" else "-"

            presencas_usuario = presencas[presencas["Nome"] == nome]
            presencas_usuario = presencas_usuario.sort_values("Data", ascending=True)
            ultima_presenca = presencas_usuario.groupby("DataPartida").last().reset_index()

            qnt_presencas = ultima_presenca["Presença"].str.lower().tolist().count("sim")
            qnt_ausencias = ultima_presenca["Presença"].str.lower().tolist().count("não")

            mensalidade_paga = usuario.get("pagamentos", {}).get(mes_referencia, False)
            mensalidade_status = "✅" if mensalidade_paga else "❌"

            estatisticas.append({
                "👤": nome,
                "🎯": posicao,
                "⚽": gols_total,
                "⭐": craques,
                "🐢": perebas,
                "🧤": paredoes,
                "✅": qnt_presencas,
                "❌": qnt_ausencias,
                "💰": mensalidade_status
            })

        df_estatisticas = pd.DataFrame(estatisticas)
        df_estatisticas.index += 1
        df_estatisticas.index.name = "#"

        # Aplica centralização ao conteúdo da tabela via estilo
        st.markdown("""
            <style>
                table td, table th {
                    text-align: center !important;
                    vertical-align: middle !important;
                }

                [data-testid="stDataFrame"] .row-widget.stDataFrame div {
                    justify-content: center;
                }
            </style>
        """, unsafe_allow_html=True)

        st.dataframe(df_estatisticas, use_container_width=True)






    # Presença/Ausência
    def tela_presenca_login():
        _, _, usuarios_atualizados, _, _, _, _ = load_data()
        st.session_state["usuarios"] = usuarios_atualizados

        nome = st.session_state.get("nome", "usuário")
        usuarios = st.session_state.get("usuarios", {})
        email = st.session_state.get("email", "")
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

        if passou_do_prazo:
            st.warning("⚠️ O prazo para confirmar presença ou ausência é toda **quarta-feira até às 22h**.")

        # carregar confirmação anterior, se não estiver mudando de ideia
        if "presenca_confirmada" not in st.session_state and not st.session_state.get("mudando_ideia", False):
            # carrega apenas a linha do próprio usuário
            gc = autenticar_gsheets()
            sh = gc.open(NOME_PLANILHA)
            aba_presencas = sh.worksheet("Presenças")
            df = get_as_dataframe(aba_presencas).dropna(how="all")

            for _, row in df.iterrows():
                if row.get("Email", "") == email:
                    st.session_state["presenca_confirmada"] = "sim" if row["Presença"].strip().lower() == "sim" else "nao"
                    st.session_state["motivo"] = row.get("Motivo", "")
                    break

        resposta_enviada = "presenca_confirmada" in st.session_state

        # 👉 SE JÁ RESPONDEU
        if resposta_enviada:
            status = st.session_state["presenca_confirmada"]
            if status == "sim":
                st.success(f"{nome}, sua **presença** foi confirmada com sucesso! ✅")
            else:
                motivo = st.session_state.get("motivo", "não informado")
                st.success(f"{nome}, sua **ausência** foi registrada com o motivo: **{motivo}** ❌")

            # botão para mudar de ideia
            if st.button("🔁 Mudar de ideia"):
                st.session_state.pop("presenca_confirmada", None)
                st.session_state.pop("motivo", None)
                st.session_state["mudando_ideia"] = True
                st.rerun()

            # carrega e exibe a lista somente após resposta
            gc = autenticar_gsheets()
            sh = gc.open(NOME_PLANILHA)
            aba_presencas = sh.worksheet("Presenças")
            df = get_as_dataframe(aba_presencas).dropna(how="all")

            presencas_dict = {}
            for _, row in df.iterrows():
                presencas_dict[row["Email"]] = {
                    "nome": row["Nome"],
                    "presenca": "sim" if row["Presença"].strip().lower() == "sim" else "nao",
                    "motivo": row.get("Motivo", ""),
                }
            st.session_state["presencas_confirmadas"] = presencas_dict

            presencas = st.session_state["presencas_confirmadas"]
            todos_usuarios = st.session_state.get("usuarios", {})

            linhas_html = ""
            confirmados = 0
            linha_confirmados = 0
            goleiros_confirmados = 0

            for email_u, dados_usuario in sorted(todos_usuarios.items(), key=lambda x: x[1]["nome"]):
                nome_u = dados_usuario["nome"]
                posicao_u = dados_usuario.get("posicao", "Linha")
                status = "❓"
                motivo = ""

                info = presencas.get(email_u)
                if info:
                    if info["presenca"] == "sim":
                        status = "✅"
                        confirmados += 1
                        if "goleiro" in posicao_u.strip().lower():
                            goleiros_confirmados += 1
                        else:
                            linha_confirmados += 1
                    elif info["presenca"] == "nao":
                        status = "❌"
                        motivo = info.get("motivo", "")

                if status == "❌" and motivo:
                    linhas_html += f"<li>{status} {nome_u} ({posicao_u}) — <em>{motivo}</em></li>"
                else:
                    linhas_html += f"<li>{status} {nome_u} ({posicao_u})</li>"

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

        # 👉 SE AINDA NÃO RESPONDEU
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

                    gc = autenticar_gsheets()
                    sh = gc.open(NOME_PLANILHA)
                    aba_presencas = sh.worksheet("Presenças")
                    df = get_as_dataframe(aba_presencas).dropna(how="all")
                    df = pd.concat([df, pd.DataFrame([nova_linha])], ignore_index=True)
                    set_with_dataframe(aba_presencas, df)

                    st.session_state["presenca_confirmada"] = "sim" if presenca == "✅ Sim" else "nao"
                    if presenca == "❌ Não":
                        st.session_state["motivo"] = justificativa

                    st.rerun()









    # Tela de sorteio

    def tela_sorteio():
        st.title("🎲 Sorteio de Times")
        st.markdown("Selecione a data da partida para sortear os times.")

        if "dados_gsheets" not in st.session_state:
            st.session_state["dados_gsheets"] = load_data()
        _, _, usuarios, presencas, _, _, _ = st.session_state["dados_gsheets"]

        data_partida = st.date_input("📅 Data da Partida")
        data_partida = pd.to_datetime(data_partida).date()

        presencas["DataPartida"] = pd.to_datetime(presencas["DataPartida"], errors="coerce").dt.date
        confirmados = presencas[(presencas["DataPartida"] == data_partida) & (presencas["Presença"].str.lower() == "sim")]

        nomes_confirmados = confirmados["Nome"].tolist()

        if len(nomes_confirmados) <= 10:
            st.warning("⚠️ É necessário pelo menos 10 jogadores confirmados para realizar o sorteio.")
            return

        if st.button("🎯 Sortear Times") or "times_sorteados" not in st.session_state:
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

            random.shuffle(goleiros)
            random.shuffle(linha)

            times = [[] for _ in range(2)]
            jogadores_usados = set()

            # Distribui goleiros para os dois primeiros times
            if goleiros:
                if len(goleiros) >= 1:
                    times[0].append(goleiros[0])
                    jogadores_usados.add(goleiros[0])
                if len(goleiros) >= 2:
                    times[1].append(goleiros[1])
                    jogadores_usados.add(goleiros[1])

            # Preencher os dois primeiros times com jogadores de linha
            for i in range(2):
                while len(times[i]) < 6 and linha:
                    jogador = linha.pop(0)
                    if jogador not in jogadores_usados:
                        times[i].append(jogador)
                        jogadores_usados.add(jogador)

            # Jogadores restantes (linha + goleiros não distribuídos)
            restantes = [j for j in nomes_confirmados if j not in jogadores_usados]
            random.shuffle(restantes)

            for i in range(2, (len(restantes) // 5) + 3):
                novo_time = []
                while restantes and len(novo_time) < 5:
                    jogador = restantes.pop()
                    novo_time.append(jogador)
                if novo_time:
                    times.append(novo_time)

            st.session_state.times_sorteados = times

            cores = ["🟡", "🔵", "🟢", "🟣", "🟠", "🔴"]
            for i, time in enumerate(times, 1):
                cor = cores[(i - 1) % len(cores)]
                st.markdown(f"### {cor} Time {i}")
                for jogador in time:
                    st.markdown(f"- {jogador}")
                st.markdown("---")



        


    # Avaliação pós-jogo
    def tela_avaliacao_pos_jogo():
        if "dados_gsheets" not in st.session_state:
            st.session_state["dados_gsheets"] = load_data()

        partidas, jogadores, usuarios, presencas, avaliacao, mensalidades, transparencia = st.session_state["dados_gsheets"]

        if "Votante" not in avaliacao.columns or "DataRodada" not in avaliacao.columns:
            avaliacao = pd.DataFrame(columns=["Votante", "Craque", "Pereba", "Goleiro", "DataRodada"])

        agora = datetime.now()
        hoje = agora.weekday()
        dias_para_quinta = (3 - hoje) % 7
        proxima_quinta = agora + timedelta(days=dias_para_quinta)
        data_rodada = proxima_quinta.date()

        presencas["Presença"] = presencas["Presença"].fillna("").str.lower()
        presencas["DataPartida"] = pd.to_datetime(presencas["DataPartida"], errors="coerce").dt.date

        confirmados = presencas[(presencas["DataPartida"] == data_rodada) & (presencas["Presença"] == "sim")]
        jogadores_presentes = confirmados["Nome"].tolist()

        votante = st.session_state.get("nome", "usuário")

        if votante not in jogadores_presentes:
            st.warning("⚠️ Apenas jogadores que confirmaram presença na rodada podem votar.")
            return

        linha = [j for j in jogadores_presentes if usuarios.get(email := next((e for e, d in usuarios.items() if d["nome"] == j), None), {}).get("posicao", "linha").lower() != "goleiro"]
        goleiros = [j for j in jogadores_presentes if j not in linha]

        ja_votou = not avaliacao[(avaliacao["Votante"] == votante) & (avaliacao["DataRodada"] == str(data_rodada))].empty

        if ja_votou:
            st.success("✅ Você já votou nesta rodada.")

            df_votos_rodada = avaliacao[avaliacao["DataRodada"] == str(data_rodada)]

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
                        f"<div style='background-color: {podium_colors[i]}; padding: 10px 15px; border-radius: 8px; font-weight: bold; font-size: 18px; min-width: 100px; box-shadow: 2px 2px 5px #aaa; text-align: center;'>"
                        f"{podium_labels[i]}<br>{nomes}<br>{votos} voto(s)"
                        "</div></div>"
                    )

                podium_html += "</div>"
                return podium_html

            st.markdown(gerar_html_podio(df_votos_rodada["Craque"], "Craques da rodada (Top 3)", "🏆"), unsafe_allow_html=True)
            st.markdown(gerar_html_podio(df_votos_rodada["Pereba"], "Perebas da rodada (Top 3)", "🐢"), unsafe_allow_html=True)
            st.markdown(gerar_html_podio(df_votos_rodada["Goleiro"], "Goleiro da Rodada", "🧤"), unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

        else:
            st.markdown("<h5 style='font-weight: bold;'>😎 Tá na hora do veredito!</h5>", unsafe_allow_html=True)
            st.markdown("<p style='font-size:14px;'>Vote no <strong>craque</strong>, <strong>pereba</strong> e <strong>melhor goleiro</strong> da rodada</p>", unsafe_allow_html=True)

            craque = st.selectbox("⭐ Craque da rodada", options=["-- Selecione --"] + [p for p in linha if p != votante])
            pereba_opcoes = [j for j in linha if j != craque and j != votante]
            pereba = st.selectbox("🥴 Pereba da rodada", options=["-- Selecione --"] + pereba_opcoes)
            goleiro = st.selectbox("🧤 Melhor goleiro", options=["-- Selecione --"] + [g for g in goleiros if g != votante])

            if st.button("Votar"):
                if craque == "-- Selecione --" or pereba == "-- Selecione --" or goleiro == "-- Selecione --":
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
                    avaliacao = pd.concat([avaliacao, novo_voto], ignore_index=True)
                    save_data_gsheets(partidas, jogadores, usuarios, presencas, avaliacao, mensalidades, transparencia)
                    st.session_state["dados_gsheets"] = (partidas, jogadores, usuarios, presencas, avaliacao, mensalidades, transparencia)
                    st.success("✅ Voto registrado com sucesso!")
                    st.rerun()

        if st.session_state.get("email", "").lower() == "matheusmoreirabr@hotmail.com":
            with st.expander("⚠️ Apagar votos da rodada atual"):
                st.markdown("Esta ação irá remover **todos os votos registrados** para a rodada atual. Não poderá ser desfeita.")
                if st.button("🗑️ Apagar votos desta rodada"):
                    avaliacao = avaliacao[avaliacao["DataRodada"] != str(data_rodada)]
                    save_data_gsheets(partidas, jogadores, usuarios, presencas, avaliacao, mensalidades, transparencia)
                    st.session_state["dados_gsheets"] = (partidas, jogadores, usuarios, presencas, avaliacao, mensalidades, transparencia)
                    st.success("✅ Votos da rodada apagados com sucesso.")
                    if st.button("🔄 Recarregar página"):
                        st.rerun()







    # Midias
    def tela_galeria_momentos():
        st.markdown("<h3>📸 Galeria de Momentos da Chopp's League</h3>", unsafe_allow_html=True)

        st.markdown(
            "Veja os melhores registros da Chopp's League: gols, resenhas e lembranças 🍻⚽"
        )

        link_drive = "https://drive.google.com/drive/u/1/folders/1yNVXxZYnh_RN0eflXUL1U-QhUBpjTE2y"

        st.markdown(
            f"""
            <div style="text-align: center; margin-top: 2rem;">
                <a href="{link_drive}" target="_blank" style="
                    display: inline-block;
                    background-color: #4CAF50;
                    color: white;
                    padding: 12px 24px;
                    text-align: center;
                    text-decoration: none;
                    font-size: 16px;
                    border-radius: 8px;
                    font-weight: bold;
                    box-shadow: 2px 2px 6px rgba(0,0,0,0.2);
                ">
                    📂 Acessar Álbum no Google Drive
                </a>
            </div>
            """,
            unsafe_allow_html=True,
        )



    # Mensalidade
    def tela_pagamento_mensalidade():
        st.markdown("<h3>💰 Controle de Pagamento da Mensalidade</h3>", unsafe_allow_html=True)

        email_usuario = st.session_state.get("email", "").lower()
        usuarios_autorizados = ["matheusmoreirabr@hotmail.com", "lucasbotelho97@hotmail.com"]

        if email_usuario not in usuarios_autorizados:
            st.warning("⚠️ Você não tem permissão para acessar esta página.")
            return

        partidas, jogadores, usuarios, presencas, avaliacao, mensalidades, transparencia = st.session_state.get("dados_gsheets", load_data())

        hoje = datetime.now()
        meses = [f"{m:02d}/{hoje.year}" for m in range(1, 13)]
        mes_atual = f"{hoje.month:02d}/{hoje.year}"
        mes_selecionado = st.selectbox("📅 Mês de referência", options=meses, index=hoje.month - 1)

        st.markdown(f"<p><strong>Mês selecionado:</strong> {mes_selecionado}</p>", unsafe_allow_html=True)
        st.markdown("Marque os jogadores que realizaram o pagamento da mensalidade para o mês selecionado.")

        nomes_ordenados = sorted([(info.get("nome", ""), email) for email, info in usuarios.items()])

        pagamentos_registrados = []

        with st.form("form_pagamento"):
            for nome, email in nomes_ordenados:
                pagamentos = usuarios[email].get("pagamentos", {})
                pago = pagamentos.get(mes_selecionado, False)
                novo_status = st.checkbox(f"{nome} ({email})", value=pago, key=f"{email}_{mes_selecionado}")
                pagamentos[mes_selecionado] = novo_status
                usuarios[email]["pagamentos"] = pagamentos

                pagamentos_registrados.append({
                    "Nome": nome,
                    "Email": email,
                    "Mês": mes_selecionado,
                    "Pago": "Sim" if novo_status else "Não"
                })

            if st.form_submit_button("💾 Salvar Pagamentos"):
                # Carregar registros existentes da aba Mensalidades
                gc = autenticar_gsheets()
                sh = gc.open(NOME_PLANILHA)
                aba_mensalidades = sh.worksheet("Mensalidades")
                dados_existentes = get_as_dataframe(aba_mensalidades).dropna(how="all")

                # Remove registros do mês atual antes de adicionar os novos
                dados_filtrados = dados_existentes[dados_existentes["Mês"] != mes_selecionado]
                df_final = pd.concat([dados_filtrados, pd.DataFrame(pagamentos_registrados)], ignore_index=True)

                # Salvar no Google Sheets
                aba_mensalidades.clear()
                set_with_dataframe(aba_mensalidades, df_final)

                st.success("✅ Pagamentos atualizados com sucesso.")
                st.session_state["usuarios"] = usuarios
                st.session_state["dados_gsheets"] = (partidas, jogadores, usuarios, presencas, avaliacao, df_final, transparencia)


    def usuarios_to_df(usuarios):
        usuarios_df = pd.DataFrame.from_dict(usuarios, orient="index").reset_index()
        usuarios_df = usuarios_df.rename(columns={"index": "email"})
        return usuarios_df







    def tela_portal_transparencia():
        st.title("🏦 Portal da Transparência")

        # Corrige: define df logo após leitura dos dados
        def ler_dados():
            if "dados_gsheets" not in st.session_state:
                st.session_state["dados_gsheets"] = load_data()
            return st.session_state["dados_gsheets"][-1]  # retorna a aba 'Transparência'

        df = ler_dados()

        # Corrige erro de KeyError se colunas estiverem ausentes
        colunas_necessarias = ["Data", "Tipo", "Descrição", "Valor"]
        for coluna in colunas_necessarias:
            if coluna not in df.columns:
                df[coluna] = None

        # Conversão de datas
        if not df.empty:
            df["Data"] = pd.to_datetime(df["Data"], errors="coerce")

        st.markdown("### 💸 Entradas e Saídas")
        col1, col2 = st.columns(2)
        with col1:
            entradas = df[df["Tipo"] == "Entrada"]
            total_entradas = entradas["Valor"].sum()
            st.metric("Total Arrecadado", f"R$ {total_entradas:,.2f}")
        with col2:
            saidas = df[df["Tipo"] == "Saída"]
            total_saidas = saidas["Valor"].sum()
            st.metric("Total Gasto", f"R$ {total_saidas:,.2f}")

        saldo = total_entradas - total_saidas
        st.success(f"💰 **Saldo atual: R$ {saldo:,.2f}**")

        st.markdown("---")
        st.markdown("### 📜 Histórico Financeiro")
        email_usuario = st.session_state.get("email", "").lower()
        autorizados = ["matheusmoreirabr@hotmail.com", "lucasbotelho97@hotmail.com"]

        if df.empty:
            st.info("Nenhum registro financeiro até o momento.")
        else:
            df_exibicao = df.copy()
            if not pd.api.types.is_datetime64_any_dtype(df_exibicao["Data"]):
                df_exibicao["Data"] = pd.to_datetime(df_exibicao["Data"], errors="coerce")
            df_exibicao["Data"] = df_exibicao["Data"].dt.strftime("%d/%m/%Y")
            st.dataframe(df_exibicao.sort_values("Data", ascending=False), use_container_width=True)

            if email_usuario in autorizados:
                st.markdown("### ✏️ Editar ou Apagar Registros")
                # Remove registros com campos obrigatórios nulos
                df_validos = df[df["Descrição"].notna() & df["Data"].notna()]

                # Gera opções seguras
                opcoes = df_validos.index.astype(str) + " - " + df_validos["Descrição"] + " - " + df_validos["Data"].dt.strftime("%d/%m/%Y")
                escolha = st.selectbox("Selecione um registro:", ["-- Selecione --"] + list(opcoes))
                if escolha != "-- Selecione --":
                    idx = int(escolha.split(" - ")[0])
                    registro = df.loc[idx]

                    with st.form("editar_registro"):
                        tipo_edit = st.selectbox("Tipo", ["Entrada", "Saída"], index=["Entrada", "Saída"].index(registro["Tipo"]))
                        desc_edit = st.text_input("Descrição", value=registro["Descrição"])
                        valor_edit = st.number_input("Valor (R$)", min_value=0.0, value=registro["Valor"], step=0.01, format="%.2f")
                        data_edit = st.date_input("Data", value=pd.to_datetime(registro["Data"]))
                        col1, col2 = st.columns(2)
                        with col1:
                            atualizar = st.form_submit_button("💾 Atualizar")
                        with col2:
                            apagar = st.form_submit_button("🗑️ Apagar")

                        if atualizar:
                            df.at[idx, "Tipo"] = tipo_edit
                            df.at[idx, "Descrição"] = desc_edit
                            df.at[idx, "Valor"] = valor_edit
                            df.at[idx, "Data"] = data_edit
                            # Substitui a aba "Transparência" e salva tudo de novo
                            partidas, jogadores, usuarios, presencas, avaliacao, mensalidades, _ = st.session_state["dados_gsheets"]
                            st.session_state["dados_gsheets"] = (partidas, jogadores, usuarios, presencas, avaliacao, mensalidades, df)
                            save_data_gsheets(partidas, jogadores, usuarios, presencas, avaliacao, mensalidades, df)
                            st.success("✅ Registro atualizado com sucesso!")
                            st.rerun()

                        if apagar:
                            df = df.drop(index=idx).reset_index(drop=True)
                            # Substitui a aba "Transparência" e salva tudo de novo
                            partidas, jogadores, usuarios, presencas, avaliacao, mensalidades, _ = st.session_state["dados_gsheets"]
                            st.session_state["dados_gsheets"] = (partidas, jogadores, usuarios, presencas, avaliacao, mensalidades, df)
                            save_data_gsheets(partidas, jogadores, usuarios, presencas, avaliacao, mensalidades, df)
                            st.success("🗑️ Registro removido com sucesso!")
                            st.rerun()

        # Adicionar novo registro
        if email_usuario in autorizados:
            st.markdown("---")
            st.markdown("### ➕ Adicionar novo registro")
            with st.form("form_financeiro"):
                tipo = st.selectbox("Tipo", ["Entrada", "Saída"])
                descricao = st.text_input("Descrição")
                valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
                data = st.date_input("Data", value=datetime.now())
                submit = st.form_submit_button("💾 Registrar")

                if submit:
                    novo_registro = pd.DataFrame([{
                        "Data": pd.to_datetime(data),
                        "Tipo": tipo,
                        "Descrição": descricao,
                        "Valor": valor,
                        "Responsável": email_usuario
                    }])
                    df = pd.concat([df, novo_registro], ignore_index=True)
                    # Substitui a aba "Transparência" e salva tudo de novo
                    partidas, jogadores, usuarios, presencas, avaliacao, mensalidades, _ = st.session_state["dados_gsheets"]
                    st.session_state["dados_gsheets"] = (partidas, jogadores, usuarios, presencas, avaliacao, mensalidades, df)
                    save_data_gsheets(partidas, jogadores, usuarios, presencas, avaliacao, mensalidades, df)
                    st.success("✅ Registro adicionado com sucesso!")
                    st.rerun()
                    
        if email_usuario in autorizados:
            if st.button("🧹 Limpar registros inválidos"):
                df = df[df["Descrição"].notna() & df["Data"].notna()]
                # Substitui a aba "Transparência" e salva tudo de novo
                partidas, jogadores, usuarios, presencas, avaliacao, mensalidades, _ = st.session_state["dados_gsheets"]
                st.session_state["dados_gsheets"] = (partidas, jogadores, usuarios, presencas, avaliacao, mensalidades, df)
                save_data_gsheets(partidas, jogadores, usuarios, presencas, avaliacao, mensalidades, df)
                st.success("Registros inválidos removidos com sucesso!")
                st.rerun()






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
        st.title("📢 Comunicado à Gestão")

        nome = st.session_state.get("nome", "usuário")
        email = st.session_state.get("email", "não informado")

        st.markdown(
            f"""
            <p>Use o espaço abaixo para enviar um comunicado à organização. 
            Assim que você clicar em <strong>Enviar via WhatsApp</strong>, a mensagem será aberta no aplicativo do WhatsApp com seus dados preenchidos.</p>
        """,
            unsafe_allow_html=True,
        )

        with st.form("form_comunicado"):
            mensagem = st.text_area(
                "✉️ Sua mensagem",
                height=150,
                placeholder="Digite aqui sua sugestão, reclamação ou comunicado...",
            )
            enviar = st.form_submit_button("📤 Gerar link para WhatsApp")

        if enviar:
            if not mensagem.strip():
                st.warning("Digite uma mensagem antes de gerar o link para o WhatsApp.")
            else:
                numero_destino = "5531991159656"  # Brasil + DDD + número
                texto = f"""Olá, aqui é {nome}!

    Email: {email}

    📢 Comunicado:
    {mensagem}
    """
                texto_codificado = urllib.parse.quote(texto)
                link = f"https://wa.me/{numero_destino}?text={texto_codificado}"
                st.success("Clique no botão abaixo para abrir o WhatsApp com sua mensagem:")
                st.markdown(f"[📲 Enviar via WhatsApp]({link})", unsafe_allow_html=True)







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
        jogadores = tela_jogadores()
    elif st.session_state.pagina_atual == "🎲 Sorteio de Times":
        tela_sorteio()
    elif st.session_state.pagina_atual == "✅ Confirmar Presença/Ausência":
        tela_presenca_login()
    elif st.session_state.pagina_atual == "🏅 Avaliação Pós-Jogo":
        tela_avaliacao_pos_jogo()
    elif st.session_state.pagina_atual == "💰 Controle da Mensalidade":
        tela_pagamento_mensalidade()
    elif st.session_state.pagina_atual == "🏦 Portal da Transparência":
        tela_portal_transparencia()
    elif st.session_state.pagina_atual == "📸 Galeria de Momentos":
        tela_galeria_momentos()
    elif st.session_state.pagina_atual == "💬 Fórum":
        tela_forum()
    elif st.session_state.pagina_atual == "📣 Comunicado à Gestão":
        tela_comunicado()
    elif st.session_state.pagina_atual == "📜 Regras Chopp's League":
        tela_regras()
