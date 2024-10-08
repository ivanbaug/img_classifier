if (API_URL == null){
    var API_URL = 'http://127.0.0.1:5000';
}

let sessionId = getQueryVariable("session");

let firstLoad = true;
const keepBtn = document.getElementById('keepBtn');
const workBtn = document.getElementById('workBtn');
// const memeBtn = document.getElementById('memeBtn');
const screenshotBtn = document.getElementById('screenshotBtn');

const mainMenuBtn = document.getElementById('mainMenuBtn');
const savePrcBtn = document.getElementById('savePrcBtn');

const trainFullBtn = document.getElementById('trainFullBtn');
const trainFineTuneBtn = document.getElementById('trainFineTuneBtn');

const screenshotEmoji = document.getElementById('screenshotPredicted');
const workEmoji = document.getElementById('workPredicted');
const keepEmoji = document.getElementById('keepPredicted');


const currentImage = document.getElementById('currentImage');
let currentFilename = '';

keepBtn.addEventListener('click', function() {
    sendImgTypeGetNewImg('keep');
});

// memeBtn.addEventListener('click', function() {
//     sendImgTypeGetNewImg('meme');
// });

screenshotBtn.addEventListener('click', function() {
    sendImgTypeGetNewImg('screenshot');
});

workBtn.addEventListener('click', function() {
    sendImgTypeGetNewImg('work');
});

mainMenuBtn.addEventListener('click', function() {
    document.location.href = '/';
});

savePrcBtn.addEventListener('click', function() {
    copyImgsToNewFolder();
});


trainFullBtn.addEventListener('click', function() {
    trainModel(true);
});

trainFineTuneBtn.addEventListener('click', function() {
    trainModel(false);
});

async function trainModel(fullTrain) {
    showSpinner();
    try {
        const postData = {
            sessionId: sessionId,
            fullTrain: fullTrain
        };
        const response = await fetch(API_URL + "/train_model", {
            method: "POST",
            url: API_URL,
            headers: {'Content-Type': 'application/json'}, 
            body: JSON.stringify(postData)
        });

        const statusCode = response.status;
        const data = await response.json();
        console.log(data);

        if (statusCode === 200) {            
            window.alert(data.info);
        } else {
            console.log(data.info);
            window.alert(data.info);
        }

    } catch (error) {
        console.log(data.info);
        console.error('Error training model:', error);
    } finally {
        hideSpinner();
    }
    
} 

async function fetchImage() {
    try {
        const response = await fetch(API_URL + "/random_image64?session=" + sessionId , {
            method: 'GET',
            url: API_URL,
        });

        const data = await response.json();

        if (data.success === false) {
            displayStats(data);
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

        // Display the predicted class
        displayPredicted(data);


    } catch (error) {
        console.error('Error fetching image:', error);
    }
}

function displayPredicted (data) {
    // Display the predicted class
    if (data.predicted) {
        keepEmoji.classList.add('hidden');
        workEmoji.classList.add('hidden');
        screenshotEmoji.classList.add('hidden');

        switch (data.predicted) {
            case 'keep':
                keepEmoji.classList.remove('hidden');
                break;
            case 'work':
                workEmoji.classList.remove('hidden');
                break;
            case 'screenshot':
                screenshotEmoji.classList.remove('hidden');
                break;
            default:
                break;
        }
    } else {
        keepEmoji.classList.add('hidden');
        workEmoji.classList.add('hidden');
        screenshotEmoji.classList.add('hidden');
    }
}

async function sendImgTypeGetNewImg(imgType) {
    showSpinner();
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

            if (data.success === false) {
                displayStats(data);
                alert(data.info);
                hideSpinner(); 
                return;
            }
            
            currentFilename = data.filename;
            // check file type by reading the file extension
            const fileExt = currentFilename.split('.').pop();
            const contentType = getContentType(fileExt);
            
            // Display the image
            const imgElement = document.getElementById('imageElement');
            imgElement.src = `data:${contentType};base64,` + data.image;
            // Display the stats
            displayStats(data);

            // Display the predicted class
            displayPredicted(data);
        } else {
            console.log(data.info);                    
        }
        hideSpinner();


    } catch (error) {
        // console.log(data.info);
        console.error('Error fetching image:', error);
        hideSpinner();
    }
}

async function copyImgsToNewFolder() {
    showSpinner();
    try {
        const response = await fetch(API_URL + "/copy_imgs_to_new_folder?session=" + sessionId , {
            method: 'GET',
            url: API_URL,
        });


        const data = await response.json();

        if (data.success === false) {
            hideSpinner();
            alert(data.info);            
            return;
        }
        else {
            hideSpinner();
            alert(data.info);
        }

    } catch (error) {
        hideSpinner();
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
        let objRemaining = data.stats.find(obj => obj.class === '');
        if (!objRemaining) {
            objRemaining = {amount: 0};
        }
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

const spinner = document.getElementById('spinner');

function showSpinner() {
    // console.log('show spinner');    
    spinner.classList.remove('hidden');
}

function hideSpinner() {
    // console.log('hide spinner');
    spinner.classList.add('hidden');
}