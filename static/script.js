// Questo codice gestisce la logica del front-end
document.addEventListener('DOMContentLoaded', () => {
    // Inizializza la libreria Mermaid.js, ma le dice di non avviarsi subito
    mermaid.initialize({ startOnLoad: false });

    // Seleziona gli elementi HTML con cui interagiremo
    const uploadInput = document.getElementById('pdf-upload');
    const uploadButton = document.getElementById('upload-button');
    const generateButton = document.getElementById('generate-button');
    const fileNameDisplay = document.getElementById('file-name');
    const resultContainer = document.getElementById('result-container');
    const uploadSection = document.querySelector('.upload-section');

    let selectedFile = null; // Variabile per memorizzare il file scelto dall'utente

    // --- Gestione dell'Upload (Click e Drag & Drop) ---

    // Quando si clicca il bottone, si attiva l'input nascosto
    uploadButton.addEventListener('click', () => {
        uploadInput.click();
    });

    // Quando un file viene scelto tramite la finestra di dialogo
    uploadInput.addEventListener('change', () => {
        if (uploadInput.files.length > 0) {
            handleFile(uploadInput.files[0]);
        }
    });

    // Gestione del trascinamento del file sull'area di upload
    uploadSection.addEventListener('dragover', (e) => {
        e.preventDefault(); // Necessario per permettere il 'drop'
        uploadSection.classList.add('dragover');
    });

    uploadSection.addEventListener('dragleave', () => {
        uploadSection.classList.remove('dragover');
    });

    uploadSection.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadSection.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleFile(e.dataTransfer.files[0]);
        }
    });

    // Funzione unica per gestire il file, sia da click che da drop
    function handleFile(file) {
        if (file && file.type === 'application/pdf') {
            selectedFile = file;
            fileNameDisplay.textContent = `File selezionato: ${file.name}`;
            generateButton.disabled = false; // Abilita il bottone "Genera Mappa"
        } else {
            alert('Per favore, seleziona un file in formato PDF.');
        }
    }

    // --- Gestione della Generazione della Mappa ---

    generateButton.addEventListener('click', async () => {
        if (!selectedFile) {
            alert('Nessun file PDF selezionato.');
            return;
        }

        showLoading(); // Mostra l'animazione di caricamento

        const formData = new FormData();
        formData.append('file', selectedFile);

        try {
            // Chiama la nostra API Python
            const response = await fetch('/api/generate', {
                method: 'POST',
                body: formData,
            });

            const data = await response.json(); // Ora ci aspettiamo una risposta JSON

            if (response.ok) {
                // Se la risposta è positiva, passiamo il codice Mermaid alla funzione di rendering
                await displayMermaidDiagram(data.mermaid_code);
            } else {
                // Altrimenti, mostriamo l'errore restituito dal server
                displayError(data.error || 'Si è verificato un errore sconosciuto.');
            }
        } catch (error) {
            displayError('Errore di connessione con il server.');
            console.error('Errore:', error);
        }
    });

    // --- Funzioni di Utilità per l'Interfaccia ---

    function showLoading() {
        resultContainer.innerHTML = '<div class="loader"></div>';
    }

    // QUESTA È LA FUNZIONE CHIAVE AGGIORNATA
    async function displayMermaidDiagram(mermaidCode) {
        try {
            // Usiamo l'API di Mermaid.js per renderizzare il codice di testo in un'immagine SVG
            const { svg } = await mermaid.render('graphDiv', mermaidCode);
            
            // Inseriamo l'SVG generato direttamente nel nostro contenitore dei risultati
            resultContainer.innerHTML = svg;
        } catch (error) {
            console.error("Errore durante il rendering di Mermaid:", error);
            displayError("Errore nella sintassi del diagramma generato. Il modello AI potrebbe aver restituito un codice non valido. Riprova.");
        }
    }

    function displayError(message) {
        resultContainer.innerHTML = `<div class="error-message">${message}</div>`;
    }
});
