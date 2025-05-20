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





# Config da página
st.set_page_config(page_title="Chopp's League", page_icon="🍻")

# Sessões iniciais
if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = False
if "usuarios" not in st.session_state:
    st.session_state.usuarios = {}
if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = "login"

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
    st.title("🔐 Acesso ao Sistema")
    aba = st.radio("Escolha uma opção:", ["Login", "Cadastro"], key="aba_login")

    if aba == "Login":
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

    else:
        with st.form("form_cadastro"):
            nome = st.text_input("Nome completo", key="cad_nome")
            posicao = st.selectbox("Posição que joga", ["", "Linha", "Goleiro"], key="cad_pos")
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

# --- SIDEBAR ---
with st.sidebar:
    st.image("./imagens/logo.png", caption="Chopp's League", use_container_width=True)
    st.markdown(f"👤 Logado como: **{st.session_state.nome}**")

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
    with st.sidebar:
        if "confirmar_logout" not in st.session_state:
            st.session_state.confirmar_logout = False

    if not st.session_state.confirmar_logout:
        # Botão vermelho centralizado
        col1, col2, col3 = st.sidebar.columns([1, 2, 1])
        with col2:
            if st.button("🚪 Logout", key="botao_logout"):
                st.session_state.confirmar_logout = True
    else:
        st.sidebar.warning("Tem certeza que deseja sair?")
        
    cols = st.sidebar.columns(2)  # Cria duas colunas do mesmo tamanho

    with cols[0]:
        if st.button("❌ Cancelar", key="cancelar_logout", use_container_width=True):
            st.session_state.confirmar_logout = False

    with cols[1]:
        if st.button("✅ Confirmar", key="confirmar_logout_btn", use_container_width=True):
            # Guarda dados essenciais antes de limpar sessão
            usuarios = st.session_state.get("usuarios", {})

            # Limpa a sessão com segurança
            st.session_state.clear()
            st.session_state.usuario_logado = False
            st.session_state.usuarios = usuarios
            st.session_state.pagina_atual = "login"
            st.experimental_rerun()

    st.markdown("---")

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

# Exibe as páginas conforme tipo
if pag == "🏠 Tela Principal":
    tela_principal()
elif pag == "📊 Registrar Partida" and st.session_state.tipo_usuario == "admin":
    partidas = registrar_partidas(partidas)
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
elif pag == "📜 Regras Choppe's League":
    tela_regras()
elif pag == "🚪 Sair":
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.experimental_rerun()





# Música ambiente (apenas se logado)
if st.session_state.usuario_logado:
    def tocar_musica_sidebar():
        caminho_musica = "audio/musica.mp3"
        if os.path.exists(caminho_musica):
            with open(caminho_musica, "rb") as f:
                audio_bytes = f.read()
            audio_base64 = base64.b64encode(audio_bytes).decode()
            st.sidebar.markdown(f"""
                <p style='text-align: center; font-weight: bold;'>🎵 Música Ambiente</p>
                <audio controls style="width: 100%;">
                    <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                    Seu navegador não suporta áudio.
                </audio>
            """, unsafe_allow_html=True)
        else:
            st.sidebar.warning("🔇 Música não encontrada.")

    tocar_musica_sidebar()




# Lista de administradores
ADMINS = ["teste"]





# Arquivos CSV
FILE_PARTIDAS = "partidas.csv"
FILE_JOGADORES = "jogadores.csv"





def init_data():
    if not os.path.exists(FILE_PARTIDAS):
        df = pd.DataFrame(columns=[
            "Data", "Número da Partida",
            "Placar Borussia", "Gols Borussia", "Assistências Borussia",
            "Placar Inter", "Gols Inter", "Assistências Inter"
        ])
        df.to_csv(FILE_PARTIDAS, index=False)

    if not os.path.exists(FILE_JOGADORES):
        df = pd.DataFrame(columns=["Nome", "Time", "Gols", "Assistências", "Faltas", "Cartões Amarelos", "Cartões Vermelhos"])
        df.to_csv(FILE_JOGADORES, index=False)

def load_data():
    partidas = pd.read_csv(FILE_PARTIDAS)
    jogadores = pd.read_csv(FILE_JOGADORES)
    return partidas, jogadores

def save_data(partidas, jogadores):
    partidas.to_csv(FILE_PARTIDAS, index=False)
    jogadores.to_csv(FILE_JOGADORES, index=False)





