const bannerImageInput = document.getElementById("bannerImgInput");
bannerImagePlaceholder = document.getElementById("bannerImgPlaceholder");
const bannerImageName = document.getElementById("bannerImgName");
const bannerImgDisplay = document.getElementById("bannerImgDisplay");
const titleInput = document.getElementById("titleInput");
const titleHelp = document.getElementById("titleHelp");
const descriptionInput = document.getElementById("descriptionInput");
const descriptionHelp = document.getElementById("descriptionHelp");

bannerImageInput.addEventListener("change", (e) => {
    if (e.target.files[0]) {
        const file = e.target.files[0];
        bannerImageName.innerText = file.name;
        bannerImgDisplay.src = URL.createObjectURL(file);
        bannerImagePlaceholder.classList.toggle("d-none");
        bannerImgDisplay.classList.toggle("d-none");
    }
});

titleInput.addEventListener("input", () => {
    const titleLength = titleInput.value.length;
    if (titleLength <= 100) {
        titleHelp.innerText = `${100 - titleLength} Characters remaining`;
    } else if (titleLength > 100) {
        titleInput.value = titleInput.value.substring(0, 99);
        titleHelp.innerText = "0 Characters remaining";
    }
});

descriptionInput.addEventListener("input", () => {
    const descriptionLength = descriptionInput.value.length;
    if (descriptionLength <= 500) {
        descriptionHelp.innerText = `${500 - descriptionLength} Characters remaining`;
    } else if (descriptionLength > 500) {
        descriptionInput.value = descriptionInput.value.substring(0, 499);
        descriptionHelp.innerText = "0 Characters remaining";
    }
});