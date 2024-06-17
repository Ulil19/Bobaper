$(document).ready(function () {
  $("#registerForm").submit(function (e) {
    e.preventDefault();
    email = $("#email").val();
    username = $("#username").val();
    password = $("#password").val();

    // Email validation
    if (!email.match(/^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$/)) {
      $("#emailHelp")
        .text("Invalid email address")
        .removeClass("text-success")
        .addClass("text-danger");
      return;
    }

    // Username validation
    if (!username.match(/^[a-zA-Z0-9]+$/)) {
      $("#usernameHelp")
        .text("Username can only contain letters and numbers")
        .removeClass("text-success")
        .addClass("text-danger");
      return;
    }

    // Password validation
    if (!password.match(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,}$/)) {
      $("#passwordHelp")
        .text(
          "Password must contain at least one uppercase letter, one lowercase letter, and one number"
        )
        .removeClass("text-success")
        .addClass("text-danger");
      return;
    }

    $.ajax({
      url: "/check-dup",
      type: "POST",
      data: { email: email },
      success: function (response) {
        if (response.exists) {
          $("#emailHelp")
            .text("Email already registered. Please use another email.")
            .removeClass("text-success")
            .addClass("text-danger");
        } else {
          // Call the register function if the email is not duplicated
          $.ajax({
            type: "POST",
            url: "/register/admin/save",
            data: {
              email: email,
              username: username,
              password: password,
            },
            success: function (response) {
              Swal.fire({
                icon: "success",
                title: "Success",
                text: "Admin registered successfully!",
              }).then(() => {
                window.location.replace("/login/admin");
              });
            },
          });
        }
      },
      error: function () {
        Swal.fire({
          icon: "error",
          title: "Error",
          text: "An error occurred while checking the email.",
        });
      },
    });
  });
});