# Carrega dados com segurança
def load_data_safe():
    try:
        partidas = pd.read_csv(FILE_PARTIDAS)
    except:
        partidas = pd.DataFrame(columns=[
            "Data", "Número da Partida",
            "Placar Borussia", "Gols Borussia", "Assistências Borussia",
            "Placar Inter", "Gols Inter", "Assistências Inter"
        ])
    try:
        jogadores = pd.read_csv(FILE_JOGADORES)
    except:
        jogadores = pd.DataFrame(columns=["Nome", "Time", "Gols", "Assistências", "Faltas", "Cartões Amarelos", "Cartões Vermelhos"])
    return partidas, jogadores

partidas, jogadores = load_data_safe()





# Tela Principal
def tela_principal(partidas, jogadores):
    st.markdown("<h2 style='font-weight: bold;'>Bem-vindo à Choppe's League!</h2>", unsafe_allow_html=True)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        if os.path.exists("./imagens/borussia.png"):
            st.image("./imagens/borussia.png", caption="Borussia", use_container_width=True)
        else:
            st.warning("Imagem do Borussia não encontrada.")
    
    with col2:
        if os.path.exists("./imagens/inter.png"):
            st.image("./imagens/inter.png", caption="Inter", use_container_width=True)
        else:
            st.warning("Imagem da Inter não encontrada.")

    st.header("Resumo das Partidas")
    st.write(f"Total de partidas registradas: {len(partidas)}")

    if not partidas.empty:
        st.write("Última partida registrada:")
        st.write(partidas.tail(1))





