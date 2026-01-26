// ======================================================
// 🧠 AEON - VERSÃO "SANGUE NO OLHO"
// ======================================================

// Pega IP e Porta da URL
const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const WS_URL = `${protocol}//${window.location.hostname}:${window.location.port}/ws`;

const videoElement = document.getElementById('bg-video');
const sphereElement = document.getElementById('mainSphere');
const chatArea = document.getElementById('chatArea');
const statusGem = document.getElementById('connectionStatus');

let socket;

window.addEventListener('load', () => {
    // ESSA É A PROVA QUE O ARQUIVO ATUALIZOU
    mostrarFumaca(`TESTE DE VERSÃO NOVA!\nTentando: ${WS_URL}`);
    
    iniciarCamera();
    setTimeout(conectarCerebro, 1000);
});

async function iniciarCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        videoElement.srcObject = stream;
        videoElement.play();
    } catch (err) {
        console.error("Erro Cam:", err);
        mostrarFumaca("Erro na Câmera (Permissão negada?)", true);
    }
}

function conectarCerebro() {
    socket = new WebSocket(WS_URL);

    socket.onopen = () => {
        mostrarFumaca("⚡ CONECTADO COM SUCESSO! ⚡");
        statusGem.style.backgroundColor = "#00ff00";
    };

    socket.onmessage = (event) => {
        mostrarFumaca(event.data);
    };

    socket.onclose = () => {
        mostrarFumaca("Desconectado. Tentando de novo...", true);
        statusGem.style.backgroundColor = "#ff0000";
        setTimeout(conectarCerebro, 3000);
    };
}

sphereElement.addEventListener('click', () => {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send("Ping: Toque na esfera");
        mostrarFumaca("Enviando sinal...");
    } else {
        mostrarFumaca("Cérebro offline!");
    }
});

function mostrarFumaca(texto, erro = false) {
    chatArea.innerHTML = ''; 
    const p = document.createElement('p');
    p.classList.add('smoke-text');
    p.innerText = texto;
    if (erro) p.style.color = '#ff4d4d';
    chatArea.appendChild(p);
}