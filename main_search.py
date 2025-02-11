import http.client
import json
import urllib.parse  # Importiamo urllib per codificare l'URL

# Parametri di ricerca
QUERY = "Giorgia Meloni"  # Termini di ricerca
COUNTRY = "IT"  # Italia
LANGUAGE = "it"  # Italiano
LIMIT = 10  # Numero massimo di articoli da ottenere
TIME_PUBLISHED = "anytime"  # Nessun limite temporale

# Codifichiamo la query per evitare problemi con spazi e caratteri speciali
QUERY_ENCODED = urllib.parse.quote(QUERY)

# Configura la connessione all'API RapidAPI
conn = http.client.HTTPSConnection("real-time-news-data.p.rapidapi.com")

headers = {
    'x-rapidapi-key': "1ac68e958emsh472c7a5ef3b8eb1p19e189jsn5e6523bb2aa8",  # Sostituisci con la tua API Key
    'x-rapidapi-host': "real-time-news-data.p.rapidapi.com"
}

# Costruiamo la richiesta API con la query codificata
endpoint = f"/search?query={QUERY_ENCODED}&limit={LIMIT}&time_published={TIME_PUBLISHED}&country={COUNTRY}&lang={LANGUAGE}"

# Debug: Stampiamo l'URL effettivo della richiesta
print(f"🔍 URL della richiesta API: {endpoint}")

# Facciamo la richiesta HTTP
conn.request("GET", endpoint, headers=headers)

# Otteniamo la risposta
res = conn.getresponse()

# Debug: Stampiamo il codice di stato HTTP
print(f"🔍 HTTP Status Code: {res.status}")

# Leggiamo la risposta API
data = res.read()

# Debug: Stampiamo il JSON grezzo ricevuto dall'API
print("\n📜 JSON grezzo ricevuto:")
print(data.decode("utf-8"))  # Stampa la risposta completa dall'API

# Proviamo a decodificare i dati JSON
try:
    articles_response = json.loads(data)
except json.JSONDecodeError as e:
    print("\n❌ Errore nel parsing JSON:", e)
    exit(1)

# Controlliamo se ci sono articoli disponibili (usando 'data' invece di 'articles')
if "data" in articles_response and articles_response["data"]:
    print(f"\n✅ Trovati {len(articles_response['data'])} articoli su '{QUERY}':\n")
    
    for article in articles_response["data"]:
        print(f"📰 Titolo: {article['title']}")
        print(f"📌 Fonte: {article['source_name']}")
        print(f"📅 Data: {article['published_datetime_utc']}")
        print(f"🔗 URL: {article['link']}\n")
else:
    print("\n❌ Nessun articolo trovato.")
