// Modal popup for robot selection with mobile-friendly checkboxes and multi-select shortcuts
export function setupRobotModal() {
  const controls = document.getElementById('controls');
  // Create modal elements
  const modal = document.createElement('div');
  modal.id = 'robot-modal';
  modal.className = 'modal';
  modal.innerHTML = `
    <div class="modal-content" style="max-width: 400px; width: 90%;">
      <span class="close" id="close-robot-modal">&times;</span>
      <h2 style="margin-bottom: 16px; font-size: 1.4rem;">Select Active Devices</h2>
      
      <div class="checkbox-container" style="text-align: left; max-height: 380px; overflow-y: auto; padding: 12px; background: #1a1a1a; border: 1px solid #444; border-radius: 8px; margin-bottom: 18px; box-sizing: border-box;">
        
        <!-- shortcuts category -->
        <div class="category-section" style="margin-bottom: 16px;">
          <div class="category-header" style="font-weight: bold; color: #646cff; border-bottom: 1px solid #333; margin-bottom: 10px; padding-bottom: 4px; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.5px;">Shortcuts</div>
          <label style="display: flex; align-items: center; margin: 8px 0; cursor: pointer; font-size: 0.95rem; user-select: none;">
            <input type="checkbox" value="all" class="robot-checkbox" id="cb-all" style="margin-right: 10px; width: 16px; height: 16px; cursor: pointer;" checked /> <strong>All (Robots + Drones + Dogs)</strong>
          </label>
          <label style="display: flex; align-items: center; margin: 8px 0; cursor: pointer; font-size: 0.95rem; user-select: none;">
            <input type="checkbox" value="all_robots" class="robot-checkbox" id="cb-all-robots" style="margin-right: 10px; width: 16px; height: 16px; cursor: pointer;" checked /> All Robots (1 - 6)
          </label>
          <label style="display: flex; align-items: center; margin: 8px 0; cursor: pointer; font-size: 0.95rem; user-select: none;">
            <input type="checkbox" value="all_drones" class="robot-checkbox" id="cb-all-drones" style="margin-right: 10px; width: 16px; height: 16px; cursor: pointer;" checked /> All Drones (1 - 2)
          </label>
          <label style="display: flex; align-items: center; margin: 8px 0; cursor: pointer; font-size: 0.95rem; user-select: none;">
            <input type="checkbox" value="all_dogs" class="robot-checkbox" id="cb-all-dogs" style="margin-right: 10px; width: 16px; height: 16px; cursor: pointer;" checked /> All Dogs (1 - 3)
          </label>
        </div>

        <!-- robots category -->
        <div class="category-section" style="margin-bottom: 16px;">
          <div class="category-header" style="font-weight: bold; color: #646cff; border-bottom: 1px solid #333; margin-bottom: 10px; padding-bottom: 4px; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.5px;">Humanoid Robots</div>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
            <label style="display: flex; align-items: center; cursor: pointer; font-size: 0.9rem; user-select: none;"><input type="checkbox" value="robot_1" class="robot-checkbox device-cb group-robots" style="margin-right: 8px; width: 14px; height: 14px;" checked /> Robot 1</label>
            <label style="display: flex; align-items: center; cursor: pointer; font-size: 0.9rem; user-select: none;"><input type="checkbox" value="robot_2" class="robot-checkbox device-cb group-robots" style="margin-right: 8px; width: 14px; height: 14px;" checked /> Robot 2</label>
            <label style="display: flex; align-items: center; cursor: pointer; font-size: 0.9rem; user-select: none;"><input type="checkbox" value="robot_3" class="robot-checkbox device-cb group-robots" style="margin-right: 8px; width: 14px; height: 14px;" checked /> Robot 3</label>
            <label style="display: flex; align-items: center; cursor: pointer; font-size: 0.9rem; user-select: none;"><input type="checkbox" value="robot_4" class="robot-checkbox device-cb group-robots" style="margin-right: 8px; width: 14px; height: 14px;" checked /> Robot 4</label>
            <label style="display: flex; align-items: center; cursor: pointer; font-size: 0.9rem; user-select: none;"><input type="checkbox" value="robot_5" class="robot-checkbox device-cb group-robots" style="margin-right: 8px; width: 14px; height: 14px;" checked /> Robot 5</label>
            <label style="display: flex; align-items: center; cursor: pointer; font-size: 0.9rem; user-select: none;"><input type="checkbox" value="robot_6" class="robot-checkbox device-cb group-robots" style="margin-right: 8px; width: 14px; height: 14px;" checked /> Robot 6</label>
          </div>
        </div>

        <!-- drones category -->
        <div class="category-section" style="margin-bottom: 16px;">
          <div class="category-header" style="font-weight: bold; color: #646cff; border-bottom: 1px solid #333; margin-bottom: 10px; padding-bottom: 4px; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.5px;">Drones</div>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
            <label style="display: flex; align-items: center; cursor: pointer; font-size: 0.9rem; user-select: none;"><input type="checkbox" value="drone_1" class="robot-checkbox device-cb group-drones" style="margin-right: 8px; width: 14px; height: 14px;" checked /> Drone 1</label>
            <label style="display: flex; align-items: center; cursor: pointer; font-size: 0.9rem; user-select: none;"><input type="checkbox" value="drone_2" class="robot-checkbox device-cb group-drones" style="margin-right: 8px; width: 14px; height: 14px;" checked /> Drone 2</label>
          </div>
        </div>

        <!-- dogs category -->
        <div class="category-section" style="margin-bottom: 16px;">
          <div class="category-header" style="font-weight: bold; color: #646cff; border-bottom: 1px solid #333; margin-bottom: 10px; padding-bottom: 4px; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.5px;">Robotic Dogs</div>
          <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px;">
            <label style="display: flex; align-items: center; cursor: pointer; font-size: 0.9rem; user-select: none;"><input type="checkbox" value="dog_1" class="robot-checkbox device-cb group-dogs" style="margin-right: 8px; width: 14px; height: 14px;" checked /> Dog 1</label>
            <label style="display: flex; align-items: center; cursor: pointer; font-size: 0.9rem; user-select: none;"><input type="checkbox" value="dog_2" class="robot-checkbox device-cb group-dogs" style="margin-right: 8px; width: 14px; height: 14px;" checked /> Dog 2</label>
            <label style="display: flex; align-items: center; cursor: pointer; font-size: 0.9rem; user-select: none;"><input type="checkbox" value="dog_3" class="robot-checkbox device-cb group-dogs" style="margin-right: 8px; width: 14px; height: 14px;" checked /> Dog 3</label>
          </div>
        </div>

        <!-- xiaoice category -->
        <div class="category-section">
          <div class="category-header" style="font-weight: bold; color: #646cff; border-bottom: 1px solid #333; margin-bottom: 10px; padding-bottom: 4px; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.5px;">Digital Human</div>
          <label style="display: flex; align-items: center; cursor: pointer; font-size: 0.9rem; user-select: none;"><input type="checkbox" value="xiaoice_1" class="robot-checkbox device-cb group-xiaoice" style="margin-right: 8px; width: 14px; height: 14px;" checked /> Xiaoice 1</label>
        </div>
      </div>
      
      <button id="robot-modal-save" style="width: 100%; font-weight: bold; padding: 12px; border-radius: 6px;">Apply Selection</button>
    </div>
  `;
  document.body.appendChild(modal);

  // Add open button
  const openBtn = document.createElement('button');
  openBtn.id = 'open-robot-modal';
  openBtn.textContent = 'Select Robot(s)';
  controls.insertBefore(openBtn, controls.firstChild);

  // Hide the old selector
  const robotSelector = document.getElementById('robot-selector');
  if (robotSelector) robotSelector.style.display = 'none';

  // Modal open/close logic
  openBtn.onclick = () => { modal.style.display = 'block'; };
  document.getElementById('close-robot-modal').onclick = () => { modal.style.display = 'none'; };

  // Setup reactive syncing for shortcuts and child checkboxes
  const cbAll = document.getElementById('cb-all');
  const cbAllRobots = document.getElementById('cb-all-robots');
  const cbAllDrones = document.getElementById('cb-all-drones');
  const cbAllDogs = document.getElementById('cb-all-dogs');

  const robotCbs = document.querySelectorAll('.group-robots');
  const droneCbs = document.querySelectorAll('.group-drones');
  const dogCbs = document.querySelectorAll('.group-dogs');
  const deviceCbs = document.querySelectorAll('.device-cb');

  // Shortcut 1: All (Robots + Drones + Dogs)
  cbAll.addEventListener('change', () => {
    const isChecked = cbAll.checked;
    cbAllRobots.checked = isChecked;
    cbAllDrones.checked = isChecked;
    cbAllDogs.checked = isChecked;
    deviceCbs.forEach(cb => cb.checked = isChecked);
  });

  // Shortcut 2: All Robots (1 - 6)
  cbAllRobots.addEventListener('change', () => {
    const isChecked = cbAllRobots.checked;
    robotCbs.forEach(cb => cb.checked = isChecked);
    updateAllShortcutState();
  });

  // Shortcut 3: All Drones (1 - 2)
  cbAllDrones.addEventListener('change', () => {
    const isChecked = cbAllDrones.checked;
    droneCbs.forEach(cb => cb.checked = isChecked);
    updateAllShortcutState();
  });

  // Shortcut 4: All Dogs (1 - 3)
  cbAllDogs.addEventListener('change', () => {
    const isChecked = cbAllDogs.checked;
    dogCbs.forEach(cb => cb.checked = isChecked);
    updateAllShortcutState();
  });

  // Child changes: Sync back to parent shortcuts
  robotCbs.forEach(cb => {
    cb.addEventListener('change', () => {
      const allChecked = Array.from(robotCbs).every(c => c.checked);
      cbAllRobots.checked = allChecked;
      updateAllShortcutState();
    });
  });

  droneCbs.forEach(cb => {
    cb.addEventListener('change', () => {
      const allChecked = Array.from(droneCbs).every(c => c.checked);
      cbAllDrones.checked = allChecked;
      updateAllShortcutState();
    });
  });

  dogCbs.forEach(cb => {
    cb.addEventListener('change', () => {
      const allChecked = Array.from(dogCbs).every(c => c.checked);
      cbAllDogs.checked = allChecked;
      updateAllShortcutState();
    });
  });

  function updateAllShortcutState() {
    const allDevicesChecked = Array.from(deviceCbs).every(c => c.checked);
    cbAll.checked = allDevicesChecked;
  }

  // Save / Apply selections back to hidden native selector
  document.getElementById('robot-modal-save').onclick = () => {
    const mainSelect = document.getElementById('robot-select');
    Array.from(mainSelect.options).forEach(opt => opt.selected = false);
    
    const checkedValues = [];
    if (cbAll.checked) checkedValues.push('all');
    if (cbAllRobots.checked) checkedValues.push('all_robots');
    if (cbAllDrones.checked) checkedValues.push('all_drones');
    if (cbAllDogs.checked) checkedValues.push('all_dogs');
    
    deviceCbs.forEach(cb => {
      if (cb.checked) checkedValues.push(cb.value);
    });
    
    checkedValues.forEach(val => {
      const match = Array.from(mainSelect.options).find(o => o.value === val);
      if (match) match.selected = true;
    });
    
    modal.style.display = 'none';
    mainSelect.dispatchEvent(new Event('change'));
  };

  // Close modal on outside click
  window.onclick = function(event) {
    if (event.target == modal) {
      modal.style.display = 'none';
    }
  };
}
