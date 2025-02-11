import feedparser
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
from dotenv import load_dotenv

# Utilizzo del nuovo SDK di OpenAI
from openai import OpenAI

load_dotenv()  # Carica il file .env
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("La variabile OPENAI_API_KEY non è stata caricata correttamente.")

# Inizializza il client OpenAI. Se non specifichi la chiave, il client cercherà la variabile d'ambiente OPENAI_API_KEY.
client = OpenAI()

def fetch_relevant_articles(rss_url, keywords):
    """
    Recupera gli articoli dal feed RSS e restituisce quelli che contengono le parole chiave.
    """
    feed = feedparser.parse(rss_url)
    articles = []
    
    for entry in feed.entries:
        title = entry.title
        summary = entry.summary if hasattr(entry, "summary") else ""
        link = entry.link
        published = entry.published

        # Verifica che l'articolo menzioni almeno una delle parole chiave (nel titolo o nel sommario)
        if any(re.search(kw, title + summary, re.IGNORECASE) for kw in keywords):
            articles.append({
                "title": title,
                "summary": summary,
                "link": link,
                "published": published
            })
    
    return articles

def fetch_article_content(url):
    """
    Scarica la pagina dell'articolo e ne estrae il testo.
    Questa versione crea una sessione requests e imposta un cookie per simulare
    l'accettazione dei cookie.
    NOTA: Potrebbe essere necessario modificare il nome e il valore del cookie in base al sito.
    """
    try:
        session = requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ' +
                          'AppleWebKit/537.36 (KHTML, like Gecko) ' +
                          'Chrome/100.0.4896.75 Safari/537.36'
        }
        # Imposta il cookie che simula l'accettazione dei cookie.
        # Verifica con gli strumenti del browser il nome e il valore effettivi richiesti da ANSA.
        session.cookies.set('cookieconsent_status', 'dismiss')
        
        response = session.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            paragraphs = soup.find_all("p")
            article_body = "\n".join(p.get_text() for p in paragraphs)
            return article_body.strip()
        else:
            print(f"Status code {response.status_code} per {url}")
            return ""
    except Exception as e:
        print(f"Errore nel recupero della pagina {url}: {e}")
        return ""


def summarize_text_openai(text, max_tokens=150):
    """
    Sintetizza il testo utilizzando le API di OpenAI con il modello gpt-4o-mini tramite il nuovo SDK.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Sei un esperto di sintesi. Riassumi il testo fornito in modo chiaro, conciso e preciso."
                },
                {
                    "role": "user",
                    "content": f"Testo:\n{text}\n\nRiassunto:"
                }
            ],
            max_tokens=max_tokens,
            temperature=0.3
        )
        summary = response.choices[0].message.content
        return summary.strip()
    except Exception as e:
        print("Errore nella chiamata OpenAI:", e)
        return ""

def main():
    # URL del feed RSS di ANSA per la politica
    rss_url = "https://www.ansa.it/sito/notizie/politica/politica_rss.xml"
    # Parole chiave per filtrare gli articoli rilevanti
    keywords = ["Meloni"]
    
    print("Recupero articoli da ANSA...")
    articles = fetch_relevant_articles(rss_url, keywords)
    
    if not articles:
        print("Nessun articolo trovato con le parole chiave specificate.")
        return
    
    results = []
    for art in articles:
        print(f"\nProcessando: {art['title']}")
        # Recupera il testo completo dell'articolo
        full_text = fetch_article_content(art["link"])
        # Se il testo completo non è disponibile, usa il sommario del feed RSS
        if not full_text:
            full_text = art["summary"]
        
        # Limita il testo per evitare di superare i limiti di token (ad esempio, a 2000 caratteri)
        if len(full_text) > 10000:
            full_text = full_text[:10000]
        
        # Esegui la sintesi tramite le API di OpenAI
        summary_text = summarize_text_openai(full_text)
        results.append({
            "title": art["title"],
            "published": art["published"],
            "link": art["link"],
            "generated_summary": summary_text
        })
        
        # Attesa per evitare di incorrere in rate limit
        time.sleep(1)
    
    # Creazione del DataFrame e salvataggio in CSV
    df = pd.DataFrame(results)
    print("\nArticoli processati:")
    print(df)
    
    output_filename = "articoli_meloni_autonomia_openai_sdk.csv"
    df.to_csv(output_filename, index=False, encoding="utf-8")
    print(f"\nI risultati sono stati salvati in '{output_filename}'.")

if __name__ == "__main__":
    main()
