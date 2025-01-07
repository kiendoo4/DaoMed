// Get references to the input and display elements
const usernameInput = document.getElementById('usernameInput');
const passwordInput = document.getElementById('passwordInput');
const displayKey = document.getElementById('displayKey');
const confirmButton = document.getElementById('confirmButton');
const errorMessage = document.getElementById('errorMessage'); // Make sure you have this element in your HTML
const popupModal = document.getElementById("popupModal");
// Create a div in your HTML to display response
const responseDiv = document.getElementById('responseDisplay');

function updateConfirmButtonState() {
  // Enable the "Confirm" button only if both inputs have characters
  confirmButton.disabled = usernameInput.value.trim() === "" || passwordInput.value.trim() === "";
}

// Add event listeners for both inputs
usernameInput.addEventListener('input', updateConfirmButtonState);
passwordInput.addEventListener('input', updateConfirmButtonState);

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
  const username = usernameInput.value.trim(); // Get username
  const password = passwordInput.value.trim(); // Get password

  try {
    // Send credentials to the backend for validation
    const response = await fetch("/validate-account", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        username: username, // Send username to the backend
        password: password, // Send password to the backend
      }),
    });

    if (response.ok) {
      // If response is okay, validate the response
      const data = await response.json();
      if (data.isValid) {
        // Login is successful, proceed to chat interface
        errorMessage.textContent = "Đăng nhập thành công!";
        errorMessage.style.color = "green";
        errorMessage.style.border = "1px solid green";
        errorMessage.style.display = "block";

        // Redirect to the main UI
        window.location.href = "/mainUI";
      } else {
        // Invalid credentials
        errorMessage.textContent = data.message;
        errorMessage.style.color = "red";
        errorMessage.style.border = "1px solid red";
        errorMessage.style.display = "block";
      }
    } else {
      // Handle backend errors
      const errorData = await response.json();
      responseDiv.textContent = JSON.stringify(errorData, null, 2);
      errorMessage.textContent = errorData.message || "Có lỗi xảy ra trong quá trình đăng nhập!";
      errorMessage.style.color = "red";
      errorMessage.style.border = "1px solid red";
      errorMessage.style.display = "block";
    }
  } catch (error) {
    // Handle network or other unexpected errors
    console.error("Connection error:", error);
    errorMessage.textContent = "Có lỗi xảy ra trong quá trình đăng nhập!";
    errorMessage.style.color = "red";
    errorMessage.style.border = "1px solid red";
    errorMessage.style.display = "block";
  }
});