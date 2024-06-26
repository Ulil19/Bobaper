function loginadmin() {
  let email = $("#input-email").val();
  let password = $("#input-password").val();

  if (email === "") {
    $("#emailHelp").text("Please enter your email");
    $("#input-email").focus();
    return false;
  } else {
    $("#emailHelp").text("");
  }
  if (password === "") {
    $("#passwordHelp").text("Please enter your password");
    $("#input-password").focus();
    return false;
  } else {
    $("#passwordHelp").text("");
  }

  $.ajax({
    type: "POST",
    url: "/login/admin",
    data: {
      email: email,
      password: password,
    },
    success: function (response) {
      console.log(response);
      if (response["result"] === "success") {
        Swal.fire({
          icon: "success",
          title: "Success",
          text: "Login Berhasil!",
        }).then(() => {
          window.location.href = "/dashboard";
        });
      } else {
        Swal.fire({
          icon: "error",
          title: "Error",
          text: "Login Failed!",
        });
      }
    },
  });
  return false;
}
