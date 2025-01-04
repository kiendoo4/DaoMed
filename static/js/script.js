// Get references to the input and display elements
const usernameInput = document.getElementById('usernameInput');
const passwordInput = document.getElementById('passwordInput');
const displayKey = document.getElementById('displayKey');
const confirmButton = document.getElementById('confirmButton');
const errorMessage = document.getElementById('errorMessage'); // Make sure you have this element in your HTML
const popupModal = document.getElementById("popupModal");
// Create a div in your HTML to display response
const responseDiv = document.getElementById('responseDisplay');

usernameInput.addEventListener('input', () => {
  // Enable the "Confirm" button only if the input has characters
  confirmButton.disabled = usernameInput.value.trim() === "";
  confirmButton.disabled = passwordInput.value.trim() === "";
});

passwordInput.addEventListener('input', () => {
  // Enable the "Confirm" button only if the input has characters
  confirmButton.disabled = passwordInput.value.trim() === "";
  confirmButton.disabled = usernameInput.value.trim() === "";
});

confirmButton.addEventListener("click", () => {
  popupModal.style.display = "block";

});

window.addEventListener("click", (event) => {
  if (event.target === popupModal) {
    popupModal.style.display = "none";
  }
  else
   {
    errorMessage.style.display = "none";
   }
});

// Handle button click
confirmButton.addEventListener("click", async () => {
  const apiKey = apiKeyInput.value.trim();

  try {
    // Use the actual Gemini API endpoint for generative AI
    const response = await fetch("https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-goog-api-key": apiKey // Gemini uses 'x-goog-api-key' header
      },
      body: JSON.stringify({
        contents: [{
          parts: [{
            text: "Hello, can you confirm the API key is working?"
          }]
        }]
      })
    });

    if (response.ok) {
      // If response is okay, validate the response
      const data = await response.json();
      // Check if the response contains expected properties
      if (data.candidates && data.candidates.length > 0) {
        // API key is valid, proceed to chat interface
        errorMessage.textContent = "Successfully!!";
        errorMessage.style.color = "green";
        errorMessage.style.border = "1px solid green";
        errorMessage.style.display = "block";
        const backendResponse = await fetch("/get-gemini-apikey", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          apiKey: apiKey  // Send the API key to the backend
          })
        }).then(response => response.json())
          .then(data => console.log(data))
          .catch(error => console.error("Error:", error));
        window.location.href = "/mainUI";
      } else {
        throw new Error("Invalid API response");
      }
    } else {
      // Handle API errors
      const errorData = await response.json();
      responseDiv.textContent = JSON.stringify(errorData, null, 2);
      errorMessage.textContent = errorData.error?.message || "Invalid API Key!";
      errorMessage.style.display = "block";
    }
  } catch (error) {
    // Handle any network or validation errors
    console.error("Connection error:", error);
    errorMessage.textContent = "Không thể kết nối đến Gemini. Vui lòng kiểm tra lại API key.";
    errorMessage.style.display = "block";
  }
});