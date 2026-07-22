const API_BASE = 'https://api.lexprime.com';

chrome.runtime.onInstalled.addListener(() => {
  console.log('LexPrime 扩展已安装');

  chrome.contextMenus.create({
    id: 'lexprime-contract-review',
    title: '使用 LexPrime 审查合同',
    contexts: ['selection', 'page'],
  });

  chrome.contextMenus.create({
    id: 'lexprime-case-search',
    title: '搜索相关判例',
    contexts: ['selection'],
  });

  chrome.contextMenus.create({
    id: 'lexprime-save-law',
    title: '收藏法律条文',
    contexts: ['selection'],
  });

  chrome.contextMenus.create({
    id: 'lexprime-explain',
    title: '解释法律术语',
    contexts: ['selection'],
  });

  chrome.storage.sync.get(['apiKey', 'autoHighlight'], (result) => {
    if (!result.apiKey) {
      chrome.runtime.openOptionsPage();
    }
  });
});

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  switch (info.menuItemId) {
    case 'lexprime-contract-review':
      await handleContractReview(info, tab);
      break;
    case 'lexprime-case-search':
      await handleCaseSearch(info, tab);
      break;
    case 'lexprime-save-law':
      await handleSaveLaw(info, tab);
      break;
    case 'lexprime-explain':
      await handleExplain(info, tab);
      break;
  }
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  switch (request.action) {
    case 'searchCases':
      searchCases(request.query)
        .then(result => sendResponse({success: true, data: result}))
        .catch(error => sendResponse({success: false, error: error.message}));
      return true;

    case 'getLawDetail':
      getLawDetail(request.lawId)
        .then(result => sendResponse({success: true, data: result}))
        .catch(error => sendResponse({success: false, error: error.message}));
      return true;

    case 'explainText':
      explainText(request.text)
        .then(result => sendResponse({success: true, data: result}))
        .catch(error => sendResponse({success: false, error: error.message}));
      return true;

    case 'translateText':
      translateText(request.text, request.targetLang)
        .then(result => sendResponse({success: true, data: result}))
        .catch(error => sendResponse({success: false, error: error.message}));
      return true;

    case 'saveToFavorites':
      saveToFavorites(request.item)
        .then(result => sendResponse({success: true, data: result}))
        .catch(error => sendResponse({success: false, error: error.message}));
      return true;

    case 'getFavorites':
      getFavorites()
        .then(result => sendResponse({success: true, data: result}))
        .catch(error => sendResponse({success: false, error: error.message}));
      return true;

    case 'getApiKey':
      chrome.storage.sync.get(['apiKey'], (result) => {
        sendResponse({apiKey: result.apiKey || ''});
      });
      return true;
  }
});

async function handleContractReview(info, tab) {
  try {
    const text = info.selectionText || '';
    if (!text) {
      showNotification('请先选择合同文本', '需要选择要审查的合同内容');
      return;
    }

    showNotification('合同审查中...', '正在分析合同内容，请稍候');

    const result = await apiRequest('/api/contract-review/upload', {
      method: 'POST',
      body: JSON.stringify({
        contract_type: '自动识别',
        contract_text: text,
        stance: '审查方',
      }),
    });

    if (result.review_id) {
      const detail = await apiRequest(`/api/contract-review/result/${result.review_id}`);
      
      const riskCount = detail.risks?.length || 0;
      const riskScore = detail.risk_score || 0;
      
      showNotification(
        `审查完成 - 风险评分: ${riskScore}`,
        `发现 ${riskCount} 项风险点，点击查看详情`
      );

      chrome.storage.local.set({lastReviewResult: detail});
    }
  } catch (error) {
    showNotification('审查失败', error.message || '请稍后重试');
  }
}

