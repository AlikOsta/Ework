function previewImage(event) {
    var reader = new FileReader();
    reader.onload = function() {
        var output = document.getElementById('image-preview');
        var previewContainer = document.getElementById('image-preview-container');
        var uploadLabel = document.getElementById('upload-label');

        output.src = reader.result;
        previewContainer.classList.remove('hidden');
        previewContainer.style.display = 'block';
        uploadLabel.classList.add('hidden');
    };
    reader.readAsDataURL(event.target.files[0]);
}

function clearImage() {
    var previewContainer = document.getElementById('image-preview-container');
    var uploadLabel = document.getElementById('upload-label');
    var photoUpload = document.getElementById('photo-upload');
    photoUpload.value = '';
    previewContainer.classList.add('hidden');
    previewContainer.style.display = 'none';
    uploadLabel.classList.remove('hidden');
    document.getElementById('image-preview').src = '#';
}

// Простое переключение поля изображения
document.addEventListener('change', function(e) {    
    if (e.target.dataset.toggle === 'image-field') {
        document.getElementById('image-upload-wrapper').style.display = e.target.checked ? 'block' : 'none';
        if (!e.target.checked) {
            clearImage(); 
        }
    }
});