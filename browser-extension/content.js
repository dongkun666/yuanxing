(() => {
  if (window.lexprimeContentLoaded) return;
  window.lexprimeContentLoaded = true;

  let highlightedElements = [];
  let isHighlightEnabled = false;

  chrome.storage.sync.get(['autoHighlight', 'highlightColor'], (result) => {
    isHighlightEnabled = result.autoHighlight || false;
    if (isHighlightEnabled) {
      detectAndHighlightLaws();
    }
  });

  function detectAndHighlightLaws() {
    const lawPatterns = [
      /《[^》]+》第[一二三四五六七八九十百千\d]+条/g,
      /民法典第[一二三四五六七八九十百千\d]+条/gi,
      /刑法第[一二三四五六七八九十百千\d]+条/gi,
      /民事诉讼法第[一二三四五六七八九十百千\d]+条/gi,
      /刑事诉讼法第[一二三四五六七八九十百千\d]+条/gi,
      /合同法第[一二三四五六七八九十百千\d]+条/gi,
    ];

    const walker = document.createTreeWalker(
      document.body,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode: (node) => {
          if (node.parentElement.closest('.lexprime-highlight')) {
            return NodeFilter.FILTER_REJECT;
          }
          const text = node.nodeValue;
          if (text.length < 10) return NodeFilter.FILTER_REJECT;
          return NodeFilter.FILTER_ACCEPT;
        },
      },
    );

    const textNodes = [];
    let node;
    while ((node = walker.nextNode())) {
      textNodes.push(node);
    }

    textNodes.forEach((textNode) => {
      highlightLawReferences(textNode, lawPatterns);
    });
  }

  function highlightLawReferences(textNode, patterns) {
    let text = textNode.nodeValue;
    let matches = [];

    patterns.forEach((pattern) => {
      let match;
      pattern.lastIndex = 0;
      while ((match = pattern.exec(text)) !== null) {
        matches.push({
          start: match.index,
          end: match.index + match[0].length,
          text: match[0],
        });
      }
    });

    if (matches.length === 0) return;

    matches.sort((a, b) => a.start - b.start);

    const fragment = document.createDocumentFragment();
    let lastIndex = 0;

    matches.forEach((match) => {
      if (match.start >= lastIndex) {
        fragment.appendChild(document.createTextNode(text.slice(lastIndex, match.start)));
        
        const span = document.createElement('span');
        span.className = 'lexprime-highlight';
        span.textContent = match.text;
        span.title = '点击查看法律条文详情';
        span.dataset.lawText = match.text;
        span.addEventListener('click', (e) => handleLawClick(e, match.text));
        
        fragment.appendChild(span);
        highlightedElements.push(span);
        
        lastIndex = match.end;
      }
    });

    fragment.appendChild(document.createTextNode(text.slice(lastIndex)));
    textNode.parentNode.replaceChild(fragment, textNode);
  }

  function handleLawClick(event, lawText) {
    event.stopPropagation();
    showLawPopup(lawText, event);
  }

  function showLawPopup(lawText, event) {
    removeExistingPopup();

    const popup = document.createElement('div');
    popup.className = 'lexprime-popup';
    popup.innerHTML = `
      <div class="lexprime-popup-header">
        <span class="lexprime-popup-title">${lawText}</span>
        <button class="lexprime-popup-close">×</button>
      </div>
      <div class="lexprime-popup-content">
        <div class="lexprime-loading">正在查询...</div>
      </div>
      <div class="lexprime-popup-actions">
        <button class="lexprime-btn lexprime-btn-primary" data-action="detail">查看详情</button>
        <button class="lexprime-btn" data-action="save">收藏</button>
        <button class="lexprime-btn" data-action="explain">解释</button>
      </div>
    `;

    document.body.appendChild(popup);

    const rect = event.target.getBoundingClientRect();
    const popupRect = popup.getBoundingClientRect();
    
    let top = rect.bottom + window.scrollY + 8;
    let left = rect.left + window.scrollX;
    
    if (left + popupRect.width > window.innerWidth) {
      left = window.innerWidth - popupRect.width - 20;
    }
    if (top + popupRect.height > window.innerHeight + window.scrollY) {
      top = rect.top + window.scrollY - popupRect.height - 8;
    }

    popup.style.top = `${top}px`;
    popup.style.left = `${left}px`;

    popup.querySelector('.lexprime-popup-close').addEventListener('click', removeExistingPopup);
    
    popup.querySelectorAll('[data-action]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const action = btn.dataset.action;
        handlePopupAction(action, lawText);
      });
    });

    loadLawDetail(lawText, popup.querySelector('.lexprime-popup-content'));

    setTimeout(() => {
      document.addEventListener('click', handleOutsideClick);
    }, 0);
  }

  function removeExistingPopup() {
    const existing = document.querySelector('.lexprime-popup');
    if (existing) {
      existing.remove();
    }
    document.removeEventListener('click', handleOutsideClick);
  }

  function handleOutsideClick(event) {
    const popup = document.querySelector('.lexprime-popup');
    const highlight = event.target.closest('.lexprime-highlight');
    if (popup && !popup.contains(event.target) && !highlight) {
      removeExistingPopup();
    }
  }

  async function loadLawDetail(lawText, contentEl) {
    try {
      const response = await chrome.runtime.sendMessage({
        action: 'explainText',
        text: lawText,
      });
      
      if (response.success) {
        contentEl.innerHTML = `<div class="lexprime-explanation">${response.data.explanation || '暂无解释'}</div>`;
      } else {
        contentEl.innerHTML = `<div class="lexprime-error">查询失败: ${response.error}</div>`;
      }
    } catch (error) {
      contentEl.innerHTML = `<div class="lexprime-error">查询失败</div>`;
    }
  }

  function handlePopupAction(action, lawText) {
    switch (action) {
      case 'detail':
        chrome.runtime.sendMessage({
          action: 'searchCases',
          query: lawText,
        });
        break;
      case 'save':
        chrome.runtime.sendMessage({
          action: 'saveToFavorites',
          item: {
            id: Date.now().toString(),
            type: 'law',
            content: lawText,
            source: window.location.href,
            title: document.title,
            createdAt: new Date().toISOString(),
          },
        });
        removeExistingPopup();
        break;
      case 'explain':
        break;
    }
  }

  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    switch (request.action) {
      case 'highlightSelection':
        highlightSelection();
        sendResponse({success: true});
        break;
      case 'toggleHighlight':
        isHighlightEnabled = request.enabled;
        if (isHighlightEnabled) {
          detectAndHighlightLaws();
        } else {
          removeAllHighlights();
        }
        sendResponse({success: true});
        break;
      case 'getSelection':
        const selection = window.getSelection().toString();
        sendResponse({text: selection});
        break;
    }
  });

  function highlightSelection() {
    const selection = window.getSelection();
    if (selection.rangeCount === 0) return;

    const range = selection.getRangeAt(0);
    const span = document.createElement('span');
    span.className = 'lexprime-highlight lexprime-user-highlight';
    range.surroundContents(span);
    highlightedElements.push(span);
  }

  function removeAllHighlights() {
    highlightedElements.forEach((el) => {
      const parent = el.parentNode;
      if (parent) {
        parent.replaceChild(document.createTextNode(el.textContent), el);
      }
    });
    highlightedElements = [];
  }
})();
