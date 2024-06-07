let firstLoad = true;
const keepBtn = document.getElementById('keepBtn');
const forgetBtn = document.getElementById('forgetBtn');
const workBtn = document.getElementById('workBtn');

const currentImage = document.getElementById('currentImage');

keepBtn.addEventListener('click', function() {
    console.log('Next button clicked');
    fetchImage();
});

forgetBtn.addEventListener('click', function() {
    console.log('Forget button clicked');
    fetchImage();
});

workBtn.addEventListener('click', function() {
    console.log('Work button clicked');
    fetchImage();
});

async function fetchImage() {
    try {
        const response = await fetch("http://127.0.0.1:5000/random_image64", {
        method: 'GET',
        url: `http://127.0.0.1:5000`,
    });
        const data = await response.json();
        const filename = data.filename;
        console.log('Filename:', filename);


        // Display the image
        const imgElement = document.getElementById('imageElement');
        imgElement.src = 'data:image/jpeg;base64,'+data.image;

    } catch (error) {
        console.error('Error fetching image:', error);
    }
}

if (firstLoad) {
    fetchImage();
    firstLoad = false;
}