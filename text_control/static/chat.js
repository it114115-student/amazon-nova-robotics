// Flag to track if a request is in progress
let isRequestInProgress = false;

document.addEventListener("DOMContentLoaded", function () {
  // Make 'All' mutually exclusive in the multi-select
  const robotSelect = document.getElementById("robot-select");
  const summary = document.getElementById("selected-robots-summary");

  function updateSummary() {
    const selected = Array.from(robotSelect.selectedOptions).map((opt) => opt.text);
    summary.textContent = selected.length
      ? "Selected: " + selected.join(", ")
      : "No robot selected";
  }

  robotSelect.addEventListener("change", function (e) {
    const selected = Array.from(robotSelect.selectedOptions).map((opt) => opt.value);
    // If 'all' is selected, deselect all others
    if (selected.includes("all") && selected.length > 1) {
      for (const opt of robotSelect.options) {
        if (opt.value !== "all") opt.selected = false;
      }
    } else if (!selected.includes("all")) {
      // If any other is selected, ensure 'all' is not selected
      robotSelect.querySelector('option[value="all"]').selected = false;
    }
    updateSummary();
  });

  // Also update summary when modal closes
  const robotModal = document.getElementById("robotSelectModal");
  if (robotModal) {
    robotModal.addEventListener("hidden.bs.modal", updateSummary);
  }

  updateSummary();

  // Add event listener for Enter key
  document.getElementById("user-input").addEventListener("keydown", function (event) {
    if (event.key === "Enter") {
      event.preventDefault();
      sendMessage();
    }
  });

  // Add click event for send button
  document.getElementById("send-button").addEventListener("click", function () {
    sendMessage();
  });
});

async function sendMessage() {
  const userInput = document.getElementById("user-input");
  if (isRequestInProgress || !userInput.value.trim()) {
    return;
  }

  const robotSelect = document.getElementById("robot-select");
  const message = userInput.value;
  const selectedRobots = Array.from(robotSelect.selectedOptions).map((option) => option.value);

  isRequestInProgress = true;
  document.getElementById("loading").style.display = "block";
  document.getElementById("send-button").disabled = true;
  userInput.disabled = true;
  robotSelect.disabled = true;

  try {
    // Determine the correct API endpoint based on current URL
    const pathParts = window.location.pathname.split('/');
    const basePath = (pathParts.length > 1 && pathParts[1] === 'prod') ? '/prod' : '';
    let endPoint = basePath + "/api/chat";
    
    // Use authenticated request if authManager is available
    let response;
    if (window.authManager && window.authManager.getAuthToken()) {
      response = await window.authManager.makeAuthenticatedRequest(endPoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message,
          robots: selectedRobots,
          session_id: Math.floor(Math.random() * 1000000),
        }),
      });
    } else {
      // Fallback to regular request for non-authenticated endpoints
      response = await fetch(endPoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message,
          robots: selectedRobots,
          session_id: Math.floor(Math.random() * 1000000),
        }),
      });
    }
    
    const data = await response.json();
    const messagesDiv = document.getElementById("messages");

    // Add user message
    const userMessageElement = document.createElement("div");
    userMessageElement.className = "message user-message mb-2";
    userMessageElement.innerHTML = `<strong>You:</strong> ${message}`;
    messagesDiv.appendChild(userMessageElement);

    // Add bot message
    const botMessageElement = document.createElement("div");
    botMessageElement.className = "message bot-message mb-2";
    botMessageElement.innerHTML = `<strong>Bot:</strong> ${data.response}`;
    messagesDiv.appendChild(botMessageElement);

    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    userInput.value = "";
  } catch (error) {
    console.error("Error:", error);
    const messagesDiv = document.getElementById("messages");
    const userMessageElement = document.createElement("div");
    userMessageElement.className = "message user-message mb-2";
    userMessageElement.innerHTML = `<strong>You:</strong> ${message}`;
    messagesDiv.appendChild(userMessageElement);
    const errorMessageElement = document.createElement("div");
    errorMessageElement.className = "message system-message mb-2";
    errorMessageElement.innerHTML = `<strong>System:</strong> Sorry, there was an error processing your request.`;
    messagesDiv.appendChild(errorMessageElement);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
  } finally {
    isRequestInProgress = false;
    document.getElementById("loading").style.display = "none";
    document.getElementById("send-button").disabled = false;
    userInput.disabled = false;
    robotSelect.disabled = false;
    userInput.focus();
  }
}
