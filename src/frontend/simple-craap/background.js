/* Click the extension icon to POST the current tab URL to the local analyzer. */
chrome.action.onClicked.addListener(async (tab) => {
  const url = tab && tab.url;
  if (!url) {
    chrome.notifications.create({
      type: "basic",
      iconUrl: "icons/icon48.png",
      title: "Analyze URL",
      message: "No URL available."
    });
    return;
  }

  const endpoint = "http://localhost:10124/analyze/url?url=" + encodeURIComponent(url);

  try {
    const resp = await fetch(endpoint, { method: "POST" });
    const msg = resp.ok ? "URL sent successfully." : `Server responded: ${resp.status}`;
    chrome.notifications.create({
      type: "basic",
      iconUrl: "icons/icon48.png",
      title: "Analyze URL",
      message: msg
    });
  } catch (err) {
    chrome.notifications.create({
      type: "basic",
      iconUrl: "icons/icon48.png",
      title: "Analyze URL",
      message: "Network error: " + (err && err.message ? err.message : String(err))
    });
  }
});