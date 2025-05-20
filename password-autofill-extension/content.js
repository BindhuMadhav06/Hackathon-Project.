window.addEventListener("load", () => {
    console.log("Autofill extension loaded");

    const currentWebsite = window.location.hostname;
    console.log(`Current website: ${currentWebsite}`);

    chrome.runtime.sendMessage(
        { action: "getPassword", website: currentWebsite },
        (response) => {
            if (response && response.username && response.password) {
                console.log(`Autofilling credentials for ${currentWebsite}`);
                
                // Find input fields
                const usernameField = document.querySelector("input[type='text'], input[name*='user']");
                const passwordField = document.querySelector("input[type='password'], input[name*='pass']");
                
                if (usernameField && passwordField) {
                    usernameField.value = response.username;
                    passwordField.value = response.password;
                    console.log("Autofill successful");
                } else {
                    console.log("No suitable input fields found");
                }
            } else {
                console.log("No saved credentials for this website");
            }
        }
    );
});
