// import { API_URL } from './config.js';
const API_URL = 'http://127.0.0.1:5000';
let sessionId = getQueryVariable("session");

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
        const response = await fetch(API_URL + "/random_image64?session=" + sessionId , {
            method: 'GET',
            url: API_URL,
        });


        const data = await response.json();

        if (data.success === false) {
            alert(data.info);
            return;
        }

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
            imgType: imgType,
            sessionId: sessionId
        };
        const response = await fetch(API_URL + "/tag_img_get_new", {
            method: "POST",
            url: API_URL,
            headers: {'Content-Type': 'application/json'}, 
            body: JSON.stringify(postData)
        });

        const statusCode = response.status;
        const data = await response.json();
        log(data);

        if (statusCode === 200) {
            
            currentFilename = data.filename;
            // Display the image
            const imgElement = document.getElementById('imageElement');
            imgElement.src = 'data:image/jpeg;base64,' + data.image;
        } else {
            console.log(data.info);
            
        }


    } catch (error) {
        console.log(data.info);
        console.error('Error fetching image:', error);
    }
}

function getQueryVariable(variable) {
    var query = window.location.search.substring(1);
    var vars = query.split("&");
    for (var i=0;i<vars.length;i++) {
      var pair = vars[i].split("=");
      if (pair[0] == variable) {
        return pair[1];
      }
    } 
    alert('Query Variable ' + variable + ' not found');
  }



if (firstLoad) {
    fetchImage();
    firstLoad = false;
}