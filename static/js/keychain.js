// Send Custom JSON request
$("#send_custom").on("click", () => {
  try {
    const customJson = JSON.parse($("#custom_json").val()); // convert to JSON object
    const jsonifiedCustomJson = JSON.stringify(customJson); // convert to JSON string
    hive_keychain.requestCustomJson(
      $("#custom_username").val(),
      "MagnetBank",
      "Posting",
      jsonifiedCustomJson, // use the JSON string
      "New Magnet Link",
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
