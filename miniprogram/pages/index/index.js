const api = require('../../utils/api.js')
const auth = require('../../utils/auth.js')

Page({
  data: {
    userInfo: null,
    isLoggedIn: false,
    searchKeyword: '',
    hotCases: [],
    scheduleList: [],
    notifications: [],
    loading: true,
    stats: {
      totalCases: 0,
      todaySchedule: 0,
      pendingReview: 0
    }
  },

  onLoad() {
    this.checkLoginStatus()
    this.loadData()
  },

  onShow() {
    this.checkLoginStatus()
    if (this.data.isLoggedIn) {
      this.loadUserRelatedData()
    }
  },

  onPullDownRefresh() {
    this.loadData().then(() => {
      wx.stopPullDownRefresh()
    })
  },

  checkLoginStatus() {
    const isLoggedIn = auth.isLoggedIn()
    const userInfo = wx.getStorageSync('user_info')
    this.setData({
      isLoggedIn,
      userInfo
    })
  },

  async loadData() {
    this.setData({ loading: true })
    try {
      await Promise.all([
        this.loadHotCases(),
        this.loadStats()
      ])
    } catch (e) {
      console.error('加载首页数据失败', e)
    } finally {
      this.setData({ loading: false })
    }
  },

  async loadUserRelatedData() {
    try {
      await Promise.all([
        this.loadTodaySchedule(),
        this.loadNotifications()
      ])
    } catch (e) {
      console.error('加载用户数据失败', e)
    }
  },

  async loadHotCases() {
    try {
      const res = await api.request({
        url: '/api/cases?limit=5&full=false',
        method: 'GET'
      })
      this.setData({ hotCases: res || [] })
    } catch (e) {
      this.setData({ hotCases: [] })
    }
  },

  async loadStats() {
    try {
      const res = await api.request({
        url: '/api/gateway/stats',
        method: 'GET'
      })
      this.setData({ stats: res || this.data.stats })
    } catch (e) {}
  },

  async loadTodaySchedule() {
    try {
      const res = await api.request({
        url: '/api/schedule/today',
        method: 'GET'
      })
      this.setData({ scheduleList: res || [] })
    } catch (e) {
      this.setData({ scheduleList: [] })
    }
  },

  async loadNotifications() {
    try {
      const res = await api.request({
        url: '/api/notifications?limit=3',
        method: 'GET'
      })
      this.setData({ notifications: res?.items || [] })
    } catch (e) {
      this.setData({ notifications: [] })
    }
  },

  onSearchInput(e) {
    this.setData({ searchKeyword: e.detail.value })
  },

  onSearch() {
    const keyword = this.data.searchKeyword.trim()
    if (!keyword) {
      wx.showToast({ title: '请输入搜索关键词', icon: 'none' })
      return
    }
    wx.navigateTo({
      url: `/pages/cases/cases?keyword=${encodeURIComponent(keyword)}`
    })
  },

  onCaseTap(e) {
    const docId = e.currentTarget.dataset.docId
    wx.navigateTo({
      url: `/pages/case-detail/case-detail?docId=${docId}`
    })
  },

  goToCases() {
    wx.switchTab({ url: '/pages/cases/cases' })
  },

  goToContractReview() {
    wx.switchTab({ url: '/pages/contract-review/contract-review' })
  },

  goToSchedule() {
    wx.navigateTo({ url: '/pages/schedule/schedule' })
  },

  goToLogin() {
    wx.navigateTo({ url: '/pages/login/login' })
  },

  goToProfile() {
    wx.switchTab({ url: '/pages/profile/profile' })
  },

  onQuickAction(e) {
    const action = e.currentTarget.dataset.action
    switch (action) {
      case 'case-search':
        wx.switchTab({ url: '/pages/cases/cases' })
        break
      case 'contract-review':
        wx.switchTab({ url: '/pages/contract-review/contract-review' })
        break
      case 'schedule':
        wx.navigateTo({ url: '/pages/schedule/schedule' })
        break
      case 'ai-chat':
        wx.navigateTo({ url: '/pages/ai-chat/ai-chat' })
        break
    }
  }
})
