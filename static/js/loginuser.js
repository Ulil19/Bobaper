$(document).ready(function () {
  $("#loginForm").submit(function (event) {
    event.preventDefault(); // Prevent the form from submitting the traditional way

    // Clear previous errors
    $("#emailHelp").text("");
    $("#passwordHelp").text("");

    // Get form values
    let email = $("#input-email").val().trim();
    let password = $("#input-password").val().trim();

    // Simple validation
    let valid = true;

    if (email === "") {
      $("#emailHelp").text("Email is required.");
      valid = false;
    } else if (!validateEmail(email)) {
      $("#emailHelp").text("Invalid email format.");
      valid = false;
    }

    if (password === "") {
      $("#passwordHelp").text("Password is required.");
      valid = false;
    }

    if (valid) {
      // Perform AJAX request
      $.ajax({
        url: "/login/user/validate",
        type: "POST",
        data: {
          email: email,
          password: password,
        },
        success: function (response) {
          if (response.result === "success") {
            alert("Login successful!");
            // Store token and user ID in session or client-side storage
            sessionStorage.setItem("token", response.token);
            sessionStorage.setItem("userId", response.user_id);
            // Redirect to product page
            window.location.href = "/product";
          } else {
            $("#passwordHelp").text(response.message);
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
});
