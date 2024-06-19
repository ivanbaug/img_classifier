const API_URL = 'http://127.0.0.1:5000'

let firstLoad = true;
const keepBtn = document.getElementById('keepBtn');
const workBtn = document.getElementById('workBtn');
const memeBtn = document.getElementById('memeBtn');
const screenshotBtn = document.getElementById('screenshotBtn');

const currentImage = document.getElementById('currentImage');
let currentFilename = '';

keepBtn.addEventListener('click', function() {
    sendImgTypeGetNewImg('keep');
});

memeBtn.addEventListener('click', function() {
    sendImgTypeGetNewImg('meme');
});

screenshotBtn.addEventListener('click', function() {
    sendImgTypeGetNewImg('screenshot');
});

workBtn.addEventListener('click', function() {
    sendImgTypeGetNewImg('work');
});

async function fetchImage() {
    try {
        const response = await fetch(API_URL + "/random_image64", {
            method: 'GET',
            url: API_URL,
        });
        const data = await response.json();
        currentFilename = data.filename;


        // Display the image
        const imgElement = document.getElementById('imageElement');
        imgElement.src = 'data:image/jpeg;base64,' + data.image;

    } catch (error) {
        console.error('Error fetching image:', error);
    }
}

async function sendImgTypeGetNewImg(imgType) {
    try {
        const postData = {
            filename: currentFilename,
            imgType: imgType
        };
        const response = await fetch(API_URL + "/tag_img_get_new", {
            method: "POST",
            url: API_URL,
            headers: {'Content-Type': 'application/json'}, 
            body: JSON.stringify(postData)
        });

        const data = await response.json();
        currentFilename = data.filename;


        // Display the image
        const imgElement = document.getElementById('imageElement');
        imgElement.src = 'data:image/jpeg;base64,' + data.image;

    } catch (error) {
        console.error('Error fetching image:', error);
    }
}



if (firstLoad) {
    fetchImage();
    firstLoad = false;
}