fetch("/api/announce_urls")
  .then((response) => response.json()) // Parse response as JSON
  .then((data) => {
    const trackers = data.filter((line) => line.trim() !== "").join("&tr=");
    document.querySelectorAll('a[href^="magnet:?"]').forEach((link) => {
      const href = link.getAttribute("href") + "&tr=" + trackers;
      link.setAttribute("href", href);
    });
  })
  .catch((error) => console.log("Error fetching trackers:", error));
