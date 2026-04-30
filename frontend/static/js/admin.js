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
    $("#admin_panel").removeClass("d-none");
    $("#login_panel").addClass("d-none");
  }
};

$("#send_signature").click(() => {
  const username = $("#username").val();
  if (window.hive_keychain) {
    hive_keychain.requestSignBuffer(
      username || null,
      "Admin Panel Authentication",
      "Active",
      (response) => {
        if (response.success) {
          createCookie("signatureSent", "true", 1);
          checkSignatureStatus();
        } else {
          alert("Signature failed: " + response.message);
        }
      },
      null,
      "Signature"
    );
  } else {
    alert("Hive Keychain not found!");
  }
});

// Update custom_json textarea with JSONified data
const updateCustomJson = () => {
  const action = $("#action").val();
  const customJson = {
    action: action,
    hash: $("#hash").val().toUpperCase(),
  };

  if (action === "update") {
    customJson.category = $("#category").val();
  }

  $("#custom_json").val(JSON.stringify(customJson, null, 2));
};

// Add event listeners to input fields
$("#action, #hash, #category").on("input change", updateCustomJson);

// Send Custom JSON request
$("#send_custom").on("click", () => {
  const username = $("#username").val();
  const jsonStr = $("#custom_json").val();

  if (window.hive_keychain) {
    hive_keychain.requestCustomJson(
      username,
      "MagnetBank",
      "Posting",
      jsonStr,
      "Admin Action: " + $("#action").val(),
      (response) => {
        console.log(response);
        const msgPanel = $("#msg_panel");
        msgPanel.removeClass("d-none");
        $("#msg_text").text(response.message || (response.success ? "Success" : "Failed"));
      }
    );
  } else {
    alert("Hive Keychain not found!");
  }
});

// Check the signature status on load
checkSignatureStatus();
updateCustomJson();
