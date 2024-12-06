document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const uploadForm = document.getElementById('upload-form');
    const uploadButton = document.getElementById('upload-button');
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress');
    const resultContainer = document.getElementById('result-container');
    const downloadLink = document.getElementById('download-link');

    // File Drop Zone handlers
    dropZone.addEventListener('click', () => fileInput.click());
    
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            handleFileSelect();
        }
    });

    fileInput.addEventListener('change', handleFileSelect);

    function handleFileSelect() {
        const file = fileInput.files[0];
        if (file && file.type === 'application/pdf') {
            uploadButton.disabled = false;
        } else {
            uploadButton.disabled = true;
            alert('Please select a PDF file');
        }
    }

    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        try {
            progressContainer.style.display = 'block';
            uploadButton.disabled = true;

            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                progressBar.style.width = '100%';
                resultContainer.style.display = 'block';
                downloadLink.href = `/download/${data.output_file}`;
            } else {
                throw new Error(data.error || 'Upload failed');
            }
        } catch (error) {
            alert('Error: ' + error.message);
        } finally {
            progressContainer.style.display = 'none';
            uploadButton.disabled = false;
        }
    });
});