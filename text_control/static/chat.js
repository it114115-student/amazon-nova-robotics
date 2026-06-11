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

    // Helper function to deselect specific options
    function deselectOptions(valuesToDeselect) {
      valuesToDeselect.forEach(value => {
        const option = robotSelect.querySelector(`option[value="${value}"]`);
        if (option) option.selected = false;
      });
    }

    // If 'all' is selected, it should be mutually exclusive with everything else
    if (selected.includes("all") && selected.length > 1) {
      for (const opt of robotSelect.options) {
        if (opt.value !== "all") opt.selected = false;
      }
    }
    // If any group selector is chosen, handle conflicts
    else {
      // If 'all_robots' is selected with individual robots or 'all', deselect conflicts
      if (selected.includes("all_robots")) {
        const conflicts = selected.filter(val => val.startsWith("robot_") || val === "all");
        if (conflicts.length > 0) {
          deselectOptions(conflicts);
        }
      }

      // If 'all_drones' is selected with individual drones or 'all', deselect conflicts  
      if (selected.includes("all_drones")) {
        const conflicts = selected.filter(val => val.startsWith("drone_") || val === "all");
        if (conflicts.length > 0) {
          deselectOptions(conflicts);
        }
      }

      // If individual items are selected, deselect their corresponding 'all_*' and 'all'
      if (selected.some(val => val.startsWith("robot_"))) {
        deselectOptions(["all_robots", "all"]);
      }
      if (selected.some(val => val.startsWith("drone_"))) {
        deselectOptions(["all_drones", "all"]);
      }

      // If xiaoice is selected, deselect 'all'
      if (selected.some(val => val.startsWith("xiaoice_"))) {
        deselectOptions(["all"]);
      }
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

  // Add click event for New Chat button
  const newChatBtn = document.getElementById("new-chat-btn");
  if (newChatBtn) {
    newChatBtn.addEventListener("click", function () {
      startNewChat();
    });
  }
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
          session_id: getOrCreateSessionId(),
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
          session_id: getOrCreateSessionId(),
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

    // Add bot message — render captured images
    const botMessageElement = document.createElement("div");
    botMessageElement.className = "message bot-message mb-2";
    const botText = data.response;

    // Check for image_key in response (from get_image MCP tool)
    const imageKeyMatch = botText.match(/image_key=(\S+)/);
    if (imageKeyMatch) {
      const imageKey = imageKeyMatch[1];
      const displayText = botText.replace(/image_key=\S+/, "").replace(/image_url=\S+/g, "").trim();
      botMessageElement.innerHTML = `<strong>Bot:</strong> ${displayText}<br><span class="text-muted small">Loading image...</span>`;
      messagesDiv.appendChild(botMessageElement);

      // Fetch presigned URL from our proxy endpoint
      const pathParts = window.location.pathname.split('/');
      const basePath = (pathParts.length > 1 && pathParts[1] === 'prod') ? '/prod' : '';
      const imageApiUrl = basePath + "/api/image/" + encodeURIComponent(imageKey);

      try {
        let imgResp;
        if (window.authManager && window.authManager.getAuthToken()) {
          imgResp = await window.authManager.makeAuthenticatedRequest(imageApiUrl);
        } else {
          imgResp = await fetch(imageApiUrl);
        }
        const imgData = await imgResp.json();
        if (imgData.image_url) {
          botMessageElement.innerHTML = `<strong>Bot:</strong> ${displayText}<br><a href="${imgData.image_url}" target="_blank" rel="noopener noreferrer"><img src="${imgData.image_url}" alt="Robot captured image" style="max-width:100%;max-height:300px;border-radius:8px;margin-top:8px;" /></a>`;
        }
      } catch (imgErr) {
        console.error("Failed to load image:", imgErr);
      }
    } else {
      // Detect S3 presigned URLs and render appropriately:
      //  - URLs with "speech-audio/" in the path → <audio> player
      //  - Other S3 URLs → <img> tag
      //  - Also handle explicit audio_url= prefix from MCP tool responses

      // Pattern to match any S3 presigned URL
      const s3UrlPattern = /(https:\/\/[^\s"'<>]+\.s3[^\s"'<>]*\.amazonaws\.com[^\s"'<>]*)/gi;
      const allUrls = botText.match(s3UrlPattern) || [];

      // Also catch audio_url=<url> where URL might not be S3
      const audioUrlPrefixMatch = botText.match(/audio_url=(https?:\/\/[^\s"'<>]+)/);
      if (audioUrlPrefixMatch && !allUrls.includes(audioUrlPrefixMatch[1])) {
        allUrls.push(audioUrlPrefixMatch[1]);
      }

      if (allUrls.length > 0) {
        // Separate audio vs image URLs
        const audioUrls = allUrls.filter(u => u.includes('speech-audio') || u.includes('.mp3') || u.includes('.ogg'));
        const imageUrls = allUrls.filter(u => !audioUrls.includes(u));

        // Strip all matched URLs and the audio_url= prefix from display text
        let displayText = botText;
        for (const url of allUrls) {
          displayText = displayText.replace(url, '');
        }
        displayText = displayText.replace(/audio_url=\s*/g, '').replace(/image_url=\s*/g, '').trim();

        let html = `<strong>Bot:</strong> ${displayText}`;

        // Render audio players
        for (const url of audioUrls) {
          html += `<br><audio controls preload="auto" style="width:100%;margin-top:8px;border-radius:8px;"><source src="${url}" type="audio/mpeg">Your browser does not support audio.</audio>`;
        }

        // Render images
        for (const url of imageUrls) {
          html += `<br><a href="${url}" target="_blank" rel="noopener noreferrer"><img src="${url}" alt="Robot captured image" style="max-width:100%;max-height:300px;border-radius:8px;margin-top:8px;" /></a>`;
        }

        botMessageElement.innerHTML = html;
      } else {
        botMessageElement.innerHTML = `<strong>Bot:</strong> ${botText}`;
      }
      messagesDiv.appendChild(botMessageElement);
    }
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

function getOrCreateSessionId() {
  let sessionId = localStorage.getItem("robot_session_id");
  if (!sessionId) {
    sessionId = typeof crypto.randomUUID === "function" ? crypto.randomUUID() : Math.floor(Math.random() * 1e16).toString();
    localStorage.setItem("robot_session_id", sessionId);
  }
  return sessionId;
}

function startNewChat() {
  const newSessionId = typeof crypto.randomUUID === "function" ? crypto.randomUUID() : Math.floor(Math.random() * 1e16).toString();
  localStorage.setItem("robot_session_id", newSessionId);
  const messagesDiv = document.getElementById("messages");
  if (messagesDiv) {
    messagesDiv.innerHTML = '<div class="message system-message mb-2 text-center text-muted small"><em>已開始新的對話。</em></div>';
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
  }
  const userInput = document.getElementById("user-input");
  if (userInput) {
    userInput.value = "";
    userInput.disabled = false;
    userInput.focus();
  }
  const sendButton = document.getElementById("send-button");
  if (sendButton) {
    sendButton.disabled = false;
  }
  const robotSelect = document.getElementById("robot-select");
  if (robotSelect) {
    robotSelect.disabled = false;
  }
  isRequestInProgress = false;
  document.getElementById("loading").style.display = "none";
}

