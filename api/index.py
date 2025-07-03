# File: api/index.py

import os
import fitz
import google.generativeai as genai
from flask import Flask, request, jsonify
import time

app = Flask(__name__)

# --- 1. Lettura sicura della Chiave API ---
# Leggiamo la chiave API una sola volta all'avvio.
api_key = os.getenv("GOOGLE_API_KEY")

# --- 2. Configurazione dell'API di Google ---
# Configuriamo l'API solo se la chiave è stata trovata.
if api_key:
    try:
        genai.configure(api_key=api_key)
        print("Chiave API di Google configurata con successo.")
    except Exception as e:
        print(f"Errore durante la configurazione dell'API Key: {e}")
        api_key = None # Se la configurazione fallisce, annulliamo la chiave.
else:
    print("ATTENZIONE: La variabile d'ambiente GOOGLE_API_KEY non è stata trovata.")

# --- Funzioni Logiche ---

def estrai_testo_da_pdf(pdf_stream):
    try:
        with fitz.open(stream=pdf_stream, filetype="pdf") as doc:
            return "".join(page.get_text() for page in doc)
    except Exception as e:
        print(f"Errore estrazione testo: {e}")
        return ""

def crea_codice_mermaid(testo_input: str):
    # --- NUOVO CONTROLLO ---
    # Ora controlliamo se la nostra variabile 'api_key' è valida.
    if not api_key:
        return "graph TD\n  A[Errore di Configurazione] --> B(La chiave API di Google non è impostata correttamente sul server.)"
    
    model = genai.GenerativeModel("gemini-1.5-flash")
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
        print(f"Errore durante la chiamata a Gemini: {e}")
        return f"graph TD\n  A[Errore API] --> B(Si è verificato un problema con l'AI: {e})"

# --- API Route (invariata) ---
@app.route("/api/generate", methods=["POST"])
def handle_map_generation():
    if 'file' not in request.files:
        return jsonify({"error": "Nessun file fornito."}), 400

    pdf_file = request.files['file']
    if pdf_file.filename == '':
        return jsonify({"error": "File non selezionato."}), 400

    try:
        testo_estratto = estrai_testo_da_pdf(pdf_file.read())
        if not testo_estratto:
            return jsonify({"error": "Impossibile estrarre testo dal PDF."}), 500

        # Logica di tentativi
        codice_mermaid_risultante = None
        for i in range(3):
            codice_temp = crea_codice_mermaid(testo_estratto)
            if "Errore" not in codice_temp and codice_temp.strip().startswith("graph TD"):
                codice_mermaid_risultante = codice_temp
                break
            time.sleep(1)

        if codice_mermaid_risultante:
            return jsonify({"mermaid_code": codice_mermaid_risultante})
        else:
            return jsonify({"error": "Il modello AI non è riuscito a generare un codice valido."}), 500

    except Exception as e:
        print(f"Errore critico: {e}")
        return jsonify({"error": "Errore imprevisto sul server."}), 500
