document.addEventListener('DOMContentLoaded', () => {
  const apiKeyInput = document.getElementById('apiKey');
  const toggleApiKeyBtn = document.getElementById('toggleApiKey');
  const saveApiKeyBtn = document.getElementById('saveApiKey');
  const autoHighlightToggle = document.getElementById('autoHighlight');
  const contextMenuToggle = document.getElementById('contextMenu');
  const notificationsToggle = document.getElementById('notifications');
  const colorOptions = document.querySelectorAll('.color-option');
  const saveSettingsBtn = document.getElementById('saveSettings');
  const resetSettingsBtn = document.getElementById('resetSettings');
  const toast = document.getElementById('toast');

  let selectedColor = 'yellow';

  loadSettings();

  toggleApiKeyBtn.addEventListener('click', () => {
    if (apiKeyInput.type === 'password') {
      apiKeyInput.type = 'text';
      toggleApiKeyBtn.textContent = '🙈';
    } else {
      apiKeyInput.type = 'password';
      toggleApiKeyBtn.textContent = '👁️';
    }
  });

  saveApiKeyBtn.addEventListener('click', () => {
    const apiKey = apiKeyInput.value.trim();
    chrome.storage.sync.set({apiKey}, () => {
      showToast('API Key 已保存');
    });
  });

  colorOptions.forEach((option) => {
    option.addEventListener('click', () => {
      colorOptions.forEach((o) => o.classList.remove('active'));
      option.classList.add('active');
      selectedColor = option.dataset.color;
    });
  });

  saveSettingsBtn.addEventListener('click', () => {
    const settings = {
      apiKey: apiKeyInput.value.trim(),
      autoHighlight: autoHighlightToggle.checked,
      contextMenu: contextMenuToggle.checked,
      notifications: notificationsToggle.checked,
      highlightColor: selectedColor,
    };

    chrome.storage.sync.set(settings, () => {
      showToast('设置已保存');
      updateContentScript();
    });
  });

  resetSettingsBtn.addEventListener('click', () => {
    if (confirm('确定要重置所有设置吗？')) {
      const defaultSettings = {
        apiKey: '',
        autoHighlight: false,
        contextMenu: true,
        notifications: true,
        highlightColor: 'yellow',
      };

      chrome.storage.sync.set(defaultSettings, () => {
        loadSettings();
        showToast('设置已重置');
      });
    }
  });

  function loadSettings() {
    chrome.storage.sync.get(
      {
        apiKey: '',
        autoHighlight: false,
        contextMenu: true,
        notifications: true,
        highlightColor: 'yellow',
      },
      (result) => {
        apiKeyInput.value = result.apiKey;
        autoHighlightToggle.checked = result.autoHighlight;
        contextMenuToggle.checked = result.contextMenu;
        notificationsToggle.checked = result.notifications;
        selectedColor = result.highlightColor;

        colorOptions.forEach((option) => {
          option.classList.toggle(
            'active',
            option.dataset.color === result.highlightColor,
          );
        });
      },
    );
  }

  function updateContentScript() {
    chrome.tabs.query({}, (tabs) => {
      tabs.forEach((tab) => {
        chrome.tabs.sendMessage(
          tab.id,
          {
            action: 'toggleHighlight',
            enabled: autoHighlightToggle.checked,
          },
          () => {
            chrome.runtime.lastError;
          },
        );
      });
    });
  }

  function showToast(message) {
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => {
      toast.classList.remove('show');
    }, 2000);
  }
});
