document.addEventListener('DOMContentLoaded', () => {
    // Seleziona gli elementi principali dell'interfaccia
    const uploadInput = document.getElementById('pdf-upload');
    const uploadButton = document.getElementById('upload-button');
    const generateButton = document.getElementById('generate-button');
    const fileNameDisplay = document.getElementById('file-name');
    const resultContainer = document.getElementById('result-container');
    const uploadSection = document.querySelector('.upload-section');

    let selectedFile = null;

    // --- Gestione dell'Upload ---

    // Apre la finestra di dialogo per la selezione del file
    uploadButton.addEventListener('click', () => {
        uploadInput.click();
    });

    // Gestisce il file selezionato dall'utente
    uploadInput.addEventListener('change', () => {
        if (uploadInput.files.length > 0) {
            handleFile(uploadInput.files[0]);
        }
    });

    // --- Gestione del Drag & Drop ---
    uploadSection.addEventListener('dragover', (e) => {
        e.preventDefault(); // Impedisce il comportamento di default del browser
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

    function handleFile(file) {
        if (file && file.type === 'application/pdf') {
            selectedFile = file;
            fileNameDisplay.textContent = `File selezionato: ${file.name}`;
            generateButton.disabled = false; // Abilita il bottone di generazione
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

        // Mostra un indicatore di caricamento
        showLoading();

        // Crea un oggetto FormData per inviare il file
        const formData = new FormData();
        formData.append('file', selectedFile);

        try {
            // Effettua la chiamata POST all'API del nostro back-end
            const response = await fetch('/api/generate', {
                method: 'POST',
                body: formData,
            });

            if (response.ok) {
                // Se la risposta è OK, ci aspettiamo un'immagine
                const imageBlob = await response.blob();
                const imageUrl = URL.createObjectURL(imageBlob);
                displayImage(imageUrl);
            } else {
                // Se c'è un errore, ci aspettiamo un JSON con il messaggio
                const errorData = await response.json();
                displayError(errorData.error || 'Si è verificato un errore sconosciuto.');
            }
        } catch (error) {
            // Gestisce errori di rete o altri problemi
            displayError('Errore di connessione con il server.');
            console.error('Errore:', error);
        }
    });

    // --- Funzioni di Utilità per l'Interfaccia ---

    function showLoading() {
        resultContainer.innerHTML = '<div class="loader"></div>';
    }

    function displayImage(url) {
        resultContainer.innerHTML = `<img src="${url}" alt="Mappa concettuale generata">`;
    }

    function displayError(message) {
        resultContainer.innerHTML = `<div class="error-message">${message}</div>`;
    }
});