/**
 * Live2D Speaking Avatar Integration Helper
 * Utilizing PIXI.js, pixi-live2d-display, and Web Audio API
 */

// Bind PIXI globally so that pixi-live2d-display can discover it under ES module scopes
if (typeof window !== "undefined" && typeof PIXI !== "undefined") {
  window.PIXI = PIXI;
}

const MOUTH_PARAMETER_IDS = [
  "ParamMouthOpenY",
  "PARAM_MOUTH_OPEN_Y",
  "ParamMouthOpen",
  "PARAM_MOUTH_OPEN",
  "ParamA",
];

function applyMouthValue(model, value) {
  const core = model?.internalModel?.coreModel || model?.internalModel?.live2DModel;
  if (!core) {
    return false;
  }

  let applied = false;

  for (const parameterId of MOUTH_PARAMETER_IDS) {
    try {
      if (typeof core.setParameterValueById === "function") {
        core.setParameterValueById(parameterId, value);
        applied = true;
      }

      if (typeof core.setParameterValue === "function") {
        core.setParameterValue(parameterId, value);
        applied = true;
      }

      if (typeof core.setParamFloat === "function") {
        core.setParamFloat(parameterId, value);
        applied = true;
      }

      if (
        typeof core.getParameterIndex === "function" &&
        typeof core.setParameterValueByIndex === "function"
      ) {
        const index = core.getParameterIndex(parameterId);
        if (index >= 0) {
          core.setParameterValueByIndex(index, value);
          applied = true;
        }
      }
    } catch (_error) {
      // Try the next supported parameter API/ID combination.
    }
  }

  return applied;
}

function fitModelToCanvas(model, canvasWidth, canvasHeight, scaleMultiplier, offsetY) {
  const bounds = typeof model.getLocalBounds === "function"
    ? model.getLocalBounds()
    : { x: 0, y: 0, width: model.width || canvasWidth, height: model.height || canvasHeight };

  const safeWidth = Math.max(bounds.width || 0, 1);
  const safeHeight = Math.max(bounds.height || 0, 1);
  const scale = Math.min(canvasWidth / safeWidth, canvasHeight / safeHeight) * scaleMultiplier;

  model.scale.set(scale);

  if (model.anchor && typeof model.anchor.set === "function") {
    model.anchor.set(0.5, 1);
    model.x = canvasWidth / 2;
    model.y = canvasHeight + offsetY;
    return;
  }

  const scaledBounds = typeof model.getLocalBounds === "function"
    ? model.getLocalBounds()
    : bounds;
  model.x = canvasWidth / 2 - (scaledBounds.x + scaledBounds.width / 2) * scale;
  model.y = canvasHeight - (scaledBounds.y + scaledBounds.height) * scale + offsetY;
}

export async function initLive2DAvatar(audioPlayer) {
  console.log("🎬 Initializing Dual Live2D Speaking Avatars...");

  const models = [
    {
      id: "left",
      canvasId: "live2d-left",
      url: "https://cdn.jsdelivr.net/npm/live2d-widget-model-shizuku@latest/assets/shizuku.model.json",
      scale: 0.9,
      offsetY: 20
    },
    {
      id: "right",
      canvasId: "live2d-right",
      url: "https://cdn.jsdelivr.net/npm/live2d-widget-model-chitose@latest/assets/chitose.model.json",
      scale: 0.85,
      offsetY: 40
    }
  ];

  const instances = {};

  for (const modelConfig of models) {
    const canvas = document.getElementById(modelConfig.canvasId);
    if (!canvas) {
      console.warn(`❌ Canvas ${modelConfig.canvasId} not found!`);
      continue;
    }

    try {
      const app = new PIXI.Application({
        view: canvas,
        transparent: true,
        backgroundAlpha: 0,
        autoStart: true,
        antialias: true,
        width: 320,
        height: 400,
      });

      console.log(`📡 Loading model: ${modelConfig.id}...`);
      const model = await PIXI.live2d.Live2DModel.from(modelConfig.url);
      app.stage.addChild(model);

      // Scale and position with Cubism 2-safe bounds handling.
      fitModelToCanvas(model, 320, 400, modelConfig.scale, modelConfig.offsetY);

      instances[modelConfig.id] = { model, canvas };

      // Mouth Sync Hook
      let smoothedVolume = 0;
      const originalInternalUpdate = model.internalModel.update;
      model.internalModel.update = function() {
        originalInternalUpdate.apply(this, arguments);
        
        // Only sync mouth if this character is currently focused/speaking
        const slot = canvas.closest('.character-slot');
        const isActive = slot.classList.contains('active');
        const isUser = slot.id === 'char-right';
        
        let rawVolume = 0;
        if (isActive) {
          rawVolume = isUser ? (audioPlayer ? audioPlayer.getInputVolume() : 0) : (audioPlayer ? audioPlayer.getVolume() : 0);
        }
        
        const targetMouthOpen = Math.min(rawVolume * 15.0, 1.0);
        smoothedVolume += (targetMouthOpen - smoothedVolume) * 0.35;
        applyMouthValue(model, smoothedVolume);
      };

      console.log(`🟢 ${modelConfig.id} model loaded!`);
    } catch (err) {
      console.error(`⚠️ Failed to load ${modelConfig.id}:`, err);
    }
  }

  // Global mouse follow
  window.addEventListener("mousemove", (event) => {
    Object.values(instances).forEach(({ model }) => {
      if (model && typeof model.focus === "function") {
        model.focus(event.clientX, event.clientY);
      }
    });
  });

  return instances;
}