async function handleCaseSearch(info, tab) {
  try {
    const query = info.selectionText || '';
    if (!query) {
      showNotification('请先选择关键词', '需要选择要搜索的内容');
      return;
    }

    const result = await searchCases(query);
    
    showNotification(
      `找到 ${result.total} 个相关判例`,
      `点击查看搜索结果详情`
    );

    chrome.storage.local.set({lastSearchResult: result, lastSearchQuery: query});
  } catch (error) {
    showNotification('搜索失败', error.message || '请稍后重试');
  }
}

async function handleSaveLaw(info, tab) {
  try {
    const text = info.selectionText || '';
    if (!text) {
      showNotification('请先选择法律条文', '需要选择要收藏的内容');
      return;
    }

    const item = {
      id: Date.now().toString(),
      type: 'law',
      content: text,
      source: tab.url,
      title: tab.title,
      createdAt: new Date().toISOString(),
    };

    await saveToFavorites(item);
    
    showNotification('收藏成功', '法律条文已添加到收藏夹');
  } catch (error) {
    showNotification('收藏失败', error.message || '请稍后重试');
  }
}

async function handleExplain(info, tab) {
  try {
    const text = info.selectionText || '';
    if (!text) {
      showNotification('请先选择文本', '需要选择要解释的内容');
      return;
    }

    const result = await explainText(text);
    
    showNotification('法律解释', result.explanation || '正在生成解释...');
  } catch (error) {
    showNotification('解释失败', error.message || '请稍后重试');
  }
}

async function searchCases(query) {
  const result = await apiRequest('/api/search', {
    method: 'POST',
    body: JSON.stringify({
      query: query,
      index: 'cases',
      page: 1,
      size: 20,
    }),
  });
  return result;
}

async function getLawDetail(lawId) {
  return await apiRequest(`/api/laws/${lawId}`);
}

async function explainText(text) {
  const result = await apiRequest('/api/ai/chat', {
    method: 'POST',
    body: JSON.stringify({
      message: `请用通俗易懂的语言解释以下法律术语/条文：\n\n${text}`,
      stream: false,
    }),
  });
  return {explanation: result.reply};
}

async function translateText(text, targetLang = 'zh-CN') {
  const result = await apiRequest('/api/ai/chat', {
    method: 'POST',
    body: JSON.stringify({
      message: `请将以下内容翻译成${targetLang === 'zh-CN' ? '中文' : '英文'}：\n\n${text}`,
      stream: false,
    }),
  });
  return {translation: result.reply};
}

async function saveToFavorites(item) {
  return new Promise((resolve, reject) => {
    chrome.storage.sync.get(['favorites'], (result) => {
      const favorites = result.favorites || [];
      favorites.unshift(item);
      if (favorites.length > 100) {
        favorites.pop();
      }
      chrome.storage.sync.set({favorites}, () => {
        resolve({success: true});
      });
    });
  });
}

async function getFavorites() {
  return new Promise((resolve, reject) => {
    chrome.storage.sync.get(['favorites'], (result) => {
      resolve(result.favorites || []);
    });
  });
}

async function apiRequest(path, options = {}) {
  const apiKey = await getApiKeyFromStorage();
  
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  
  if (apiKey) {
    headers['Authorization'] = `Bearer ${apiKey}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || error.message || `HTTP ${response.status}`);
  }

  return response.json();
}

function getApiKeyFromStorage() {
  return new Promise((resolve) => {
    chrome.storage.sync.get(['apiKey'], (result) => {
      resolve(result.apiKey || '');
    });
  });
}

function showNotification(title, message) {
  chrome.notifications.create({
    type: 'basic',
    iconUrl: 'icons/icon128.png',
    title: title,
    message: message,
  });
}

chrome.commands.onCommand.addListener((command) => {
  switch (command) {
    case 'highlight-law':
      chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
        chrome.tabs.sendMessage(tabs[0].id, {action: 'highlightSelection'});
      });
      break;
    case 'quick-search':
      chrome.action.openPopup();
      break;
  }
});
