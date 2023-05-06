let signatureSent = false; // flag to indicate if signature was sent successfully

// Function to create a cookie
function createCookie(name, value, days) {
  let expires;
  if (days) {
    const date = new Date();
    date.setTime(date.getTime() + days * 24 * 60 * 60 * 1000);
    expires = "; expires=" + date.toGMTString();
  } else {
    expires = "";
  }
  document.cookie = name + "=" + value + expires + "; path=/";
}

// Function to get a cookie
function getCookie(name) {
  const nameEQ = name + "=";
  const ca = document.cookie.split(";");
  for (let i = 0; i < ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) == " ") {
      c = c.substring(1, c.length);
    }
    if (c.indexOf(nameEQ) == 0) {
      return c.substring(nameEQ.length, c.length);
    }
  }
  return null;
}

// Function to check if the signature has been sent successfully and show the admin form
function checkSignatureStatus() {
  if (getCookie("signatureSent") == "true") {
    $("#admin_form").show();
    $("#send_signature").hide();
  }
}

$("#send_signature").click(function () {
  hive_keychain.requestSignBuffer(
    $("#username").val().length ? $("#username").val() : null,
    "Admin Panel",
    "Active",
    function (response) {
      console.log("sign");
      console.log(response);
      signatureSent = true; // set flag to true on successful signature
      createCookie("signatureSent", true, 1); // create the cookie
      checkSignatureStatus(); // check the signature status and show the admin form
    },
    null,
    "Signature"
  );
});

// Update custom_json textarea with JSONified data
function updateCustomJson() {
  const action = $("#custom_action").val();
  const hash = $("#hash").val();
  const category = $("#category").val();
  const customJson = JSON.stringify({ action, hash, category });
  $("#custom_json").val(customJson);
}

// Add event listeners to input fields
$("#custom_action").on("change", updateCustomJson);
$("#hash").on("input", updateCustomJson);
$("#category").on("input", updateCustomJson);

// Send Custom JSON request
$("#send_custom").on("click", function () {
  try {
    const customJson = JSON.parse($("#custom_json").val()); // convert to JSON object
    const jsonifiedCustomJson = JSON.stringify(customJson); // convert to JSON string
    hive_keychain.requestCustomJson(
      $("#username").val(),
      "MagnetBank",
      "Posting",
      jsonifiedCustomJson, // use the JSON string
      "Admin Changes",
      function (response) {
        console.log(response);
        $("#msg")
          .removeClass("alert-danger")
          .addClass("alert-success")
          .text(response.message);
      }
    );
  } catch (error) {
    console.error(error);
    $("#msg")
      .removeClass("alert-success")
      .addClass("alert-danger")
      .text("Error: " + error.message);
  }
});

// Hide admin form initially
$("#admin_form").hide();

// Check the signature status and show the admin form
checkSignatureStatus();
