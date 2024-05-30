$(document).ready(function () {
  $("#registerForm").submit(function (event) {
    event.preventDefault(); // Prevent the form from submitting the traditional way

    // Clear previous errors
    $("#emailHelp").text("");
    $("#usernameHelp").text("");
    $("#passwordHelp").text("");
    $("#passwordHelp2").text("");

    // Get form values
    let email = $("#email").val().trim();
    let username = $("#username").val().trim();
    let password = $("#password").val().trim();
    let password2 = $("#password2").val().trim();

    // Simple validation
    let valid = true;

    if (email === "") {
      $("#emailHelp").text("Email is required.");
      valid = false;
    } else if (!validateEmail(email)) {
      $("#emailHelp").text("Invalid email format.");
      valid = false;
    }

    if (username === "") {
      $("#usernameHelp").text("Username is required.");
      valid = false;
    }

    if (password === "") {
      $("#passwordHelp").text("Password is required.");
      valid = false;
    } else if (!validatePassword(password)) {
      $("#passwordHelp").text(
        "Password must contain at least one uppercase letter, one lowercase letter, one number, and be at least 8 characters long."
      );
      valid = false;
    }

    if (password2 === "") {
      $("#passwordHelp2").text("Confirm Password is required.");
      valid = false;
    } else if (password !== password2) {
      $("#passwordHelp2").text("Passwords do not match.");
      valid = false;
    }

    if (valid) {
      // Perform AJAX request
      $.ajax({
        url: "/register/user/save",
        type: "POST",
        data: {
          email: email,
          username: username,
          password: password,
          password2: password2,
        },
        success: function (response) {
          if (response.result === "success") {
            alert("User registered successfully!");
            window.location.replace("/login/user");
          } else {
            // Display error message
            if (response.message === "Email already registered") {
              $("#emailHelp").text(response.message);
            } else if (response.message === "Passwords do not match") {
              $("#passwordHelp2").text(response.message);
            } else {
              alert("Registration failed. Please try again.");
            }
          }
        },
        error: function (xhr, status, error) {
          alert("An error occurred: " + error);
        },
      });
    }
  });

  function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
  }

  function validatePassword(password) {
    const re = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[A-Za-z\d]{8,}$/;
    return re.test(password);
  }
});
