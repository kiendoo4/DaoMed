const usernameInput = document.getElementById('usernameInput')
const passwordInput = document.getElementById('passwordInput')
const passwordconfirmInput = document.getElementById('passwordconfirmInput')
const messageBox = document.getElementById('messageBox'); 
const usernameLabel = document.getElementById('usernameLabel');
check_username = false;
check_password = false;
check_email = false;

usernameInput.addEventListener('blur', function () {
    const username = usernameInput.value.trim(); // Get and trim the input value
    if (username === "") {
        messageBox.textContent = ""; // Clear the message if blank
        usernameLabel.style.marginBottom = 0;
        return; // Ignore blank input
    }

    // Send a request to the server
    fetch('/check_username', {
        method: 'POST', // Or 'GET' if you're using a GET request
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username: username }), // Send the username
    })
        .then(response => response.json()) // Expecting a JSON response
        .then(data => {
            if (data.exists) {
                messageBox.textContent = "Username đã tồn tại, vui lòng chọn một username khác";
                messageBox.style.color = "red";
                messageBox.style.fontSize = "0.7em";
                messageBox.style.textAlign = "left";
                messageBox.style.fontFamily = "Roboto Condensed";
                messageBox.style.marginLeft = "2.5%";
                usernameLabel.style.paddingBottom += messageBox.style.height;
            } else {
                messageBox.textContent = "Username hợp lệ";
                messageBox.style.color = "green";
                messageBox.style.fontSize = "0.7em";
                messageBox.style.textAlign = "left";
                messageBox.style.fontFamily = "Roboto Condensed";
                messageBox.style.marginLeft = "2.5%";
                usernameLabel.style.marginBottom += messageBox.style.height;
            }
        })
        .catch(error => {
            console.error("Error:", error);
        });
});

passwordInput.addEventListener('input', validatePasswords);
passwordconfirmInput.addEventListener('input', validatePasswords);

function validatePasswords() {
    if (passwordInput.value === "" || passwordconfirmInput.value === "") {
        passwordMessage.textContent = ""; // Clear the message if either field is empty
        return;
    }

    if (passwordInput.value === passwordconfirmInput.value) {
        passwordMessage.textContent = "Trùng khớp";
        passwordMessage.style.color = "green";
        passwordMessage.style.fontSize = "0.7em";
        passwordMessage.style.textAlign = "left";
        passwordMessage.style.fontFamily = "Roboto Condensed";
        passwordMessage.style.marginLeft = "2%";
    } else {
        passwordMessage.textContent = "Không trùng khớp";
        passwordMessage.style.color = "red";
        passwordMessage.style.fontSize = "0.7em";
        passwordMessage.style.textAlign = "left";
        passwordMessage.style.fontFamily = "Roboto Condensed";
        passwordMessage.style.marginLeft = "2%";
    }
}