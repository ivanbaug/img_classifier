// import { API_URL } from './config.js';
const API_URL = 'http://127.0.0.1:5000';

let firstLoad = true;
const btnContainer = document.getElementById('btnContainer');

async function getAvailableSessions() {
    try {

        const response = await fetch(API_URL + "/get_available_sessions", {
            method: "GET",
            url: API_URL,
        });

        const res = await response.json();
        console.log(res);

        if (res.success === false) {
            alert(res.info);
            return;
        }

        res.data.forEach(session => {
            const btn = document.createElement('button');
            btn.textContent = `Session ${session.session_id.toString()} - (${session.img_processed}/${session.img_total})`;
            btn.id = `btn-${session.session_id.toString()}`;
            btn.addEventListener('click', function() {
                document.location.href = `classi.html?session=${session.session_id.toString()}`;
            });
            btn.classList.add('bg-blue-500', 'hover:bg-blue-700', 'text-white', 'font-bold', 'py-2', 'px-4', 'w-36', 'rounded');
            btnContainer.appendChild(btn);
        });

    } catch (error) {
        console.error('Error fetching image:', error);
    }
}

if (firstLoad) {
    getAvailableSessions();
    firstLoad = false;
}