// Calls the Flask API (service worker avoids mixed-content/CORS problems)
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  fetch("http://localhost:5000/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ html: msg.html })
  })
    .then(r => r.json())
    .then(sendResponse)
    .catch(() => sendResponse({ failed: true }));
  return true; // keep channel open for async response
});
