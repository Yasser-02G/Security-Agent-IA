// Initialisation des variables globales
let threatChart;
const ctx = document.getElementById('threatChart').getContext('2d');

// Configuration initiale du Graphique (Chart.js)
function initChart() {
    threatChart = new Chart(ctx, {
        type: 'bar', // On passe en mode barres
        data: {
            labels: [],
            datasets: [{
                label: 'Intensité du trafic',
                data: [],
                backgroundColor: [], // Sera rempli dynamiquement (Vert ou Rouge)
                borderColor: 'rgba(255, 255, 255, 0.1)',
                borderWidth: 1,
                borderRadius: 4, // Pour un look plus moderne
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#8b9db3' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#8b9db3' }
                }
            },
            plugins: {
                legend: { display: false } // On utilise notre propre légende HTML
            }
        }
    });
}

// Fonction pour mettre à jour toutes les données du dashboard
function updateDashboardData() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            updateGraph(data.logs);
            updateBlockedIPs(data.blocked_ips);
            updateEmails(data.emails);
        })
        .catch(err => console.error("Erreur update:", err));
}

// 1. Mise à jour de la fonction updateGraph pour inclure les IPs
function updateGraph(logs) {
    const labels = logs.map(log => log.time);
    const scores = logs.map(log => log.score);
    const ips = logs.map(log => log.ip); // On récupère les IPs des logs

    const colors = scores.map(score => {
        return score >= 80 ? '#ff0055' : '#00ff9d';
    });

    threatChart.data.labels = labels;
    threatChart.data.datasets[0].data = scores;
    threatChart.data.datasets[0].backgroundColor = colors;
    
    // NOUVEAU : On stocke les IPs dans une propriété personnalisée du dataset
    threatChart.data.datasets[0].clientIPs = ips; 
    
    threatChart.update('none'); 
}

// 2. Mise à jour de initChart pour configurer l'infobulle (Tooltip)
function initChart() {
    threatChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Intensité du trafic',
                data: [],
                backgroundColor: [],
                borderColor: 'rgba(255, 255, 255, 0.1)',
                borderWidth: 1,
                borderRadius: 4,
                barThickness: 12,
                maxBarThickness: 20,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true, max: 100, grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#8b9db3' } },
                x: { grid: { display: false }, ticks: { color: '#8b9db3' } }
            },
            plugins: {
                legend: { display: false },
                // --- CONFIGURATION DE L'INFOBULLE ---
                tooltip: {
                    backgroundColor: 'rgba(5, 10, 16, 0.9)', // Fond sombre pour coller au thème
                    titleFont: { size: 14, weight: 'bold' },
                    bodyFont: { size: 13, family: 'monospace' },
                    padding: 10,
                    borderColor: 'rgba(58, 134, 255, 0.3)',
                    borderWidth: 1,
                    displayColors: false, // Enlever le petit carré de couleur par défaut
                    callbacks: {
                        // On personnalise le texte après l'intensité
                        afterLabel: function(context) {
                            const index = context.dataIndex;
                            const ip = context.dataset.clientIPs[index]; // On récupère l'IP stockée
                            return `🌐 IP Client: ${ip}`;
                        },
                        label: function(context) {
                            return `📊 Intensité: ${context.parsed.y}%`;
                        }
                    }
                }
            }
        }
    });
}

// Mise à jour de la liste des IPs Bloquées
function updateBlockedIPs(ips) {
    const list = document.getElementById('blocked-list');
    list.innerHTML = '';
    if (ips.length === 0) {
        list.innerHTML = '<li>Aucune menace active.</li>';
        return;
    }
    ips.forEach(ip => {
        const li = document.createElement('li');
        li.innerHTML = `
            <span>💉 ${ip}</span>
            <button class="unblock-btn" onclick="unblockIP('${ip}')">DÉBLOQUER</button>
        `;
        list.appendChild(li);
    });
}

// Fonction pour débloquer une IP
function unblockIP(ip) {
    fetch('/api/unblock', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ip: ip })
    }).then(res => {
        updateDashboardData(); // Rafraîchir immédiatement
        addBotMessage(`Commande exécutée : IP ${ip} retirée de la liste noire.`);
    });
}

// Mise à jour de la liste des Emails
function updateEmails(emails) {
    const list = document.getElementById('email-list');
    list.innerHTML = '';
    if (emails.length === 0) {
        list.innerHTML = '<li>Aucun rapport récent.</li>';
        return;
    }
    // On affiche du plus récent au plus ancien
    emails.slice().reverse().forEach(email => {
        const li = document.createElement('li');
        li.innerHTML = `
            <span class="email-date">${email.date}</span>
            <span class="email-subject">Dujet: ${email.subject}</span>
        `;
        list.appendChild(li);
    });
}

// --- LOGIQUE DU CHATBOT ---
function sendMessage() {
    const input = document.getElementById('user-input');
    const message = input.value.trim();
    if (message === "") return;

    // Ajouter le message utilisateur
    const chatBox = document.getElementById('chat-box');
    chatBox.innerHTML += `<div class="user-message">${message}</div>`;
    input.value = '';
    chatBox.scrollTop = chatBox.scrollHeight;

    // Appel API
    fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: message })
    })
    .then(response => response.json())
    .then(data => {
        addBotMessage(data.response);
    });
}

function addBotMessage(text) {
    const chatBox = document.getElementById('chat-box');
    chatBox.innerHTML += `<div class="bot-message">${text}</div>`;
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Gestion de la touche Entrée pour le chat
document.getElementById('user-input').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') sendMessage();
});

// --- Lancement ---
document.addEventListener('DOMContentLoaded', () => {
    initChart();
    updateDashboardData();
    // Rafraîchir les données toutes les 3 secondes
    setInterval(updateDashboardData, 3000);
});