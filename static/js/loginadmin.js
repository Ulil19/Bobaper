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
        window.location.href = "/dashboard";
      } else {
        alert(response["error_msg"]);
      }
    },
  });
  return false;
}