# Tela de registro das partidas
def registrar_partidas(partidas):
    st.title("Registrar Estatísticas da Partida")

    jogadores_originais = st.session_state.get("jogadores_presentes", [
        "Matheus Moreira", "José Moreira", "Lucas", "Alex", "Gustavo",
        "Lula", "Juninho", "Jesus", "Gabriel", "Arthur"
    ])
    
    numero_partida = len(partidas) + 1
    data = st.date_input("Data da partida")
    st.markdown(f"**Número da Partida:** {numero_partida}")

    # Escudos
    col_a, col_b, col_c = st.columns([3, 1, 3])

    with col_a:
        st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
        if os.path.exists("./imagens/borussia.png"):
            st.image("./imagens/borussia.png", use_container_width=True)
        else:
            st.warning("Imagem do Borussia não encontrada.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_b:
        st.markdown("<div style='text-align:center; margin-top: 50px; font-size: 48px;'>✖</div>", unsafe_allow_html=True)

    with col_c:
        st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
        if os.path.exists("./imagens/inter.png"):
            st.image("./imagens/inter.png", use_container_width=True)
        else:
            st.warning("Imagem da Inter não encontrada.")
        st.markdown("</div>", unsafe_allow_html=True)

    # Seções de input
    col1, col2 = st.columns(2)

    with col1:
        lista_borussia = ["Ninguém marcou"] + jogadores_originais * 2
        gols_borussia = st.multiselect("Goleadores (Borussia)", lista_borussia, key="gols_borussia")
        placar_borussia = 0 if "Ninguém marcou" in gols_borussia else len(gols_borussia)
        st.markdown(f"<div style='text-align:center; font-size: 28px; font-weight:bold;'>{placar_borussia} gol(s)</div>", unsafe_allow_html=True)

        if "Ninguém marcou" in gols_borussia and len(gols_borussia) > 1:
            st.warning("Você não pode selecionar jogadores junto com 'Ninguém marcou'")
            gols_borussia = ["Ninguém marcou"]
            st.session_state["gols_borussia"] = ["Ninguém marcou"]

        assist_borussia = []
        if placar_borussia > 0 and "Ninguém marcou" not in gols_borussia:
            max_assists = 2 if placar_borussia > 1 else 1
            assist_borussia = st.multiselect(
                f"Garçons Borussia (máx {max_assists})",
                [j for j in jogadores_originais if j not in gols_borussia],
                max_selections=max_assists,
                key="assist_borussia"
            )

    with col2:
        jogadores_indisponiveis = set(gols_borussia + assist_borussia)
        lista_inter = ["Ninguém marcou"] + [j for j in jogadores_originais if j not in jogadores_indisponiveis] * 2
        gols_inter = st.multiselect("Goleadores (Inter)", lista_inter, key="gols_inter")
        placar_inter = 0 if "Ninguém marcou" in gols_inter else len(gols_inter)
        st.markdown(f"<div style='text-align:center; font-size: 28px; font-weight:bold;'>{placar_inter} gol(s)</div>", unsafe_allow_html=True)

        if "Ninguém marcou" in gols_inter and len(gols_inter) > 1:
            st.warning("Você não pode selecionar jogadores junto com 'Ninguém marcou'")
            gols_inter = ["Ninguém marcou"]
            st.session_state["gols_inter"] = ["Ninguém marcou"]

        assist_inter = []
        if placar_inter > 0 and "Ninguém marcou" not in gols_inter:
            max_assists = 2 if placar_inter > 1 else 1
            assist_inter = st.multiselect(
                f"Garçons Inter (máx {max_assists})",
                [j for j in jogadores_originais if j not in gols_inter],
                max_selections=max_assists,
                key="assist_inter"
            )

    # Registro final
    if st.button("Registrar"):
        nova = {
            "Data": data,
            "Número da Partida": numero_partida,
            "Placar Borussia": placar_borussia,
            "Gols Borussia": ", ".join(gols_borussia),
            "Assistências Borussia": ", ".join(assist_borussia),
            "Placar Inter": placar_inter,
            "Gols Inter": ", ".join(gols_inter),
            "Assistências Inter": ", ".join(assist_inter)
        }
        partidas = pd.concat([partidas, pd.DataFrame([nova])], ignore_index=True)
        partidas.to_csv("partidas.csv", index=False)
        st.success("✅ Partida registrada com sucesso!")

    st.markdown("---")
    st.subheader("📋 Histórico de Partidas Registradas:")
    st.dataframe(partidas)

    return partidas





# Estatisticas dos jogadores
def tela_jogadores(jogadores):
    st.title("Registrar Estatísticas dos Jogadores")
    jogadores_lista = [
        "Matheus Moreira", "José Moreira", "Lucas", "Alex", "Gustavo",
        "Lula", "Juninho", "Jesus", "Gabriel", "Arthur",
        "Walter", "Eduardo", "Cristian", "Luciano", "Deivid"
    ]
    times = ["Borussia", "Time 2"]
    with st.form("form_jogadores", clear_on_submit=True):
        nome = st.selectbox("Jogador", jogadores_lista)
        time = st.selectbox("Time", times)
        gols = st.number_input("Gols", min_value=0, step=1)
        assistencias = st.number_input("Assistências", min_value=0, step=1)
        faltas = st.number_input("Faltas", min_value=0, step=1)
        cart_amarelos = st.number_input("Cartões Amarelos", min_value=0, step=1)
        cart_vermelhos = st.number_input("Cartões Vermelhos", min_value=0, step=1)
        submit = st.form_submit_button("Registrar")

        if submit:
            registro = {
                "Nome": nome,
                "Time": time,
                "Gols": gols,
                "Assistências": assistencias,
                "Faltas": faltas,
                "Cartões Amarelos": cart_amarelos,
                "Cartões Vermelhos": cart_vermelhos
            }
            jogadores = jogadores.append(registro, ignore_index=True)
            jogadores.to_csv(FILE_JOGADORES, index=False)
            st.success("Estatísticas registradas com sucesso!")

    st.dataframe(jogadores)
    return jogadores




# Tela de sorteio
def tela_sorteio():
    st.title("🎲 Sorteio de Times")
    st.markdown("⚠️ Em breve...")




# Tela de confirmação de presença/ausência
def tela_presenca_login():
    st.title("✅ Confirmação de Presença")
    nome = st.session_state.get("nome", "usuário")

    # Define o prazo de quarta-feira às 22h
    agora = datetime.now()
    hoje = agora.weekday()  # segunda = 0 ... domingo = 6
    dias_para_quarta = (2 - hoje) % 7
    proxima_quarta = agora + timedelta(days=dias_para_quarta)
    prazo_limite = proxima_quarta.replace(hour=22, minute=0, second=0, microsecond=0)

    passou_do_prazo = agora > prazo_limite
    resposta_enviada = "presenca_confirmada" in st.session_state

    if passou_do_prazo:
        st.warning("⚠️ O prazo para confirmar presença ou ausência é toda **quarta-feira até às 22h**.")
        if resposta_enviada:
            status = st.session_state["presenca_confirmada"]
            if status == "sim":
                st.info(f"{nome}, você **confirmou presença** para esta semana. ✅")
            else:
                motivo = st.session_state.get("motivo", "não informado")
                st.info(f"{nome}, você **informou ausência** com o motivo: **{motivo}** ❌")
        else:
            st.info("Você não informou sua presença ou ausência esta semana.")
        return

    # Se o jogador já respondeu, mostrar mensagem + botão para mudar de ideia
    if resposta_enviada:
        if st.session_state["presenca_confirmada"] == "sim":
            st.success(f"{nome}, sua **presença** foi confirmada com sucesso! ✅")
        else:
            motivo = st.session_state.get("motivo", "não informado")
            st.success(f"{nome}, sua **ausência** foi registrada com o motivo: **{motivo}** ❌")
        
        if st.button("🔁 Mudar de ideia"):
            for key in ["presenca_confirmada", "motivo"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.experimental_rerun()
        return  # <-- ESSENCIAL para evitar o erro


    # Exibe opções caso não tenha respondido ou clicado em "mudar de ideia"
    presenca = st.radio("Você vai comparecer?", ["✅ Sim", "❌ Não"], horizontal=True)

    motivo = ""
    motivo_outros = ""

    if presenca == "❌ Não":
        motivo = st.selectbox("Qual o motivo da ausência?", [
            "Saúde", "Trabalho", "Compromisso acadêmico", "Viagem", "Problemas pessoais", "Lesão", "Outros"
        ])
        if motivo == "Outros":
            motivo_outros = st.text_area("Descreva o motivo")

    if st.button("Enviar resposta"):
        if presenca == "❌ Não" and motivo == "Outros" and not motivo_outros.strip():
            st.warning("Descreva o motivo da ausência.")
        else:
            if presenca == "✅ Sim":
                st.session_state["presenca_confirmada"] = "sim"
            else:
                st.session_state["presenca_confirmada"] = "nao"
                st.session_state["motivo"] = motivo_outros.strip() if motivo == "Outros" else motivo
            st.experimental_rerun()





#Tela da avaliação pós-jogo
def tela_avaliacao_pos_jogo():
    FILE_VOTOS = "votacao.csv"

    if not os.path.exists(FILE_VOTOS):
        df_votos = pd.DataFrame(columns=["Votante", "Craque", "Pereba"])
        df_votos.to_csv(FILE_VOTOS, index=False)

    df_votos = pd.read_csv(FILE_VOTOS)

    jogadores_presentes = st.session_state.get("jogadores_presentes", [
        "Matheus Moreira", "José Moreira", "Lucas", "Alex", "Gustavo",
        "Lula", "Juninho", "Jesus", "Gabriel", "Arthur"
    ])

    st.title("🏅 Avaliação Pós-Jogo")

    votante = st.session_state.get("nome", "usuário")
    jogadores_para_voto = [j for j in jogadores_presentes if j != votante]
    ja_votou = votante in df_votos["Votante"].values

    if not ja_votou:
        st.markdown(f"Olá, **{votante}**! Escolha os destaques da partida:")
        with st.form("votacao_form"):
            craque = st.selectbox("Craque da Choppe's League ⭐", jogadores_para_voto, placeholder="Selecione")
            pereba = st.selectbox("Pereba da Choppe's League 🥴", jogadores_para_voto, placeholder="Selecione")
            submit = st.form_submit_button("Votar")

            if submit:
                if craque == pereba:
                    st.error("O craque e o pereba não podem ser a mesma pessoa.")
                else:
                    novo_voto = pd.DataFrame([{
                        "Votante": votante,
                        "Craque": craque,
                        "Pereba": pereba
                    }])
                    df_votos = pd.concat([df_votos, novo_voto], ignore_index=True)
                    df_votos.to_csv(FILE_VOTOS, index=False)
                    st.success("✅ Voto registrado com sucesso!")
                    ja_votou = True

    if ja_votou and not df_votos.empty:
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
                    f"<div style='"
                    f"background-color: {podium_colors[i]};"
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

        st.markdown(gerar_html_podio(df_votos["Craque"], "Craque da Choppe's League (Top 3)", "🏆"), unsafe_allow_html=True)
        st.markdown(gerar_html_podio(df_votos["Pereba"], "Pereba da Choppe's League (Top 3)", "🐢"), unsafe_allow_html=True)





# Midias
def tela_galeria_momentos():
    st.title("📸 Galeria de Momentos da Chopp's League")

    st.markdown("Veja os melhores registros da Choppe's League: gols, resenhas e lembranças 🍻⚽")

    # --- TÓPICOS DA GALERIA ---
    topicos = {
        "🏖️ Confraternizações": "midia/confraternizacoes",
        "🔥 Jogadas Bonitas": "midia/jogadas_bonitas",
        "😂 Lances Engraçados": "midia/lances_engracados",
        "🥅 Gols Incríveis": "midia/gols_incriveis",
        "🎉 Bastidores & Zoações": "midia/bastidores"
    }

    for titulo, pasta in topicos.items():
        st.markdown(f"### {titulo}")

        if not os.path.exists(pasta):
            st.info("Nenhum conteúdo disponível ainda.")
            continue

        arquivos = sorted(os.listdir(pasta))
        imagens = [a for a in arquivos if a.lower().endswith(('.png', '.jpg', '.jpeg'))]
        videos = [a for a in arquivos if a.lower().endswith(('.mp4', '.mov', '.webm'))]

        col1, col2 = st.columns(2)

        with col1:
            for img in imagens:
                st.image(os.path.join(pasta, img), caption=img, use_container_width=True)

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
        mensagem = st.text_area("Mensagem", placeholder="Digite seu comentário aqui...", max_chars=500, label_visibility="collapsed")
        enviar = st.form_submit_button("Enviar")

        if enviar:
            if mensagem.strip() == "":
                st.warning("O comentário não pode estar vazio.")
            else:
                novo = pd.DataFrame([{
                    "Autor": nome,
                    "Mensagem": mensagem.strip(),
                    "DataHora": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }])
                df_forum = pd.concat([df_forum, novo], ignore_index=True)
                df_forum.to_csv(FILE_FORUM, index=False)
                st.success("Comentário publicado!")

    # --- Exibe comentários existentes (mais recentes primeiro) ---
    st.markdown("### 🗂 Comentários recentes")

    if df_forum.empty:
        st.info("Ainda não há comentários. Seja o primeiro a escrever! 🤙")
    else:
        # Ordena por data decrescente
        df_forum["DataHora"] = pd.to_datetime(df_forum["DataHora"])
        df_forum = df_forum.sort_values(by="DataHora", ascending=False)

        for _, row in df_forum.iterrows():
            st.markdown(f"""
            <div style='border:1px solid #ddd; border-radius:8px; padding:10px; margin-bottom:10px; background-color: #f9f9f9;'>
                <strong>{row['Autor']}</strong> <span style='color:gray; font-size:12px;'>({row['DataHora'].strftime('%d/%m/%Y %H:%M')})</span>
                <div style='margin-top:5px;'>{row['Mensagem']}</div>
            </div>
            """, unsafe_allow_html=True)





# Tela de mensagem a gestão
def tela_comunicado():
    st.title("📣 Comunicado à Gestão")

    nome = st.session_state.get("nome", "usuário")
    telefone = st.session_state.get("telefone", "não informado")
    email = st.session_state.get("email", "não informado")

    st.markdown(f"""
        <p>Use o espaço abaixo para enviar um comunicado à organização. 
        Assim que você clicar em <strong>Enviar via WhatsApp</strong>, a mensagem será aberta no aplicativo do WhatsApp com seus dados preenchidos.</p>
    """, unsafe_allow_html=True)

    mensagem = st.text_area("✉️ Sua mensagem", height=150, placeholder="Digite aqui sua sugestão, reclamação ou comunicado...")

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
            st.success("Clique no botão abaixo para abrir o WhatsApp com sua mensagem:")
            st.markdown(f"[📲 Abrir WhatsApp]({link})", unsafe_allow_html=True)





# Tela das Regras
def tela_regras():
    st.markdown("<h1 style='font-size:32px;'>📜 Regras Oficiais – Chopp's League</h1>", unsafe_allow_html=True)

    def subtitulo(txt):
        st.markdown(f'<h3 style="font-size:20px; margin-top: 1em;">{txt}</h3>', unsafe_allow_html=True)

    subtitulo("✅ 1. Confirmação de Presença")
    st.markdown("""
    - Os jogadores devem confirmar presença **até as 22h de quarta-feira**.
    - Quem não confirmar no prazo **não poderá jogar**.
    """)

    subtitulo("⌛ 2. Tempo de Jogo e Rodízio")
    st.markdown("""
    - Cada partida terá duração de **7 minutos ou até 2 gols**, o que ocorrer primeiro.
    - O **time que entra joga pelo empate**:
        - Se empatar, o **time vencedor da partida anterior sai**.
        - Se perder, o **time que entrou sai normalmente**.
    """)

    subtitulo("👕 3. Uniforme Obrigatório")
    st.markdown("""
    - É obrigatório comparecer com o uniforme padrão completo:
        - Camisa do **Borussia Dortmund**
        - Camisa da **Inter de Milão**
        - **Calção preto**
        - **Meião preto**
    - Jogadores sem o uniforme completo **não poderão jogar**.
    """)

    subtitulo("💰 4. Mensalidade e Pagamento")
    st.markdown("""
    - A mensalidade deve ser paga **até o dia 10 de cada mês**.
    - **Jogadores inadimplentes não poderão jogar até quitar sua dívida**.
    - **Goleiros são isentos da mensalidade**, mas devem pagar **o uniforme**.
    """)

    subtitulo("💸 5. Contribuição para o Caixa")
    st.markdown("""
    - Todos os jogadores, incluindo goleiros, devem contribuir com **R$20,00 adicionais**.
    - O valor será utilizado exclusivamente para:
        - **Materiais esportivos** (bolas, bomba de encher bola, etc.)
        - **Itens médicos** (Gelol, faixa, esparadrapo, gelo, etc.)
        - **Água**
        - **Confraternizações** ou outras necessidades da Choppe's League
    """)

    subtitulo("📅 6. Comprometimento")
    st.markdown("""
    - Ao confirmar presença, o jogador assume o compromisso de comparecer.
    - **Faltas não justificadas** podem resultar em **suspensão da próxima rodada**.
    """)

    subtitulo("⚠️ 7. Comportamento")
    st.markdown("""
    - Discussões, brigas ou qualquer tipo de agressividade resultam em **suspensão automática da próxima rodada**.
    - Em caso de reincidência, o jogador poderá ser **banido temporariamente ou definitivamente**, conforme decisão da gestão.
    """)

    subtitulo("🧤 8. Goleiros e Rodízio")
    st.markdown("""
    - Na ausência de goleiro fixo, haverá **rodízio entre os jogadores de linha** para cobrir o gol.
    """)

    subtitulo("🔐 9. Responsabilidade")
    st.markdown("""
    - Comprometimento com **pagamentos, presença e respeito** é essencial para manter a organização.
    - **Quem não estiver em dia com os compromissos não joga.**
    """)

    subtitulo("⭐ 10. Avaliação Pós-Jogo: Péreba e Craque")
    st.markdown("""
    - Após cada partida, será feita uma votação divertida para eleger:
        - **Péreba**: jogador com a pior performance da rodada.
        - **Craque**: jogador com a melhor performance.
    - A votação é **exclusiva para quem confirmou presença e jogou na partida do dia**.
    - Somente jogadores presentes poderão votar.
    - A finalidade é **uma brincadeira para animar o grupo e fortalecer o espírito da Choppe's League**.
    - Os resultados serão divulgados para descontração na tela **'Avaliação pós-jogo'**.
    """)






# Inicialização de sessão
if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = "🏠 Tela Principal"

if "nome" not in st.session_state:
    st.session_state.nome = "usuário"

# Dados fictícios para partidas
if "partidas" not in st.session_state:
    st.session_state.partidas = pd.DataFrame(columns=[
        "Data", "Número da Partida",
        "Placar Borussia", "Gols Borussia", "Assistências Borussia",
        "Placar Inter", "Gols Inter", "Assistências Inter"
    ])

partidas = st.session_state.partidas





# Roteador de páginas
if st.session_state.pagina_atual == "🏠 Tela Principal":
    tela_principal(partidas, jogadores)
elif st.session_state.pagina_atual == "📊 Registrar Partida":
    partidas = registrar_partidas(partidas)
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
elif st.session_state.pagina_atual == "📜 Regras Choppe's League":
    tela_regras()