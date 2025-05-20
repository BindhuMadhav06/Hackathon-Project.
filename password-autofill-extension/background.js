chrome.runtime.onInstalled.addListener(() => {
    console.log('Password Manager Extension Installed');
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "getPassword") {
        console.log("Request to get password for:", message.website);

        fetch(`http://127.0.0.1:5000/get-password?website=${encodeURIComponent(message.website)}`)
            .then(response => response.json())
            .then(data => {
                console.log("Data from Flask:", data);
                sendResponse(data);
            })
            .catch(error => {
                console.error("Error fetching password:", error);
                sendResponse(null);
            });
        return true;
    }
});
