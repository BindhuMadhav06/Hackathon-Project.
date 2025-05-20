document.getElementById("saveBtn").addEventListener("click", async () => {
    const website = document.getElementById("website").value;
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    if (website && username && password) {
        // Save to Chrome Storage
        chrome.storage.sync.set({ [website]: { username, password } }, () => {
            console.log(`Saved credentials for ${website}`);
            alert("Credentials saved successfully!");
        });
    } else {
        alert("Please fill all fields!");
    }
});
