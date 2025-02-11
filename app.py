import streamlit as st
import http.client
import json
import urllib.parse
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# ========================================
# CONFIGURAZIONE API KEY
# ========================================
RAPIDAPI_KEY = "1ac68e958emsh472c7a5ef3b8eb1p19e189jsn5e6523bb2aa8"
OPENAI_API_KEY="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"

# ========================================
# FUNZIONE PER OTTENERE GLI ARTICOLI TOP
# ========================================
def get_top_articles():
    TOPIC_ID = "CAAqJAgKIh5DQkFTRUFvS0wyMHZNR1JzYkRaeFpoSUNhWFFvQUFQAQ"  # Topic di Giorgia Meloni
    COUNTRY = "IT"
    LANGUAGE = "it"
    LIMIT = 10

    conn = http.client.HTTPSConnection("real-time-news-data.p.rapidapi.com")
    headers = {
        'x-rapidapi-key': RAPIDAPI_KEY,
        'x-rapidapi-host': "real-time-news-data.p.rapidapi.com"
    }
    endpoint = f"/topic-headlines?topic={TOPIC_ID}&limit={LIMIT}&country={COUNTRY}&lang={LANGUAGE}"
    st.write(f"🔍 Richiesta articoli: {endpoint}")
    
    try:
        conn.request("GET", endpoint, headers=headers)
        res = conn.getresponse()
        st.write("🔍 HTTP Status Code (articoli):", res.status)
        data = res.read()
        st.write("🔍 Raw data (articoli):", data.decode("utf-8"))
        articles_response = json.loads(data.decode("utf-8"))
    except Exception as e:
        st.error(f"Errore nella richiesta articoli: {e}")
        return []
    
    if "data" in articles_response and articles_response["data"]:
        return articles_response["data"]
    else:
        st.error("Nessun articolo trovato.")
        return []

# ========================================
# FUNZIONE PER ESTRARRE IL CONTENUTO DELL'ARTICOLO
# ========================================
def extract_article_content(url):
    """
    Utilizza l'host lexper.p.rapidapi.com per estrarre il contenuto.
    Viene aggiunto del codice di debug per controllare la risposta.
    """
    conn = http.client.HTTPSConnection("lexper.p.rapidapi.com")
    headers = {
        'x-rapidapi-key': RAPIDAPI_KEY,
        'x-rapidapi-host': "lexper.p.rapidapi.com"
    }
    # Percent-encode l'URL in ingresso
    encoded_url = urllib.parse.quote(url, safe='')
    endpoint = f"/v1.1/extract?url={encoded_url}&js=true&js_timeout=30&media=true"
    st.write(f"🔍 Endpoint utilizzato per l'estrazione: {endpoint}")
    
    try:
        conn.request("GET", endpoint, headers=headers)
    except Exception as e:
        st.error(f"Errore durante la richiesta all'API di estrazione: {e}")
        return None
    
    try:
        res = conn.getresponse()
        st.write("🔍 HTTP Status Code (estrazione):", res.status)
    except Exception as e:
        st.error(f"Errore ottenendo la risposta dall'API di estrazione: {e}")
        return None
    
    try:
        raw_data = res.read()
        decoded_data = raw_data.decode("utf-8")
        st.write("🔍 Raw data (estrazione):", decoded_data)
    except Exception as e:
        st.error(f"Errore nella lettura dei dati grezzi: {e}")
        return None

    try:
        content_response = json.loads(decoded_data)
        st.write("🔍 JSON decodificato (estrazione):", content_response)
    except Exception as e:
        st.error(f"Errore nel parsing della risposta JSON: {e}")
        return None

    return content_response

# ========================================
# FUNZIONE PER RIASSUMERE IL TESTO CON LLM (LANGCHAIN)
# ========================================
def summarize_text(text):
    try:
        llm = OpenAI(temperature=0)
    except Exception as e:
        st.error(f"Errore nell'inizializzare l'LLM: {e}")
        return "Impossibile generare il riassunto."
    
    prompt_template = (
        "Riassumi il seguente testo in italiano, evidenziando le posizioni principali "
        "espresse riguardo Giorgia Meloni:\n\n{text}\n\nRiassunto:"
    )
    prompt = PromptTemplate(template=prompt_template, input_variables=["text"])
    chain = LLMChain(llm=llm, prompt=prompt)
    
    try:
        summary = chain.run(text=text)
    except Exception as e:
        st.error(f"Errore nella generazione del riassunto: {e}")
        summary = "Impossibile generare il riassunto."
    return summary

# ========================================
# GESTIONE DELLO STATO CON st.session_state
# ========================================
if 'articles' not in st.session_state:
    st.session_state.articles = None
if 'selected_article' not in st.session_state:
    st.session_state.selected_article = None
if 'summary' not in st.session_state:
    st.session_state.summary = None

# ========================================
# INTERFACCIA UTENTE CON STREAMLIT
# ========================================
st.title("Demo: Monitoraggio Posizioni del Presidente del Consiglio")
st.markdown(
    """
Questa demo mostra alcuni articoli riguardanti **Giorgia Meloni**.
Selezionando un articolo, verrà estratto il suo contenuto e generato un riassunto.
    """
)

# Pulsante per caricare gli articoli
if st.button("Carica Articoli"):
    with st.spinner("Recupero articoli..."):
        st.session_state.articles = get_top_articles()

if st.session_state.articles:
    titles = [article["title"] for article in st.session_state.articles]
    selected_title = st.selectbox("Seleziona un articolo", titles, key="selectbox_title")
    st.session_state.selected_article = next(
        (a for a in st.session_state.articles if a["title"] == selected_title), None
    )
    if st.session_state.selected_article:
        st.subheader("Dettagli Articolo")
        st.markdown(f"**Titolo:** {st.session_state.selected_article['title']}")
        st.markdown(f"**Fonte:** {st.session_state.selected_article['source_name']}")
        st.markdown(f"**Data:** {st.session_state.selected_article['published_datetime_utc']}")
        st.markdown(f"**URL:** [Leggi l'articolo]({st.session_state.selected_article['link']})")

        if st.button("Estrai Contenuto e Genera Riassunto"):
            with st.spinner("Estrazione contenuto in corso..."):
                content_response = extract_article_content(st.session_state.selected_article["link"])
            if content_response:
                # Debug: Visualizza l'intera risposta JSON
                st.write("🔍 Risposta completa dall'API di estrazione:", content_response)
                
                # Prova a prelevare il testo estratto dalla risposta JSON.
                # Se il JSON ha la chiave "article", estrai il testo da lì.
                article_text = ""
                if "article" in content_response:
                    article_text = content_response["article"].get("text", "")
                    st.write("🔍 Testo estratto da content_response['article']['text']:", article_text)
                else:
                    article_text = content_response.get("text") or content_response.get("content", "")
                    st.write("🔍 Testo estratto dai livelli top-level:", article_text)
                
                if article_text:
                    st.subheader("Contenuto Estratto")
                    st.write(article_text)
                    with st.spinner("Generazione riassunto in corso..."):
                        st.session_state.summary = summarize_text(article_text)
                    st.subheader("Riassunto")
                    st.write(st.session_state.summary)
                else:
                    st.error("Contenuto non disponibile o formato non riconosciuto.")
            else:
                st.error("Errore nell'estrazione del contenuto dell'articolo.")
