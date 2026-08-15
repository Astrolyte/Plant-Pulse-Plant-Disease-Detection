console.log("style.js loaded");
// SHOW MENU
const navMenu = document.getElementById("nav-menu");
const navToggle = document.getElementById("nav-toggle");
const navClose = document.getElementById("nav-close");

if (navToggle) {
  navToggle.addEventListener("click", () => {
    navMenu.classList.add("show-menu");
  });
}

if (navClose) {
  navClose.addEventListener("click", () => {
    navMenu.classList.remove("show-menu");
  });
}

// REMOVE MENU MOBILE
const navLink = document.querySelectorAll(".nav-link");

function linkAction() {
  const navMenu = document.getElementById("nav-menu");
  navMenu.classList.remove("show-menu");
}

navLink.forEach((f) => f.addEventListener("click", linkAction));

// CHANGE BACKGROUND HEADER
function scrollHeader() {
  const header = document.getElementById("header");
  if (this.scrollY >= 80) header.classList.add("scroll-header");
  else header.classList.remove("scroll-header");
}

window.addEventListener("scroll", scrollHeader);

// QUESTIONS ACCORDION
const accordionItems = document.querySelectorAll(".questions-item");

accordionItems.forEach((item) => {
  const accordionHeader = item.querySelector(".questions-header");

  accordionHeader.addEventListener("click", () => {
    const openItem = document.querySelector(".accordion-open");

    toggleItem(item);

    if (openItem && openItem !== item) {
      toggleItem(openItem);
    }
  });
});

const toggleItem = (item) => {
  const accordionContent = item.querySelector(".questions-content");

  if (item.classList.contains("accordion-open")) {
    accordionContent.removeAttribute("style");
    item.classList.remove("accordion-open");
  } else {
    accordionContent.style.height = accordionContent.scrollHeight + "px";
    item.classList.add("accordion-open");
  }
};

// SCROLL SECTIONS ACTIV LINK
const sections = document.querySelectorAll("section[id]");

function scrollActive() {
  const scrollY = window.pageYOffset;

  sections.forEach((current) => {
    const sectionHeight = current.offsetHeight,
      sectionTop = current.offsetTop - 58,
      sectionId = current.getAttribute("id");

    if ((scrollY > sectionTop) & (scrollY <= sectionTop + sectionHeight)) {
      document
        .querySelector(".nav-menu a[href*=" + sectionId + "]")
        .classList.add("active-link");
    } else {
      document
        .querySelector(".nav-menu a[href*=" + sectionId + "]")
        .classList.remove("active-link");
    }
  });
}

window.addEventListener("scroll", scrollActive);

// SHOW SCROLL UP
function scrollUp() {
  const scrollUp = document.getElementById("scroll-up");

  if (this.scrollY >= 200) scrollUp.classList.add("show-scroll");
  else scrollUp.classList.remove("show-scroll");
}

window.addEventListener("scroll", scrollUp);

// DARK LIGHT THEME
const themeButton = document.getElementById("theme-button");
const darkTheme = "dark-theme";
const iconTheme = "ri-sun-line";

const selectedTheme = localStorage.getItem("selected-theme");
const selectedIcon = localStorage.getItem("selected-icon");

const getCurrentTheme = () =>
  document.body.classList.contains(darkTheme) ? "dark" : "light";
const getCurrentIcon = () =>
  themeButton.classList.contains(iconTheme) ? "ri-moon-line" : "ri-sun-line";

if (selectedTheme) {
  document.body.classList[selectedTheme === "dark" ? "add" : "remove"](
    darkTheme,
  );
  themeButton.classList[selectedIcon === "ri-moon-line" ? "add" : "remove"](
    iconTheme,
  );
}

themeButton.addEventListener("click", () => {
  document.body.classList.toggle(darkTheme);
  themeButton.classList.toggle(iconTheme);

  localStorage.setItem("selected-theme", getCurrentTheme());
  localStorage.setItem("selected-icon", getCurrentIcon());
});

