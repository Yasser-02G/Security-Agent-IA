async function fetchLogs() {
    try {
        const response = await fetch('/api/logs');
        const logs = await response.json();
        const tableBody = document.getElementById('log-body');
        
        tableBody.innerHTML = ''; // Nettoyer le tableau

        logs.forEach(log => {
            const row = document.createElement('tr');
            const statusClass = log.status === 'CRITICAL' ? 'status-blocked' : 'status-ok';
            
            row.innerHTML = `
                <td>${log.timestamp}</td>
                <td>${log.source}</td>
                <td>${log.event}</td>
                <td class="${statusClass}">${log.status}</td>
                <td>${log.action}</td>
                <td>${log.reason}</td>
            `;
            tableBody.appendChild(row);
        });
    } catch (e) {
        console.error("Erreur logs:", e);
    }
}


async function sendMessage() {
    const input = document.getElementById('user-input');
    const chatBox = document.getElementById('chat-box');
    const message = input.value.trim();

    if (!message) return;

    // 1. Message Utilisateur
    chatBox.innerHTML += `
        <div class="message user">
            <div class="avatar">👤</div>
            <div class="bubble">${message}</div>
        </div>
    `;
    input.value = '';
    chatBox.scrollTop = chatBox.scrollHeight;

    // 2. Message d'attente IA
    const loadingId = "loading-" + Date.now();
    chatBox.innerHTML += `
        <div class="message ai" id="${loadingId}">
            <div class="avatar">🤖</div>
            <div class="bubble">Analyse des logs en cours...</div>
        </div>
    `;

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({message: message})
        });
        const data = await response.json();

        // 3. Remplacer par la vraie réponse
        document.getElementById(loadingId).querySelector('.bubble').innerText = data.response;
    } catch (e) {
        document.getElementById(loadingId).querySelector('.bubble').innerText = "Erreur de connexion à l'IA.";
    }
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Actualisation automatique toutes les 3 secondes
setInterval(fetchLogs, 3000);
fetchLogs();

// Touche Entrée pour le chat
document.getElementById('user-input')?.addEventListener('keypress', function (e) {
    if (e.key === 'Enter') sendMessage();
});