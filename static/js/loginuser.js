const toggleForm = () => {
  const container = document.querySelector(".container");
  container.classList.toggle("active");
};

$(document).ready(function () {
  // Function to validate email format
  function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
  }

  // Function to validate password format
  function validatePassword(password) {
    const re = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[A-Za-z\d]{8,}$/;
    return re.test(password);
  }

  // Include token in all AJAX requests if available
  $.ajaxSetup({
    beforeSend: function (xhr, settings) {
      let token = sessionStorage.getItem("token");
      if (token) {
        xhr.setRequestHeader("Authorization", "Bearer " + token);
      }
    },
  });

  // Function to add token to navbar links
  function updateNavbarLinks() {
    let token = sessionStorage.getItem("token");
    if (token) {
      $("nav .navbar-nav a").each(function () {
        let href = $(this).attr("href");
        if (href && href !== "#") {
          let url = new URL(href, window.location.origin);
          url.searchParams.set("token", token);
          $(this).attr("href", url.href);
        }
      });
    }
  }

  updateNavbarLinks();

  // Login form submit handler
  $("#loginForm").submit(function (event) {
    event.preventDefault();

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
            Swal.fire({
              icon: "success",
              title: "Success",
              text: "Login Berhasil!",
            }).then(function () {
              sessionStorage.setItem("token", response.token);
              window.location.replace("/product");
            });
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

  // Register form submit handler
  $("#registerForm").submit(function (event) {
    event.preventDefault();

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
            Swal.fire({
              icon: "success",
              title: "Success",
              text: "User Berhasil Didaftarkan!",
            }).then(function () {
              window.location.replace("/login/user");
            });
          } else {
            // Display error message
            if (response.message === "Email already registered") {
              $("#emailHelp").text(response.message);
            } else if (response.message === "Passwords do not match") {
              $("#passwordHelp2").text(response.message);
            } else {
              Swal.fire({
                icon: "error",
                title: "Error",
                text: "Registration failed. Please try again.",
              });
            }
          }
        },
        error: function (xhr, status, error) {
          alert("An error occurred: " + error);
        },
      });
    }
  });
});
