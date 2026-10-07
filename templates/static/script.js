const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const btnCapturar = document.getElementById('btnCapturar');
const resultadoDiv = document.getElementById('resultado');

// Iniciar cámara al cargar la página
navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => {
        video.srcObject = stream;
    })
    .catch(err => {
        resultadoDiv.innerHTML = `<p style="color:red;">No se pudo acceder a la cámara: ${err.message}</p>`;
    });

btnCapturar.addEventListener('click', () => {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);

    const imageDataUrl = canvas.toDataURL('image/jpeg', 0.8);

    resultadoDiv.innerHTML = "<p>Analizando...</p>";

    fetch('/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: imageDataUrl })
    })
    .then(res => res.json())
    .then(data => mostrarResultado(data))
    .catch(err => {
        resultadoDiv.innerHTML = `<p style="color:red;">Error: ${err.message}</p>`;
    });
});

function mostrarResultado(data) {
    const claseCard = data.acceso ? 'acceso-concedido' : 'acceso-denegado';
    const titulo = data.acceso ? '✅ Acceso concedido' : '❌ Acceso denegado';
    const mensajePrincipal = data.acceso
        ? `Bienvenido, <b>${data.nombre}</b>`
        : `Mejor coincidencia: ${data.nombre} (${data.confianza}%)`;

    let top3Html = '<div class="top3"><b>Top 3:</b><ul>';
    data.top3.forEach(item => {
        top3Html += `<li>${item.nombre}: ${item.confianza.toFixed(2)}%</li>`;
    });
    top3Html += '</ul></div>';

    resultadoDiv.innerHTML = `
        <div class="${claseCard}">
            <h2>${titulo}</h2>
            <p>${mensajePrincipal}</p>
            <p style="color:gray; font-size:13px;">faceId: ${data.face_id} | Margen: ${data.margen}pts</p>
        </div>
        ${top3Html}
    `;
}