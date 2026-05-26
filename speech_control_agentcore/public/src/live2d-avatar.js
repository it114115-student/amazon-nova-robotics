/**
 * Live2D Speaking Avatar Integration Helper
 * Utilizing PIXI.js, pixi-live2d-display, and Web Audio API
 */

// Bind PIXI globally so that pixi-live2d-display can discover it under ES module scopes
if (typeof window !== "undefined" && typeof PIXI !== "undefined") {
  window.PIXI = PIXI;
}

export async function initLive2DAvatar(audioPlayer) {
  console.log("🎬 Initializing Live2D Speaking Avatar...");

  const canvas = document.getElementById("live2d-canvas");
  const orb = document.getElementById("voice-orb");

  if (!canvas) {
    console.error("❌ Live2D canvas element not found!");
    return;
  }

  // Model URL (extremely stable, npm-backed public CDN link for Shizuku)
  const MODEL_URL = "https://cdn.jsdelivr.net/npm/live2d-widget-model-shizuku@latest/assets/shizuku.model.json";

  try {
    // 1. Setup PIXI Application with high resolution
    const app = new PIXI.Application({
      view: canvas,
      transparent: true, // Standard transparency configuration for PixiJS v5/v6
      backgroundAlpha: 0, // Standard transparency configuration for PixiJS v7/v8
      autoStart: true,
      antialias: true,
      width: 320,
      height: 320,
    });

    // 🛡️ Unified Event Polyfill: Bridge PixiJS v7/v8's new EventSystem onto the legacy InteractionManager property
    if (app.renderer && app.renderer.plugins) {
      if (!app.renderer.plugins.interaction && app.renderer.events) {
        app.renderer.plugins.interaction = app.renderer.events;
      }
    }

    console.log("📡 Downloading and loading Live2D model...");
    // 2. Load the Live2D model
    const model = await PIXI.live2d.Live2DModel.from(MODEL_URL);
    app.stage.addChild(model);

    // 3. Scale and Position the Model to fit nicely at 320px
    const scaleX = 320 / model.width;
    const scaleY = 320 / model.height;
    const finalScale = Math.min(scaleX, scaleY) * 0.90; // leave 10% padding
    model.scale.set(finalScale);

    // Center model inside canvas
    model.x = (320 - model.width) / 2;
    model.y = (320 - model.height) / 2 + 10; // offset down slightly

    // 4. Hide static Voice Orb and Display Live2D Canvas
    if (orb) {
      orb.style.display = "none";
    }
    canvas.style.display = "block";
    console.log("🟢 Live2D model loaded successfully!");

    // 5. Cursor Tracking Hook
    // Make head and eyes follow mouse cursor when moved on screen
    window.addEventListener("mousemove", (event) => {
      if (model && typeof model.focus === "function") {
        model.focus(event.clientX, event.clientY);
      }
    });

    // 6. Real-time Lip Sync (Hooked directly into internalModel's update cycle to ensure manual values override internal motions)
    let smoothedVolume = 0;
    let isTestingMouth = false;
    let testSpeakingTimeout = null;
    let lastLogTime = 0;

    // Manual Click Test: Click/Tap on her to verify mouth animation rendering instantly!
    canvas.addEventListener("click", () => {
      console.log("👆 Live2D Canvas clicked! Triggering 3-second mouth movement test...");
      isTestingMouth = true;
      
      if (testSpeakingTimeout) {
        clearTimeout(testSpeakingTimeout);
      }

      testSpeakingTimeout = setTimeout(() => {
        isTestingMouth = false;
        smoothedVolume = 0;
        console.log("⏹️ Live2D mouth movement test completed.");
      }, 3000);
    });

    const originalInternalUpdate = model.internalModel.update;
    model.internalModel.update = function() {
      // Run the original update first to let the standard animations and physics execute
      originalInternalUpdate.apply(this, arguments);

      if (isTestingMouth) {
        // Generate a smooth oscillating speaking wave (0 to 1) for the manual click test
        const elapsed = Date.now();
        const testOpenValue = 0.5 + 0.5 * Math.sin(elapsed * 0.02);
        smoothedVolume = testOpenValue;
      } else {
        // Fetch dynamic root-mean-square volume from the active AudioPlayer
        const rawVolume = audioPlayer ? audioPlayer.getVolume() : 0;

        // Map volume to mouth opening (Conversational RMS averages ~0.02 - 0.10, so we scale it by 12.0 to make movement clearly visible)
        const targetMouthOpen = Math.min(rawVolume * 12.0, 1.0);

        // Linear Interpolation (lerp) for smooth movements
        smoothedVolume += (targetMouthOpen - smoothedVolume) * 0.35;

        // Throttled debug log to verify mouth sync in the browser console
        const now = Date.now();
        if (rawVolume > 0 && (now - lastLogTime > 1000)) {
          console.log(`[Live2D Mouth Sync Debug] rawVolume=${rawVolume.toFixed(4)}, targetMouthOpen=${targetMouthOpen.toFixed(4)}, smoothedVolume=${smoothedVolume.toFixed(4)}`);
          lastLogTime = now;
        }
      }

      // Inject the smoothed mouth parameter right after the standard motion calculations
      const core = model.internalModel.coreModel;
      if (core) {
        if (typeof core.setParameterValue === "function") {
          core.setParameterValue("ParamMouthOpenY", smoothedVolume);
          core.setParameterValue("PARAM_MOUTH_OPEN_Y", smoothedVolume);
        } else if (typeof core.setParamFloat === "function") {
          core.setParamFloat("ParamMouthOpenY", smoothedVolume);
          core.setParamFloat("PARAM_MOUTH_OPEN_Y", smoothedVolume);
        } else if (typeof core.setValue === "function") {
          // Fallback support for generic setValue method
          core.setValue("ParamMouthOpenY", smoothedVolume);
          core.setValue("PARAM_MOUTH_OPEN_Y", smoothedVolume);
        }
      }
    };

  } catch (error) {
    console.error("⚠️ Failed to load Live2D avatar. Falling back to glowing Voice Orb.", error);
    canvas.style.display = "none";
    if (orb) {
      orb.style.display = "flex";
    }
  }
}
