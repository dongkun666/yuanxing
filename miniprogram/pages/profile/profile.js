const api = require('../../utils/api.js')
const auth = require('../../utils/auth.js')
const app = getApp()

Page({
  data: {
    userInfo: null,
    isLoggedIn: false,
    menuGroups: [
      {
        title: '我的服务',
        items: [
          { icon: '⭐', label: '我的收藏', page: 'favorites' },
          { icon: '📋', label: '审查记录', page: 'review-history' },
          { icon: '📅', label: '日程管理', page: 'schedule' },
          { icon: '👥', label: '客户管理', page: 'clients' }
        ]
      },
      {
        title: '其他',
        items: [
          { icon: '🔔', label: '消息通知', page: 'notifications' },
          { icon: '⚙️', label: '设置', page: 'settings' },
          { icon: '❓', label: '帮助中心', page: 'help' },
          { icon: 'ℹ️', label: '关于我们', page: 'about' }
        ]
      }
    ],
    stats: {
      favoriteCount: 0,
      reviewCount: 0,
      caseCount: 0
    }
  },

  onShow() {
    this.checkLoginStatus()
    if (this.data.isLoggedIn) {
      this.loadUserStats()
    }
  },

  checkLoginStatus() {
    const isLoggedIn = auth.isLoggedIn()
    const userInfo = wx.getStorageSync('user_info')
    this.setData({
      isLoggedIn,
      userInfo
    })
  },

  async loadUserStats() {
    try {
      const res = await api.request({
        url: '/api/gateway/user-stats',
        method: 'GET'
      })
      if (res) {
        this.setData({ stats: res })
      }
    } catch (e) {
      console.error('加载用户统计失败', e)
    }
  },

  goToLogin() {
    wx.navigateTo({ url: '/pages/login/login' })
  },

  onMenuTap(e) {
    const page = e.currentTarget.dataset.page
    if (!auth.requireLogin()) return
    wx.navigateTo({ url: `/pages/${page}/${page}` })
  },

  async onLogout() {
    wx.showModal({
      title: '确认退出',
      content: '确定要退出登录吗？',
      success: (res) => {
        if (res.confirm) {
          auth.logout()
          app.clearToken()
          this.setData({
            isLoggedIn: false,
            userInfo: null
          })
          wx.showToast({ title: '已退出登录', icon: 'success' })
        }
      }
    })
  },

  onAvatarTap() {
    if (!this.data.isLoggedIn) {
      this.goToLogin()
    }
  }
})