// SCROLL REVEAL ANIMATION
const sr = ScrollReveal({
  origin: "top",
  distance: "60px",
  duration: 2500,
  delay: 400,
});

document.addEventListener("DOMContentLoaded", function () {
    const uploadBtn = document.getElementById("upload-btn");
    const imageInput = document.getElementById("image-input");
    const diagnoseBtn = document.getElementById("diagnose-btn");
    const plantNameInput = document.getElementById("plant-name");
    const resultsDiv = document.getElementById("results");
    const moreInfoBtn = document.getElementById("more-info-btn");
    const imagePreview = document.getElementById("image-preview");

    let selectedPlantName = "";
    let selectedFile = null;
    let diseaseData = null;

    // Plant name input

    plantNameInput.addEventListener("input", function () {
        selectedPlantName = plantNameInput.value.trim();
        updateDiagnoseButtonState();
    });

    // Upload button


    uploadBtn.addEventListener("click", function () {
        imageInput.click();
    });

    // Image selection


    imageInput.addEventListener("change", function (event) {

        const file = event.target.files[0];

        if (!file) {
            return;
        }

        // Validate file type
        if (!file.type.startsWith("image/")) {

            resultsDiv.innerHTML ="<p>Please select a valid image file.</p>";

            imageInput.value = "";
            selectedFile = null;

            updateDiagnoseButtonState();

            return;
        }

        // Validate file size - 5 MB
        const maxSize = 5 * 1024 * 1024;

        if (file.size > maxSize) {

            resultsDiv.innerHTML ="<p>Image size must be less than 5 MB.</p>";

            imageInput.value = "";
            selectedFile = null;

            updateDiagnoseButtonState();

            return;
        }

        selectedFile = file;

        updateDiagnoseButtonState();

        // Preview image
        const reader = new FileReader();

        reader.onload = function (e) {

            imagePreview.src = e.target.result;
            imagePreview.style.display = "block";

        };

        reader.readAsDataURL(file);
    });


    // Diagnose button state


    function updateDiagnoseButtonState() {

        diagnoseBtn.disabled = !(
            selectedPlantName &&
            selectedFile
        );

    }


    // Prediction


    diagnoseBtn.addEventListener("click", async function () {

        if (!selectedPlantName || !selectedFile) {

            alert(
                "Please enter a plant name and upload an image."
            );

            return;
        }


        // Disable button during inference
        diagnoseBtn.disabled = true;

        diagnoseBtn.textContent = "Analyzing...";

        resultsDiv.innerHTML ="<p>Analyzing image... Please wait.</p>";

        moreInfoBtn.style.display = "none";

        diseaseData = null;

        // Create request


        const formData = new FormData();

        formData.append(
            "file",
            selectedFile
        );

        formData.append(
            "plant_type",
            selectedPlantName
        );


        try {

            const response = await fetch(
                "/api/predict",
                {
                    method: "POST",
                    body: formData
                }
            );


            const data = await response.json();


            // Handle HTTP errors


            if (!response.ok) {

                resultsDiv.innerHTML = `
                    <p>
                        <strong>Error:</strong>
                        ${data.error || "Prediction failed."}
                    </p>
                    <p>
                        Request ID:
                        ${data.request_id || "N/A"}
                    </p>
                `;

                return;
            }

            // Validate response


            if (!data.prediction) {

                resultsDiv.innerHTML =
                    "<p>No prediction received.</p>";

                return;
            }


            // Extract prediction

            const disease = data.prediction.disease;

            const confidence = data.prediction.confidence;


            diseaseData = disease;


            // Display result

            const confidencePercentage = (confidence * 100).toFixed(2);


            const recommendation =
                disease === "Healthy"
                    ? "Your plant looks healthy! Continue regular care."
                    : "Consult a plant specialist for targeted treatment.";


            resultsDiv.innerHTML = `

                <div class="prediction-result">

                    <p>
                        <strong>Plant:</strong>
                        ${selectedPlantName}
                    </p>

                    <p>
                        <strong>Analysis Result:</strong>
                        ${disease}
                    </p>

                    <p>
                        <strong>Confidence:</strong>
                        ${confidencePercentage}%
                    </p>

                    <p>
                        <strong>Recommended Action:</strong>
                        ${recommendation}
                    </p>

                    <p>
                        <small>
                            Request ID:
                            ${data.request_id}
                        </small>
                    </p>

                </div>

            `;


            // Show more information button
            moreInfoBtn.style.display ="inline-block";


        } catch (error) {

            console.error(
                "Error analyzing plant:",
                error
            );

            resultsDiv.innerHTML = `
                <p>
                    <strong>Error analyzing plant.</strong>
                </p>
                <p>
                    Please check your connection
                    and try again.
                </p>
            `;

        } finally {

            // Re-enable button
            diagnoseBtn.disabled = !(
                selectedPlantName &&
                selectedFile
            );

            diagnoseBtn.textContent ="Diagnose";

        }

    });


    // ------------------------------------------
    // More information
    // ------------------------------------------

    moreInfoBtn.addEventListener(
        "click",
        function () {

            if (!diseaseData) {
                return;
            }


            const diseaseDetails =
                getDiseaseDetails(diseaseData);


            if (!diseaseDetails.symptoms) {

                resultsDiv.innerHTML += `
                    <div class="disease-details">
                        <p>
                            No additional information
                            available for this disease.
                        </p>
                    </div>
                `;

                return;
            }


            resultsDiv.innerHTML += `

                <div class="disease-details">

                    <h3>
                        More Information About
                        ${diseaseData}
                    </h3>

                    <p>
                        <strong>Symptoms:</strong>
                        ${diseaseDetails.symptoms}
                    </p>

                    <p>
                        <strong>Treatment:</strong>
                        ${diseaseDetails.treatment}
                    </p>

                    <p>
                        <strong>Where to Buy Medicines:</strong>
                        ${diseaseDetails.medicineStores}
                    </p>

                </div>

            `;

        }
    );

    // Disease information


    function getDiseaseDetails(disease) {

        const diseaseInfo = {

            "Healthy": {

                symptoms:
                    "No symptoms. Your plant is healthy.",

                treatment:
                    "No treatment needed. Keep up regular care.",

                medicineStores:
                    "Not applicable."

            },


            "Early_blight": {

                symptoms:
                    "Dark spots on leaves with concentric rings.",

                treatment:
                    "Use fungicides and remove affected leaves.",

                medicineStores:
                    "Buy fungicides from gardening stores or online."

            },


            "Late_blight": {

                symptoms:
                    "Water-soaked lesions, often leading to plant decay.",

                treatment:
                    "Use appropriate fungicides or remove affected plants.",

                medicineStores:
                    "Available at most garden centers."

            },


            "Septoria_leaf_spots": {

                symptoms:
                    "Small, dark brown to black spots with light centers.",

                treatment:
                    "Remove infected leaves and apply appropriate fungicides.",

                medicineStores:
                    "Available at gardening and plant-care stores."

            },


            "Bacterial_spot": {

                symptoms:
                    "Water-soaked spots on leaves with yellow halos.",

                treatment:
                    "Remove affected leaves and use appropriate plant-care treatment.",

                medicineStores:
                    "Available at specialized plant-care stores."

            },


            "Yellow_leaf_curl_virus": {

                symptoms:
                    "Yellowing and curling of leaves.",

                treatment:
                    "Remove infected plants to help prevent spread.",

                medicineStores:
                    "No direct cure; consider resistant plant varieties."

            }

        };


        return diseaseInfo[disease] || {};

    }

});

sr.reveal(`.home-data`);
sr.reveal(`.home-img`, { delay: 500 });
sr.reveal(`.home-social`, { delay: 600 });
sr.reveal(`.about-img, .contact-box`, { origin: "left" });
sr.reveal(`.about-data, .contact-form`, { origin: "right" });
sr.reveal(`.steps-card, .product-card, .questions-group, .footer`, {
  interval: 100,
});
