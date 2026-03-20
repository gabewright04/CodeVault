// ============ MODAL ============
function openModal() {
    document.getElementById('modalOverlay').classList.add('active');
}

function closeModal() {
    document.getElementById('modalOverlay').classList.remove('active');
    resetModal();
}

function resetModal() {
    document.getElementById('selectedFile').style.display = 'none';
    document.getElementById('selectedFileName').textContent = '';
    document.getElementById('notesInput').value = '';
    document.getElementById('uploadStatus').textContent = '';
    document.getElementById('uploadStatus').className = 'upload-status';
    document.getElementById('fileInput').value = '';
    selectedFile = null;
}

// ============ FILE SELECTION ============
let selectedFile = null;

function handleFileSelect(input) {
    if (input.files && input.files[0]) {
        selectedFile = input.files[0];
        document.getElementById('selectedFileName').textContent = selectedFile.name;
        document.getElementById('selectedFile').style.display = 'flex';
    }
}

// Drag and drop
const dropZone = document.getElementById('dropZone');

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
    const file = e.dataTransfer.files[0];
    if (file) {
        selectedFile = file;
        document.getElementById('selectedFileName').textContent = file.name;
        document.getElementById('selectedFile').style.display = 'flex';
    }
});

// ============ UPLOAD ============
async function uploadFile() {
    if (!selectedFile) {
        showStatus('Please select a file first.', true);
        return;
    }

    const btn = document.getElementById('submitBtn');
    btn.disabled = true;
    btn.textContent = 'Importing...';
    showStatus('⚡ Generating AI overview...');

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('notes', document.getElementById('notesInput').value);

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            showStatus('✓ ' + data.message);
            btn.textContent = 'Done!';
            setTimeout(() => {
                closeModal();
                window.location.reload();
            }, 1000);
        } else {
            showStatus(data.error || 'Upload failed.', true);
            btn.disabled = false;
            btn.textContent = 'Import to Vault';
        }
    } catch (err) {
        showStatus('Something went wrong. Try again.', true);
        btn.disabled = false;
        btn.textContent = 'Import to Vault';
    }
}

function showStatus(msg, isError = false) {
    const el = document.getElementById('uploadStatus');
    el.textContent = msg;
    el.className = 'upload-status' + (isError ? ' error' : '');
}

// ============ DELETE ============
async function deleteFile(fileId, btn) {
    if (!confirm('Delete this file from the vault?')) return;

    const card = btn.closest('.file-card');
    card.style.transition = 'opacity 0.3s, transform 0.3s';
    card.style.opacity = '0';
    card.style.transform = 'scale(0.95)';

    await fetch(`/file/${fileId}/delete`, { method: 'POST' });

    setTimeout(() => {
        card.remove();
    }, 300);
}

// ============ KEYBOARD ============
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeModal();
});