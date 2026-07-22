(function () {
    'use strict';

    var STORAGE_KEY_PREFIX = 'lexprime.recommendation.';
    var FEEDBACK_STORAGE_KEY = STORAGE_KEY_PREFIX + 'feedback';

    function _getFeedbackStorage() {
        try {
            var data = localStorage.getItem(FEEDBACK_STORAGE_KEY);
            return data ? JSON.parse(data) : {};
        } catch (e) {
            return {};
        }
    }

    function _saveFeedbackStorage(data) {
        try {
            localStorage.setItem(FEEDBACK_STORAGE_KEY, JSON.stringify(data));
        } catch (e) {
            console.warn('[Recommendation] 保存反馈数据失败:', e);
        }
    }

    function _getUserId() {
        var userId = localStorage.getItem(STORAGE_KEY_PREFIX + 'user_id');
        if (!userId) {
            userId = 'user_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem(STORAGE_KEY_PREFIX + 'user_id', userId);
        }
        return userId;
    }

    function _formatNumber(num) {
        if (num >= 10000) {
            return (num / 10000).toFixed(1) + '万';
        }
        if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'k';
        }
        return num.toString();
    }

    var Recommendation = {
        _cache: {},

        getRecommendedCases: function (options, callback) {
            var self = this;
            options = options || {};
            var limit = options.limit || 10;
            var category = options.category || '';
            var useCache = options.cache !== false;
            var cacheKey = 'cases_' + limit + '_' + category;

            if (useCache && this._cache[cacheKey]) {
                if (callback) callback(null, this._cache[cacheKey]);
                return;
            }

            var url = '/api/recommend/cases?user_id=' + encodeURIComponent(_getUserId()) +
                '&limit=' + limit;
            if (category) {
                url += '&category=' + encodeURIComponent(category);
            }

            if (typeof API !== 'undefined' && API.get) {
                API.get(url, function (data) {
                    self._cache[cacheKey] = data;
                    if (callback) callback(null, data);
                }, function (err) {
                    console.warn('[Recommendation] 获取推荐案件失败，使用本地数据:', err);
                    var mockData = self._getMockCases(limit);
                    if (callback) callback(null, mockData);
                });
            } else {
                setTimeout(function () {
                    var mockData = self._getMockCases(limit);
                    self._cache[cacheKey] = mockData;
                    if (callback) callback(null, mockData);
                }, 300);
            }
        },

        getRecommendedLawyers: function (options, callback) {
            var self = this;
            options = options || {};
            var limit = options.limit || 10;
            var specialty = options.specialty || '';
            var useCache = options.cache !== false;
            var cacheKey = 'lawyers_' + limit + '_' + specialty;

            if (useCache && this._cache[cacheKey]) {
                if (callback) callback(null, this._cache[cacheKey]);
                return;
            }

            var url = '/api/recommend/lawyers?user_id=' + encodeURIComponent(_getUserId()) +
                '&limit=' + limit;
            if (specialty) {
                url += '&specialty=' + encodeURIComponent(specialty);
            }

            if (typeof API !== 'undefined' && API.get) {
                API.get(url, function (data) {
                    self._cache[cacheKey] = data;
                    if (callback) callback(null, data);
                }, function (err) {
                    console.warn('[Recommendation] 获取推荐律师失败，使用本地数据:', err);
                    var mockData = self._getMockLawyers(limit);
                    if (callback) callback(null, mockData);
                });
            } else {
                setTimeout(function () {
                    var mockData = self._getMockLawyers(limit);
                    self._cache[cacheKey] = mockData;
                    if (callback) callback(null, mockData);
                }, 300);
            }
        },

        getRecommendedTemplates: function (options, callback) {
            var self = this;
            options = options || {};
            var limit = options.limit || 10;
            var templateType = options.templateType || '';
            var category = options.category || '';
            var useCache = options.cache !== false;
            var cacheKey = 'templates_' + limit + '_' + templateType + '_' + category;

            if (useCache && this._cache[cacheKey]) {
                if (callback) callback(null, this._cache[cacheKey]);
                return;
            }

            var url = '/api/recommend/templates?user_id=' + encodeURIComponent(_getUserId()) +
                '&limit=' + limit;
            if (templateType) {
                url += '&template_type=' + encodeURIComponent(templateType);
            }
            if (category) {
                url += '&category=' + encodeURIComponent(category);
            }

            if (typeof API !== 'undefined' && API.get) {
                API.get(url, function (data) {
                    self._cache[cacheKey] = data;
                    if (callback) callback(null, data);
                }, function (err) {
                    console.warn('[Recommendation] 获取推荐模板失败，使用本地数据:', err);
                    var mockData = self._getMockTemplates(limit);
                    if (callback) callback(null, mockData);
                });
            } else {
                setTimeout(function () {
                    var mockData = self._getMockTemplates(limit);
                    self._cache[cacheKey] = mockData;
                    if (callback) callback(null, mockData);
                }, 300);
            }
        },

        submitFeedback: function (itemId, itemType, feedbackType, reason, callback) {
            var feedbackStorage = _getFeedbackStorage();
            var key = itemType + '_' + itemId;
            feedbackStorage[key] = {
                item_id: itemId,
                item_type: itemType,
                feedback_type: feedbackType,
                reason: reason || null,
                created_at: new Date().toISOString()
            };
            _saveFeedbackStorage(feedbackStorage);

            var url = '/api/recommend/feedback?user_id=' + encodeURIComponent(_getUserId());
            var body = {
                item_id: itemId,
                item_type: itemType,
                feedback_type: feedbackType,
                reason: reason || null
            };

            if (typeof API !== 'undefined' && API.post) {
                API.post(url, body, function (data) {
                    if (callback) callback(null, data);
                }, function (err) {
                    console.warn('[Recommendation] 提交反馈失败，本地已保存:', err);
                    if (callback) callback(null, { status: 'local_saved' });
                });
            } else {
                if (callback) callback(null, { status: 'local_saved' });
            }

            this.clearCache();
        },

        refreshRecommendations: function (type, callback) {
            var self = this;
            type = type || 'all';

            var url = '/api/recommend/refresh?user_id=' + encodeURIComponent(_getUserId()) +
                '&type=' + type;

            if (typeof API !== 'undefined' && API.get) {
                API.get(url, function (data) {
                    self.clearCache();
                    if (callback) callback(null, data);
                }, function (err) {
                    console.warn('[Recommendation] 刷新推荐失败:', err);
                    self.clearCache();
                    if (callback) callback(null, { status: 'success', new_count: 3 });
                });
            } else {
                setTimeout(function () {
                    self.clearCache();
                    if (callback) callback(null, { status: 'success', new_count: 3 });
                }, 500);
            }
        },

        clearCache: function () {
            this._cache = {};
        },

        hasFeedback: function (itemId, itemType) {
            var feedbackStorage = _getFeedbackStorage();
            var key = itemType + '_' + itemId;
            return !!feedbackStorage[key];
        },

        getFeedback: function (itemId, itemType) {
            var feedbackStorage = _getFeedbackStorage();
            var key = itemType + '_' + itemId;
            return feedbackStorage[key] || null;
        },

        renderCaseCard: function (item, options) {
            options = options || {};
            var showReasons = options.showReasons !== false;
            var showMatch = options.showMatch !== false;

            var matchPercent = item.match_percentage || Math.round((item.score || 0.7) * 100);
            var reasonsHtml = '';
            if (showReasons && item.reasons && item.reasons.length > 0) {
                var reasonItems = item.reasons.slice(0, 2).map(function (reason) {
                    return '<span class="inline-flex items-center gap-1 text-[10px] text-fg-tertiary">' +
                        '<iconify-icon icon="mdi:check-circle-outline" class="text-success"></iconify-icon>' +
                        reason +
                        '</span>';
                }).join('');
                reasonsHtml = '<div class="flex flex-wrap gap-2 mt-2">' + reasonItems + '</div>';
            }

            var matchHtml = '';
            if (showMatch) {
                matchHtml = '<div class="flex items-center gap-1.5">' +
                    '<div class="flex-1 h-1.5 bg-bg rounded-full overflow-hidden">' +
                    '<div class="h-full bg-gradient-to-r from-brand to-brand-hover rounded-full" style="width: ' + matchPercent + '%"></div>' +
                    '</div>' +
                    '<span class="text-[10px] font-semibold text-brand whitespace-nowrap">' + matchPercent + '% 匹配</span>' +
                    '</div>';
            }

            var card = document.createElement('div');
            card.className = 'recommend-case-card bg-white rounded-xl shadow-card border border-bg-border p-4 hover:shadow-lg hover:border-brand/30 transition-all cursor-pointer';
            card.dataset.itemId = item.id;
            card.dataset.itemType = 'case';

            card.innerHTML = [
                '<div class="flex items-start justify-between gap-3 mb-2">',
                '  <h3 class="text-sm font-semibold text-fg-primary line-clamp-2 flex-1">' + (item.case_name || item.title || '') + '</h3>',
                '  <button class="recommend-feedback-btn flex-shrink-0 w-7 h-7 flex items-center justify-center text-fg-tertiary hover:text-warning transition-colors rounded-lg hover:bg-bg" title="不感兴趣" data-feedback="dislike">',
                '    <iconify-icon icon="mdi:thumb-down-outline" class="text-base"></iconify-icon>',
                '  </button>',
                '</div>',
                '<div class="flex items-center gap-2 mb-2">',
                '  <span class="px-2 py-0.5 bg-brand-tint text-brand text-[10px] font-medium rounded-full">' + (item.cause_category || '合同纠纷') + '</span>',
                '  <span class="text-[11px] text-fg-tertiary">' + (item.court || '') + '</span>',
                '</div>',
                matchHtml,
                reasonsHtml
            ].join('');

            var self = this;
            var feedbackBtn = card.querySelector('.recommend-feedback-btn');
            if (feedbackBtn) {
                feedbackBtn.addEventListener('click', function (e) {
                    e.stopPropagation();
                    self.submitFeedback(item.id, 'case', 'dislike', null, function () {
                        card.style.opacity = '0.5';
                        if (typeof Utils !== 'undefined' && Utils.showToast) {
                            Utils.showToast('已减少此类推荐');
                        }
                    });
                });
            }

            return card;
        },

        renderLawyerCard: function (item, options) {
            options = options || {};
            var showReasons = options.showReasons !== false;
            var showMatch = options.showMatch !== false;

            var matchPercent = item.match_percentage || Math.round((item.score || 0.7) * 100);
            var avatar = item.avatar_url || '/assets/images/avatar.jpg';

            var specialtiesHtml = '';
            if (item.specialties && item.specialties.length > 0) {
                specialtiesHtml = item.specialties.slice(0, 2).map(function (s) {
                    return '<span class="px-1.5 py-0.5 bg-bg text-fg-secondary text-[10px] rounded">' + s + '</span>';
                }).join('');
            }

            var reasonsHtml = '';
            if (showReasons && item.reasons && item.reasons.length > 0) {
                var reasonItems = item.reasons.slice(0, 2).map(function (reason) {
                    return '<span class="inline-flex items-center gap-1 text-[10px] text-fg-tertiary">' +
                        '<iconify-icon icon="mdi:star-outline" class="text-warning"></iconify-icon>' +
                        reason +
                        '</span>';
                }).join('');
                reasonsHtml = '<div class="flex flex-wrap gap-2 mt-2">' + reasonItems + '</div>';
            }

            var matchHtml = '';
            if (showMatch) {
                matchHtml = '<div class="flex items-center gap-1.5 mb-2">' +
                    '<div class="flex-1 h-1.5 bg-bg rounded-full overflow-hidden">' +
                    '<div class="h-full bg-gradient-to-r from-success to-success-hover rounded-full" style="width: ' + matchPercent + '%"></div>' +
                    '</div>' +
                    '<span class="text-[10px] font-semibold text-success whitespace-nowrap">' + matchPercent + '% 匹配</span>' +
                    '</div>';
            }

            var card = document.createElement('div');
            card.className = 'recommend-lawyer-card bg-white rounded-xl shadow-card border border-bg-border p-4 hover:shadow-lg hover:border-success/30 transition-all cursor-pointer';
            card.dataset.itemId = item.id;
            card.dataset.itemType = 'lawyer';

            card.innerHTML = [
                '<div class="flex items-start gap-3 mb-3">',
                '  <div class="w-12 h-12 rounded-full bg-bg flex items-center justify-center overflow-hidden flex-shrink-0">',
                '    <img src="' + avatar + '" alt="' + (item.name || '') + '" class="w-full h-full object-cover" onerror="this.style.display=\'none\'; this.parentNode.innerHTML=\'<iconify-icon icon=\\\'mdi:account\\\' class=\\\'text-2xl text-fg-tertiary\\\'></iconify-icon>\'">',
                '  </div>',
                '  <div class="flex-1 min-w-0">',
                '    <div class="flex items-center justify-between gap-2">',
                '      <h3 class="text-sm font-semibold text-fg-primary truncate">' + (item.name || '') + '</h3>',
                '      <button class="recommend-feedback-btn flex-shrink-0 w-6 h-6 flex items-center justify-center text-fg-tertiary hover:text-warning transition-colors rounded-lg hover:bg-bg" title="不感兴趣" data-feedback="dislike">',
                '        <iconify-icon icon="mdi:thumb-down-outline" class="text-sm"></iconify-icon>',
                '      </button>',
                '    </div>',
                '    <p class="text-[11px] text-fg-tertiary truncate mt-0.5">' + (item.firm_name || '') + '</p>',
                '  </div>',
                '</div>',
                matchHtml,
                '<div class="flex items-center justify-between text-[11px] text-fg-secondary mb-2">',
                '  <span>胜诉率 <span class="font-semibold text-fg-primary">' + (item.win_rate ? item.win_rate.toFixed(1) : '0') + '%</span></span>',
                '  <span>执业 <span class="font-semibold text-fg-primary">' + (item.experience_years || 0) + '年</span></span>',
                '  <span>评分 <span class="font-semibold text-warning">' + (item.rating || 0) + '</span></span>',
                '</div>',
                '<div class="flex flex-wrap gap-1 mb-1">' + specialtiesHtml + '</div>',
                reasonsHtml
            ].join('');

            var self = this;
            var feedbackBtn = card.querySelector('.recommend-feedback-btn');
            if (feedbackBtn) {
                feedbackBtn.addEventListener('click', function (e) {
                    e.stopPropagation();
                    self.submitFeedback(item.id, 'lawyer', 'dislike', null, function () {
                        card.style.opacity = '0.5';
                        if (typeof Utils !== 'undefined' && Utils.showToast) {
                            Utils.showToast('已减少此类推荐');
                        }
                    });
                });
            }

            return card;
        },

        renderTemplateCard: function (item, options) {
            options = options || {};
            var showReasons = options.showReasons !== false;
            var showMatch = options.showMatch !== false;

            var matchPercent = item.match_percentage || Math.round((item.score || 0.7) * 100);
            var typeIcon = 'mdi:file-document-outline';
            var typeColor = 'text-brand';
            if (item.template_type === 'contract' || item.template_type === 'agreement') {
                typeIcon = 'mdi:file-sign-outline';
                typeColor = 'text-success';
            } else if (item.template_type === 'complaint' || item.template_type === 'defense') {
                typeIcon = 'mdi:gavel';
                typeColor = 'text-warning';
            }

            var reasonsHtml = '';
            if (showReasons && item.reasons && item.reasons.length > 0) {
                var reasonItems = item.reasons.slice(0, 2).map(function (reason) {
                    return '<span class="inline-flex items-center gap-1 text-[10px] text-fg-tertiary">' +
                        '<iconify-icon icon="mdi:lightbulb-outline" class="text-wiki"></iconify-icon>' +
                        reason +
                        '</span>';
                }).join('');
                reasonsHtml = '<div class="flex flex-wrap gap-2 mt-2">' + reasonItems + '</div>';
            }

            var matchHtml = '';
            if (showMatch) {
                matchHtml = '<div class="flex items-center gap-1.5 mb-2">' +
                    '<div class="flex-1 h-1.5 bg-bg rounded-full overflow-hidden">' +
                    '<div class="h-full bg-gradient-to-r from-wiki to-wiki-hover rounded-full" style="width: ' + matchPercent + '%"></div>' +
                    '</div>' +
                    '<span class="text-[10px] font-semibold text-wiki whitespace-nowrap">' + matchPercent + '% 匹配</span>' +
                    '</div>';
            }

            var card = document.createElement('div');
            card.className = 'recommend-template-card bg-white rounded-xl shadow-card border border-bg-border p-4 hover:shadow-lg hover:border-wiki/30 transition-all cursor-pointer';
            card.dataset.itemId = item.id;
            card.dataset.itemType = 'template';

            card.innerHTML = [
                '<div class="flex items-start gap-3 mb-2">',
                '  <div class="w-10 h-10 rounded-lg bg-wiki-tint flex items-center justify-center flex-shrink-0">',
                '    <iconify-icon icon="' + typeIcon + '" class="' + typeColor + ' text-xl"></iconify-icon>',
                '  </div>',
                '  <div class="flex-1 min-w-0">',
                '    <div class="flex items-start justify-between gap-2">',
                '      <h3 class="text-sm font-semibold text-fg-primary line-clamp-2 flex-1">' + (item.name || '') + '</h3>',
                '      <button class="recommend-feedback-btn flex-shrink-0 w-6 h-6 flex items-center justify-center text-fg-tertiary hover:text-warning transition-colors rounded-lg hover:bg-bg" title="不感兴趣" data-feedback="dislike">',
                '        <iconify-icon icon="mdi:thumb-down-outline" class="text-sm"></iconify-icon>',
                '      </button>',
                '    </div>',
                '    <span class="text-[10px] text-fg-tertiary mt-0.5 inline-block">' + (item.category || '') + '</span>',
                '  </div>',
                '</div>',
                matchHtml,
                '<p class="text-[11px] text-fg-secondary line-clamp-2 mb-2">' + (item.description || '') + '</p>',
                '<div class="flex items-center justify-between text-[10px] text-fg-tertiary">',
                '  <span class="flex items-center gap-1">',
                '    <iconify-icon icon="mdi:download-outline" class="text-xs"></iconify-icon>',
                _formatNumber(item.usage_count || 0) + ' 次使用',
                '  </span>',
                '  <span class="flex items-center gap-1">',
                '    <iconify-icon icon="mdi:star" class="text-warning text-xs"></iconify-icon>',
                (item.rating || 0).toFixed(1),
                '  </span>',
                '</div>',
                reasonsHtml
            ].join('');

            var self = this;
            var feedbackBtn = card.querySelector('.recommend-feedback-btn');
            if (feedbackBtn) {
                feedbackBtn.addEventListener('click', function (e) {
                    e.stopPropagation();
                    self.submitFeedback(item.id, 'template', 'dislike', null, function () {
                        card.style.opacity = '0.5';
                        if (typeof Utils !== 'undefined' && Utils.showToast) {
                            Utils.showToast('已减少此类推荐');
                        }
                    });
                });
            }

            return card;
        },

        renderRecommendationSection: function (container, type, options) {
            container = typeof container === 'string' ? document.querySelector(container) : container;
            if (!container) return;

            options = options || {};
            var title = options.title || this._getDefaultTitle(type);
            var limit = options.limit || 5;
            var showRefresh = options.showRefresh !== false;

            var section = document.createElement('div');
            section.className = 'recommendation-section mb-6';

            var headerHtml = [
                '<div class="flex items-center justify-between mb-3">',
                '  <div class="flex items-center gap-2">',
                '    <iconify-icon icon="' + this._getTypeIcon(type) + '" class="' + this._getTypeColor(type) + ' text-lg"></iconify-icon>',
                '    <h2 class="text-base font-bold text-fg-primary">' + title + '</h2>',
                '  </div>',
                '  <div class="flex items-center gap-2">',
                showRefresh ? '    <button class="recommend-refresh-btn flex items-center gap-1 px-2 py-1 text-[11px] text-fg-secondary hover:text-brand hover:bg-bg rounded-lg transition-colors">' +
                    '      <iconify-icon icon="mdi:refresh" class="text-sm"></iconify-icon>' +
                    '      <span>换一批</span>' +
                    '    </button>' : '',
                '    <button class="flex items-center gap-1 px-2 py-1 text-[11px] text-fg-secondary hover:text-brand hover:bg-bg rounded-lg transition-colors">' +
                    '      <span>查看更多</span>',
                '      <iconify-icon icon="mdi:chevron-right" class="text-sm"></iconify-icon>' +
                '    </button>',
                '  </div>',
                '</div>'
            ].join('');

            var contentHtml = '<div class="recommend-content grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">' +
                '<div class="col-span-full flex items-center justify-center py-8 text-fg-tertiary text-sm">' +
                '<iconify-icon icon="mdi:loading" class="text-xl mr-2 animate-spin"></iconify-icon>加载中...' +
                '</div>' +
                '</div>';

            section.innerHTML = headerHtml + contentHtml;
            container.appendChild(section);

            var self = this;
            var contentEl = section.querySelector('.recommend-content');

            this._loadRecommendations(contentEl, type, limit);

            var refreshBtn = section.querySelector('.recommend-refresh-btn');
            if (refreshBtn) {
                refreshBtn.addEventListener('click', function () {
                    var icon = refreshBtn.querySelector('iconify-icon');
                    if (icon) icon.style.animation = 'spin 0.5s linear';

                    self.refreshRecommendations(type, function () {
                        self._loadRecommendations(contentEl, type, limit, true);
                        setTimeout(function () {
                            if (icon) icon.style.animation = '';
                        }, 500);
                    });
                });
            }
        },

        _loadRecommendations: function (container, type, limit, forceRefresh) {
            var self = this;
            var options = { limit: limit, cache: !forceRefresh };

            var renderItems = function (items) {
                container.innerHTML = '';
                items.forEach(function (item) {
                    var card;
                    if (type === 'case') {
                        card = self.renderCaseCard(item);
                    } else if (type === 'lawyer') {
                        card = self.renderLawyerCard(item);
                    } else if (type === 'template') {
                        card = self.renderTemplateCard(item);
                    }
                    if (card) {
                        container.appendChild(card);
                    }
                });
            };

            if (type === 'case') {
                this.getRecommendedCases(options, function (err, data) {
                    if (data && data.items) {
                        renderItems(data.items);
                    }
                });
            } else if (type === 'lawyer') {
                this.getRecommendedLawyers(options, function (err, data) {
                    if (data && data.items) {
                        renderItems(data.items);
                    }
                });
            } else if (type === 'template') {
                this.getRecommendedTemplates(options, function (err, data) {
                    if (data && data.items) {
                        renderItems(data.items);
                    }
                });
            }
        },

        _getDefaultTitle: function (type) {
            var titles = {
                'case': '为你推荐的案件',
                'lawyer': '为你推荐的律师',
                'template': '为你推荐的模板'
            };
            return titles[type] || '推荐';
        },

        _getTypeIcon: function (type) {
            var icons = {
                'case': 'mdi:briefcase-star-outline',
                'lawyer': 'mdi:account-star-outline',
                'template': 'mdi:file-star-outline'
            };
            return icons[type] || 'mdi:star-outline';
        },

        _getTypeColor: function (type) {
            var colors = {
                'case': 'text-brand',
                'lawyer': 'text-success',
                'template': 'text-wiki'
            };
            return colors[type] || 'text-brand';
        },

        _getMockCases: function (limit) {
            var mockCases = [
                { id: 'CASE001', type: 'case', case_name: '张三诉李四借款合同纠纷案', court: '北京市第一中级人民法院', cause: '借款合同纠纷', cause_category: '合同纠纷', judgment_date: '2026-03-15', lex_score: 85, score: 0.92, match_percentage: 92, reasons: ['与您关注的合同纠纷高度相关', '您收藏过类似案件', '同法院近期典型案例'] },
                { id: 'CASE002', type: 'case', case_name: '某公司诉王某买卖合同纠纷案', court: '上海市浦东新区人民法院', cause: '买卖合同纠纷', cause_category: '合同纠纷', judgment_date: '2026-02-20', lex_score: 78, score: 0.85, match_percentage: 85, reasons: ['高 LexScore 评分案件', '您浏览过同类型案件'] },
                { id: 'CASE003', type: 'case', case_name: '某科技公司诉某公司知识产权侵权案', court: '深圳市中级人民法院', cause: '侵害商标权纠纷', cause_category: '知识产权', judgment_date: '2026-04-05', lex_score: 90, score: 0.88, match_percentage: 88, reasons: ['符合您的偏好设置', '同类案件胜诉率较高'] },
                { id: 'CASE004', type: 'case', case_name: '某银行诉某公司金融借款合同纠纷案', court: '北京市西城区人民法院', cause: '金融借款合同纠纷', cause_category: '合同纠纷', judgment_date: '2026-03-01', lex_score: 88, score: 0.82, match_percentage: 82, reasons: ['最新判决的典型案例', '同法院近期典型案例'] }
            ];
            return {
                items: mockCases.slice(0, limit),
                total: mockCases.length,
                algorithm: 'hybrid',
                mock_mode: true
            };
        },

        _getMockLawyers: function (limit) {
            var mockLawyers = [
                { id: 'LAWYER001', type: 'lawyer', name: '张明', avatar_url: '/assets/images/avatar.jpg', firm_name: '北京某律师事务所', specialties: ['民商事诉讼', '合同纠纷', '知识产权'], win_rate: 72.5, total_cases: 156, rating: 4.8, experience_years: 8, score: 0.88, match_percentage: 88, reasons: ['擅长您关注的合同纠纷领域', '胜诉率高于行业平均', '与您有相似案件经验'] },
                { id: 'LAWYER002', type: 'lawyer', name: '李华', avatar_url: null, firm_name: '上海某律师事务所', specialties: ['公司法', '投融资', '并购重组'], win_rate: 68.2, total_cases: 203, rating: 4.6, experience_years: 12, score: 0.75, match_percentage: 75, reasons: ['高评分资深律师', '多年执业经验'] },
                { id: 'LAWYER003', type: 'lawyer', name: '王芳', avatar_url: null, firm_name: '广州某律师事务所', specialties: ['婚姻家事', '遗产继承', '财富管理'], win_rate: 75.8, total_cases: 128, rating: 4.9, experience_years: 6, score: 0.72, match_percentage: 72, reasons: ['客户评价优秀', '高评分资深律师'] }
            ];
            return {
                items: mockLawyers.slice(0, limit),
                total: mockLawyers.length,
                algorithm: 'hybrid',
                mock_mode: true
            };
        },

        _getMockTemplates: function (limit) {
            var mockTemplates = [
                { id: 'TPL001', type: 'template', name: '民事起诉状模板（合同纠纷）', template_type: 'complaint', category: '诉讼文书', description: '适用于合同纠纷类案件的民事起诉状模板', usage_count: 1250, rating: 4.7, score: 0.85, match_percentage: 85, reasons: ['与您正在处理的案件类型匹配', '高评分常用模板', '同领域律师推荐'] },
                { id: 'TPL002', type: 'template', name: '劳动合同模板', template_type: 'contract', category: '合同模板', description: '标准劳动合同模板，包含试用期、薪资、社保等条款', usage_count: 3560, rating: 4.8, score: 0.78, match_percentage: 78, reasons: ['使用量排名靠前', '高评分常用模板'] },
                { id: 'TPL003', type: 'template', name: '法律意见书模板', template_type: 'opinion', category: '法律文书', description: '通用法律意见书模板，适用于各类法律咨询', usage_count: 890, rating: 4.6, score: 0.70, match_percentage: 70, reasons: ['官方认证优质模板', '使用量排名靠前'] }
            ];
            return {
                items: mockTemplates.slice(0, limit),
                total: mockTemplates.length,
                algorithm: 'hybrid',
                mock_mode: true
            };
        }
    };

    globalThis.Recommendation = Recommendation;
})();
