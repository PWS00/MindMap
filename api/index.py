# File: api/index.py

# Importiamo le librerie necessarie per il server web, la gestione dei file,
# l'AI di Google e la chiamata al servizio di rendering delle immagini.
import os
import fitz  # PyMuPDF
import google.generativeai as genai
from flask import Flask, request, Response, jsonify
import time
import requests # Per chiamare l'API di Kroki.io

# --- 1. Setup dell'applicazione Flask ---
# Questa è la base della nostra web app.
app = Flask(__name__)

# --- 2. Configurazione sicura della Chiave API ---
# Sostituisce la logica dei "Segreti" di Colab.
try:
    # os.getenv() è il modo standard per leggere le Variabili d'Ambiente su un server.
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
    else:
        # Questo messaggio apparirà nei log di Vercel se la chiave non è impostata.
        print("ATTENZIONE: La variabile d'ambiente GOOGLE_API_KEY non è stata trovata.")
except Exception as e:
    print(f"Errore durante la configurazione della chiave API: {e}")

# --- 3. Le Tue Funzioni Logiche (Adattate per il Web) ---

def estrai_testo_da_pdf(pdf_stream) -> str:
    """
    Estrae il testo da un flusso di dati PDF ricevuto da un upload web.
    Non usa più un percorso di file locale.
    """
    try:
        # fitz.open() può leggere direttamente i dati binari del file.
        with fitz.open(stream=pdf_stream, filetype="pdf") as doc:
            testo = "".join(page.get_text() for page in doc)
        return testo
    except Exception as e:
        print(f"Errore durante l'estrazione del testo dal PDF: {e}")
        return ""

def crea_codice_mermaid(testo_input: str, modello: str = "gemini-1.5-flash") -> str:
    """
    Analizza il testo e genera il codice Mermaid.
    Questa funzione è quasi identica a quella di Colab.
    """
    if not genai.api_key:
        return "graph TD\n  A[Errore Configurazione] --> B(La chiave API di Google non è configurata sul server.)"
    
    model = genai.GenerativeModel(modello)
    prompt = f"""
Crea una mappa concettuale di RIEPILOGO e ad alto livello. La mappa deve essere chiara e contenere solo i concetti più importanti, ignorando i dettagli minuti.

Istruzioni:
1.  Identifica i **5-7 macro-argomenti** principali del testo. Questi saranno i concetti di primo livello.
2.  Per ogni macro-argomento, estrai solo i **3-5 concetti secondari più cruciali**.
3.  Ignora completamente i dettagli specifici, le liste lunghe di esempi, le singole funzioni o le proprietà minori. L'obiettivo è la chiarezza, non la completezza.
4.  Organizza la mappa con `graph TD` e usa `subgraph` per raggruppare i macro-argomenti.
5.  Usa forme di nodo diverse per distinguere le categorie di informazioni seguendo la corretta sintassi Mermaid. Ad esempio:
    - Nodi rettangolari `[ ]` per i concetti principali.
    - Nodi a forma di stadio `([ ])` per gli eventi.
    - Nodi a rombo `{{ }}` per le decisioni.
    - Nodi circolari `(( ))` per i risultati.

    Regola Fondamentale per il Testo dei Nodi: Per evitare errori di sintassi, il testo di un nodo NON DEVE contenere caratteri speciali come `()` o '||' o '&&' o `{{}} ecc. MA SOLO LETTERE E NUMERI`.
    - ❌ **Esempio SBAGLIATO:** `A[Nodo con [parentesi]]`
    - ❌ **Esempio SBAGLIATO:** `A[Nodo con (parentesi)]`
    - ❌ **Esempio SBAGLIATO:** `A[Caratteri speciali!! & ||]`
    - ✅ **Esempio CORRETTO:** `A[Parole o numeri]`

6.  Collega i nodi con frecce etichettate per descrivere la natura della relazione (es. `-->|causa|`, `-->|include|`).
7.  **Output richiesto**: Restituisci SOLO ed UNICAMENTE il blocco di codice Mermaid che rispetti la sintassi. L'output deve iniziare con `graph TD` e terminare con l'ultima riga di sintassi Mermaid.

Testo da analizzare:
    ---
    {testo_input}
    ---
    """
    try:
        response = model.generate_content(prompt)
        codice_mermaid = response.text.replace("```mermaid", "").replace("```", "").strip()
        return codice_mermaid
    except Exception as e:
        return f"graph TD\n  A[Errore API] --> B(Si è verificato un problema: {e})"

def genera_png_da_mermaid(codice_mermaid: str, tema: str = 'forest') -> bytes:
    """
    Genera un'immagine PNG dal codice Mermaid usando l'API di Kroki.io.
    Questa funzione replica la logica della tua funzione 'creare_mappa_mermaid'.
    """
    print("Avvio generazione PNG tramite Kroki.io...")
    url_kroki = "https://kroki.io/mermaid/png"
    payload = {
        "diagram_source": codice_mermaid,
        "diagram_options": {"theme": tema}
    }
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(url_kroki, headers=headers, json=payload, timeout=30) # Aggiunto timeout
        response.raise_for_status()  # Lancia un'eccezione per errori HTTP
        print("Immagine PNG ricevuta con successo da Kroki.")
        return response.content  # Restituisce i dati binari dell'immagine
    except requests.exceptions.RequestException as e:
        print(f"Errore durante la chiamata a Kroki.io: {e}")
        # Se Kroki restituisce un errore, potremmo provare a mostrarlo
        if e.response is not None:
            print(f"Dettaglio errore da Kroki: {e.response.text}")
        raise  # Rilanciamo l'eccezione per farla gestire dalla route principale

# --- 4. La "Route" Principale dell'API ---
# Questo è l'indirizzo web (endpoint) che il nostro front-end chiamerà.
@app.route("/api/generate", methods=["POST"])
def handle_map_generation():
    # Controlla se un file è stato inviato nella richiesta
    if 'file' not in request.files:
        return jsonify({"error": "Nessun file fornito."}), 400

    pdf_file = request.files['file']
    if pdf_file.filename == '':
        return jsonify({"error": "File non selezionato."}), 400

    try:
        # Eseguiamo l'intero flusso
        testo_estratto = estrai_testo_da_pdf(pdf_file.read())
        if not testo_estratto:
            return jsonify({"error": "Impossibile estrarre il testo dal PDF."}), 500

        # Logica di tentativi multipli per la generazione del codice
        codice_mermaid_risultante = None
        for i in range(3): # 3 tentativi
            codice_temp = crea_codice_mermaid(testo_estratto)
            if "Errore" not in codice_temp and codice_temp.strip().startswith("graph TD"):
                codice_mermaid_risultante = codice_temp
                break
            time.sleep(1) # Piccola pausa tra i tentativi

        if not codice_mermaid_risultante:
            return jsonify({"error": "Il modello AI non è riuscito a generare un codice valido."}), 500

        # Generazione dell'immagine PNG
        png_image_bytes = genera_png_da_mermaid(codice_mermaid_risultante)

        # Restituisce l'immagine PNG come risposta
        return Response(png_image_bytes, mimetype='image/png')

    except Exception as e:
        print(f"Errore critico durante il processo: {e}")
        return jsonify({"error": "Si è verificato un errore imprevisto sul server."}), 500