const signatureSent = false; // flag to indicate if signature was sent successfully

// Function to create a cookie
const createCookie = (name, value, days) => {
  const expires = days
    ? `; expires=${new Date(
        Date.now() + days * 24 * 60 * 60 * 1000
      ).toGMTString()}`
    : "";
  document.cookie = `${name}=${value}${expires}; path=/`;
};

// Function to get a cookie
const getCookie = (name) => {
  const nameEQ = `${name}=`;
  const ca = document.cookie.split(";");
  for (const c of ca) {
    let trimmed = c.trim();
    if (trimmed.startsWith(nameEQ)) {
      return trimmed.substring(nameEQ.length);
    }
  }
  return null;
};

// Function to check if the signature has been sent successfully and show the admin form
const checkSignatureStatus = () => {
  if (getCookie("signatureSent")?.toLowerCase() === "true") {
    $("#admin_form").show();
    $("#send_signature").hide();
  }
};

$("#send_signature").click(() => {
  hive_keychain.requestSignBuffer(
    $("#username").val() || null,
    "Admin Panel",
    "Active",
    (response) => {
      console.log("sign", response);
      createCookie("signatureSent", true, 1); // create the cookie
      checkSignatureStatus(); // check the signature status and show the admin form
    },
    null,
    "Signature"
  );
});

// Update custom_json textarea with JSONified data
const updateCustomJson = () => {
  const customJson = {
    custom_action: $("#custom_action").val(),
    hash: $("#hash").val(),
    category: $("#category").val(),
  };
  $("#custom_json").val(JSON.stringify(customJson));
};
// Add event listeners to input fields
$("#custom_action, #hash, #category").on("input", updateCustomJson);

// Send Custom JSON request
$("#send_custom").on("click", () => {
  try {
    const customJson = JSON.parse($("#custom_json").val());
    hive_keychain.requestCustomJson(
      $("#username").val(),
      "MagnetBank",
      "Posting",
      JSON.stringify(customJson),
      "Admin Changes",
      (response) => {
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
      .text(`Error: ${error.message}`);
  }
});

// Hide admin form initially
$("#admin_form").hide();

// Check the signature status and show the admin form
checkSignatureStatus();
