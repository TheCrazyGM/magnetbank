fetch(
  "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_best.txt"
)
  .then((response) => response.text())
  .then((text) => {
    const trackers = text
      .split("\n")
      .filter((line) => line.trim() !== "")
      .join("&tr=");
    document.querySelectorAll('a[href^="magnet:?"]').forEach((link) => {
      const href = link.getAttribute("href") + "&tr=" + trackers;
      link.setAttribute("href", href);
    });
  })
  .catch((error) => console.log("Error fetching trackers:", error));
