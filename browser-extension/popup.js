document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('searchInput');
  const searchBtn = document.getElementById('searchBtn');
  const optionsBtn = document.getElementById('optionsBtn');
  const contentArea = document.getElementById('contentArea');
  const actionBtns = document.querySelectorAll('.action-btn');

  optionsBtn.addEventListener('click', () => {
    chrome.runtime.openOptionsPage();
  });

  searchBtn.addEventListener('click', handleSearch);
  searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  });

  actionBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      const action = btn.dataset.action;
      handleAction(action);
    });
  });

  async function handleSearch() {
    const query = searchInput.value.trim();
    if (!query) return;

    showLoading();

    try {
      const response = await chrome.runtime.sendMessage({
        action: 'searchCases',
        query: query,
      });

      if (response.success) {
        showSearchResults(response.data, query);
      } else {
        showError(response.error);
      }
    } catch (error) {
      showError('搜索失败，请检查网络连接');
    }
  }

  function handleAction(action) {
    switch (action) {
      case 'contract-review':
        showContractReview();
        break;
      case 'case-search':
        searchInput.focus();
        break;
      case 'ai-chat':
        showAIChat();
        break;
      case 'favorites':
        showFavorites();
        break;
    }
  }

  function showLoading() {
    contentArea.innerHTML = '<div class="loading">加载中...</div>';
  }

  function showError(message) {
    contentArea.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">⚠️</div>
        <div>${message}</div>
      </div>
    `;
  }

  function showSearchResults(data, query) {
    const items = data.items || [];
    const total = data.total || 0;

    if (items.length === 0) {
      contentArea.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">🔍</div>
          <div>未找到相关判例</div>
        </div>
      `;
      return;
    }

    const html = `
      <div style="margin-bottom: 12px; font-size: 13px; color: #64748b;">
        找到 <strong style="color: #1e40af;">${total}</strong> 个相关结果
      </div>
      ${items.map((item) => `
        <div class="case-item" data-doc-id="${item.doc_id}">
          <div class="case-name">${item.case_name || '未知案件'}</div>
          <div class="case-info">
            <span class="case-court">${item.court || ''}</span>
            <span class="case-date">${item.judgment_date || ''}</span>
          </div>
          <div class="case-footer">
            <span class="case-score">
              LexScore: <span class="score-value">${item.lex_score || 0}</span>
            </span>
          </div>
        </div>
      `).join('')}
    `;

    contentArea.innerHTML = html;

    document.querySelectorAll('.case-item').forEach((item) => {
      item.addEventListener('click', () => {
        const docId = item.dataset.docId;
        chrome.tabs.create({
          url: `https://lexprime.com/cases/${docId}`,
        });
      });
    });
  }

  function showContractReview() {
    chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
      chrome.tabs.sendMessage(tabs[0].id, {action: 'getSelection'}, (response) => {
        const selectedText = response?.text || '';
        
        contentArea.innerHTML = `
          <div class="tab-bar">
            <div class="tab-item active">合同审查</div>
          </div>
          <div style="margin-bottom: 12px;">
            <textarea 
              id="contractText" 
              style="width: 100%; min-height: 120px; padding: 12px; border: 1px solid #e2e8f0; border-radius: 8px; font-size: 13px; font-family: inherit; resize: vertical;"
              placeholder="请输入或粘贴合同文本..."
            >${selectedText}</textarea>
          </div>
          <div style="display: flex; gap: 8px; margin-bottom: 12px;">
            <select id="contractType" style="flex: 1; padding: 8px 12px; border: 1px solid #e2e8f0; border-radius: 8px; font-size: 13px;">
              <option value="">选择合同类型</option>
              <option value="借款合同">借款合同</option>
              <option value="买卖合同">买卖合同</option>
              <option value="租赁合同">租赁合同</option>
              <option value="劳动合同">劳动合同</option>
              <option value="其他">其他</option>
            </select>
          </div>
          <button id="startReviewBtn" style="width: 100%; padding: 12px; background: #1e40af; color: #fff; border: none; border-radius: 8px; font-size: 14px; font-weight: 500; cursor: pointer;">
            开始审查
          </button>
        `;

        document.getElementById('startReviewBtn').addEventListener('click', async () => {
          const text = document.getElementById('contractText').value.trim();
          const type = document.getElementById('contractType').value;
          
          if (!text) {
            alert('请输入合同文本');
            return;
          }

          const btn = document.getElementById('startReviewBtn');
          btn.disabled = true;
          btn.textContent = '审查中...';

          try {
            const response = await chrome.runtime.sendMessage({
              action: 'searchCases',
              query: text.substring(0, 100),
            });
            btn.disabled = false;
            btn.textContent = '开始审查';
            alert('审查功能演示：已发送到 LexPrime 服务端');
          } catch (error) {
            btn.disabled = false;
            btn.textContent = '开始审查';
            alert('审查失败: ' + error.message);
          }
        });
      });
    });
  }

  function showAIChat() {
    contentArea.innerHTML = `
      <div class="tab-bar">
        <div class="tab-item active">AI 法律咨询</div>
      </div>
      <div style="background: #f8fafc; border-radius: 8px; padding: 12px; margin-bottom: 12px;">
        <div style="font-size: 13px; color: #475569; line-height: 1.6;">
          您好！我是 LexPrime AI 法律助手，有什么可以帮您的吗？
        </div>
      </div>
      <div style="display: flex; gap: 8px;">
        <input 
          type="text" 
          id="chatInput" 
          placeholder="输入您的问题..."
          style="flex: 1; padding: 10px 12px; border: 1px solid #e2e8f0; border-radius: 8px; font-size: 13px;"
        />
        <button id="sendChatBtn" style="padding: 0 16px; background: #1e40af; color: #fff; border: none; border-radius: 8px; cursor: pointer;">
          发送
        </button>
      </div>
    `;

    document.getElementById('sendChatBtn').addEventListener('click', () => {
      const input = document.getElementById('chatInput');
      const message = input.value.trim();
      if (message) {
        alert('AI 咨询功能演示');
      }
    });
  }

  async function showFavorites() {
    showLoading();

    try {
      const response = await chrome.runtime.sendMessage({action: 'getFavorites'});
      
      if (response.success) {
        const favorites = response.data || [];
        
        if (favorites.length === 0) {
          contentArea.innerHTML = `
            <div class="empty-state">
              <div class="empty-icon">⭐</div>
              <div>暂无收藏</div>
              <div style="font-size: 12px; margin-top: 8px;">在网页上选中文本右键收藏</div>
            </div>
          `;
          return;
        }

        const html = `
          <div class="tab-bar">
            <div class="tab-item active">我的收藏 (${favorites.length})</div>
          </div>
          ${favorites.map((item) => `
            <div class="favorite-item">
              <div class="favorite-content">${item.content}</div>
              <div style="display: flex; justify-content: space-between;">
                <span class="favorite-date">${new Date(item.createdAt).toLocaleDateString()}</span>
              </div>
              <div class="favorite-actions">
                <button class="favorite-btn" data-id="${item.id}" data-action="view">查看</button>
                <button class="favorite-btn" data-id="${item.id}" data-action="delete">删除</button>
              </div>
            </div>
          `).join('')}
        `;

        contentArea.innerHTML = html;
      }
    } catch (error) {
      showError('加载收藏失败');
    }
  }
});
