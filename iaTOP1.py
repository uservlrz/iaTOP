import re
import re
from pathlib import Path
import pickle
from unidecode import unidecode
import streamlit as st
from cryptography.fernet import Fernet
from pathlib import Path
import pickle
import streamlit as st
import openai
from unidecode import unidecode
import streamlit as st

CHAVE_CRIPTOGRAFIA = b'72WM3vHTYph_VyGjix1er6oCWTFZeAKM2u2ccZjAj6s='
CHAVE_API_CRIPTOGRAFADA = b'gAAAAABmEF9yxl_rg21p1-OoNdVHZxqiWoEsrZcLWR7uPqex10ximY5j65emibWHXskvNDVQHqk18VgCUKMeu5Jt-7_27TTTanB3c5OAE2BYdzgiNl5ItFzbnSk0I7ZJAUPEaTJlCBeZF82wl_UE2XN_l-X17PQNRA=='

cipher_suite = Fernet(CHAVE_CRIPTOGRAFIA)

PASTA_CONFIGERACOES = Path(__file__).parent / 'configuracoes'
PASTA_CONFIGERACOES.mkdir(exist_ok=True)
PASTA_MENSAGENS = Path(__file__).parent / 'mensagens'
PASTA_MENSAGENS.mkdir(exist_ok=True)
CACHE_DESCONVERTE = {}

def decodifica_chave_api():
    chave_api_decodificada = cipher_suite.decrypt(CHAVE_API_CRIPTOGRAFADA).decode()
    return chave_api_decodificada

def retorna_resposta_modelo(mensagens, modelo='gpt-3.5-turbo', temperatura=0):
    openai.api_key = decodifica_chave_api()  # Usando a chave decodificada aqui
    # Estrutura de mensagens para o modelo de chat
    chat_messages = [{"role": m['role'], "content": m['content']} for m in mensagens]

    response = openai.ChatCompletion.create(
        model=modelo,
        messages=chat_messages,
        temperature=temperatura
    )

    # Ajuste conforme a nova estrutura de resposta
    if response.choices and len(response.choices) > 0:
        return response.choices[0].message['content']
    else:
        return "Desculpe, não consegui processar sua resposta."


def converte_nome_mensagem(nome_mensagem):
    nome_arquivo = unidecode(nome_mensagem)
    nome_arquivo = re.sub(r'\W+', '', nome_arquivo).lower()
    return nome_arquivo

def desconverte_nome_mensagem(nome_arquivo):
    if not nome_arquivo in CACHE_DESCONVERTE:
        nome_mensagem = ler_mensagem_por_nome_arquivo(nome_arquivo, key='nome_mensagem')
        CACHE_DESCONVERTE[nome_arquivo] = nome_mensagem
    return CACHE_DESCONVERTE[nome_arquivo]

def retorna_nome_da_mensagem(mensagens):
    nome_mensagem = ''
    for mensagem in mensagens:
        if mensagem['role'] == 'user':
            nome_mensagem = mensagem['content'][:30]
            break
    return nome_mensagem

def salvar_mensagens(mensagens):
    if len(mensagens) == 0:
        return False
    nome_mensagem = retorna_nome_da_mensagem(mensagens)
    nome_arquivo = converte_nome_mensagem(nome_mensagem)
    arquivo_salvar = {'nome_mensagem': nome_mensagem,
                      'nome_arquivo': nome_arquivo,
                      'mensagem': mensagens}
    with open(PASTA_MENSAGENS / nome_arquivo, 'wb') as f:
        pickle.dump(arquivo_salvar, f)

def ler_mensagem_por_nome_arquivo(nome_arquivo, key='mensagem'):
    with open(PASTA_MENSAGENS / nome_arquivo, 'rb') as f:
        mensagens = pickle.load(f)
    return mensagens[key]

def ler_mensagens(mensagens, key='mensagem'):
    if len(mensagens) == 0:
        return []
    nome_mensagem = retorna_nome_da_mensagem(mensagens)
    nome_arquivo = converte_nome_mensagem(nome_mensagem)
    with open(PASTA_MENSAGENS / nome_arquivo, 'rb') as f:
        mensagens = pickle.load(f)
    return mensagens[key]

def listar_conversas():
    conversas = list(PASTA_MENSAGENS.glob('*'))
    conversas = sorted(conversas, key=lambda item: item.stat().st_mtime_ns, reverse=True)
    return [c.stem for c in conversas]

# SALVAMENTO E LEITURA DA APIKEY ========================
# PÁGINAS ==================================================

def inicializacao():
    if 'mensagens' not in st.session_state:
        st.session_state['mensagens'] = []
    if 'conversa_atual' not in st.session_state:
        st.session_state['conversa_atual'] = ''
    if 'modelo' not in st.session_state:
        st.session_state['modelo'] = 'gpt-3.5-turbo'

def pagina_principal():
    mensagens = ler_mensagens(st.session_state['mensagens'])
    st.header('Chat gpTOP', divider=True)

    for mensagem in mensagens:
        chat = st.chat_message(mensagem['role'])
        chat.markdown(mensagem['content'])
    
    prompt = st.chat_input('Fale com o chat')
    if prompt:
        nova_mensagem = {'role': 'user', 'content': prompt}
        chat = st.chat_message(nova_mensagem['role'])
        chat.markdown(nova_mensagem['content'])
        mensagens.append(nova_mensagem)

        resposta_completa = retorna_resposta_modelo(mensagens, modelo=st.session_state['modelo'])
        chat = st.chat_message('assistant')
        chat.markdown(resposta_completa)
        
        nova_mensagem = {'role': 'assistant', 'content': resposta_completa}
        mensagens.append(nova_mensagem)

        st.session_state['mensagens'] = mensagens
        salvar_mensagens(mensagens)


def tab_conversas(tab):

    tab.button('➕ Nova conversa',
                on_click=seleciona_conversa,
                args=('', ),
                use_container_width=True)
    tab.markdown('')
    conversas = listar_conversas()
    for nome_arquivo in conversas:
        nome_mensagem = desconverte_nome_mensagem(nome_arquivo).capitalize()
        if len(nome_mensagem) == 30:
            nome_mensagem += '...'
        tab.button(nome_mensagem,
            on_click=seleciona_conversa,
            args=(nome_arquivo, ),
            disabled=nome_arquivo==st.session_state['conversa_atual'],
            use_container_width=True)

def seleciona_conversa(nome_arquivo):
    if nome_arquivo == '':
        st.session_state['mensagens'] = []
    else:
        mensagem = ler_mensagem_por_nome_arquivo(nome_arquivo)
        st.session_state['mensagens'] = mensagem
    st.session_state['conversa_atual'] = nome_arquivo

def tab_configuracoes(tab):
    modelo_escolhido = tab.selectbox('Selecione o modelo',
                                     ['gpt-3.5-turbo', 'gpt-4'])
    st.session_state['modelo'] = modelo_escolhido


def main():
    inicializacao()
    pagina_principal()
    tab1, tab2 = st.sidebar.tabs(['Conversas', 'Configurações'])
    tab_conversas(tab1)
    tab_configuracoes(tab2)



if __name__ == '__main__':
    main()