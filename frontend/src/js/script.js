// import { API_URL } from './config.js';
const API_URL = 'http://127.0.0.1:5000';
let sessionId = getQueryVariable("session");

let firstLoad = true;
const keepBtn = document.getElementById('keepBtn');
const workBtn = document.getElementById('workBtn');
const memeBtn = document.getElementById('memeBtn');
const screenshotBtn = document.getElementById('screenshotBtn');

const mainMenuBtn = document.getElementById('mainMenuBtn');
const savePrcBtn = document.getElementById('savePrcBtn');


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

mainMenuBtn.addEventListener('click', function() {
    document.location.href = 'index.html';
});

savePrcBtn.addEventListener('click', function() {
    copyImgsToNewFolder();
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
        // check file type by reading the file extension
        const fileExt = currentFilename.split('.').pop();
        const contentType = getContentType(fileExt);

        // Display the image
        const imgElement = document.getElementById('imageElement');
        imgElement.src = `data:${contentType};base64,` + data.image;

        // If stats received, display them
        displayStats(data);

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
        console.log(data);

        if (statusCode === 200) {
            
            currentFilename = data.filename;
            // check file type by reading the file extension
            const fileExt = currentFilename.split('.').pop();
            const contentType = getContentType(fileExt);
            
            // Display the image
            const imgElement = document.getElementById('imageElement');
            imgElement.src = `data:${contentType};base64,` + data.image;
            // Display the stats
            displayStats(data);
        } else {
            console.log(data.info);
            
        }

    } catch (error) {
        console.log(data.info);
        console.error('Error fetching image:', error);
    }
}

async function copyImgsToNewFolder() {
    try {
        const response = await fetch(API_URL + "/copy_imgs_to_new_folder?session=" + sessionId , {
            method: 'GET',
            url: API_URL,
        });


        const data = await response.json();

        if (data.success === false) {
            alert(data.info);
            return;
        }
        else {
            alert(data.info);
        }

    } catch (error) {
        // console.error('Error fetching image:', error);
    }
}

function getContentType(fileExt) {
    // assign content type based on file extension
    let contentType = '';
    switch (fileExt.toLowerCase()) {
        case 'gif':
            contentType = 'image/gif';
            break;
        case 'jpg':
            contentType = 'image/jpeg';
        case 'jpeg':
            contentType = 'image/jpeg';
            break;
        case 'png':
            contentType = 'image/png';
            break;
        case 'tiff':
            contentType = 'image/tiff';
            break;
        case 'icon':
            contentType = 'image/vnd.microsoft.icon';
            break;
        case 'x-icon':
            contentType = 'image/x-icon';
            break;
        case 'djvu':
            contentType = 'image/vnd.djvu';
            break;
        case 'svg':
            contentType = 'image/svg+xml';
            break;
        default:
            contentType = 'image/jpeg';
    }
    return contentType;
}

function displayStats(data){
    // If stats received, display them
    if (data.stats) {
        const statsElement = document.getElementById('listStats');
        const totalStatsElement = document.getElementById('totalStats');
        const total = data.stats.reduce((a, b) => a + b.amount, 0);
        console.log(total);
        const objRemaining = data.stats.find(obj => obj.class === '');
        const labeled = total - objRemaining.amount;

        totalStatsElement.innerHTML = `Total: ${total} Labeled: ${labeled} Remaining: ${objRemaining.amount}`;

        // Display the stats as a ul list
        statsElement.innerHTML = '';
        data.stats.forEach(stat => {
            // skip if class is empty
            if (stat.class == '') {
                return;
            }
            const li = document.createElement('li');
            li.innerHTML = `${stat.class}: ${stat.amount}`;
            statsElement.appendChild(li);
        });            
    } else {
        const statsElement = document.getElementById('listStats');
        const totalStatsElement = document.getElementById('totalStats');
        totalStatsElement.innerHTML = '';
        statsElement.innerHTML = '';
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