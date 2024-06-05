$(document).ready(function () {
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

  // Existing loginForm submit handler
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
            alert("Login successful!");
            // Store token in session storage
            sessionStorage.setItem("token", response.token);
            // Redirect to product page with token
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
