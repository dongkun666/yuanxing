const auth = require('./utils/auth.js')
const api = require('./utils/api.js')

App({
  globalData: {
    userInfo: null,
    token: null,
    baseUrl: 'https://api.lexprime.com',
    systemInfo: null
  },

  onLaunch() {
    this.getSystemInfo()
    this.checkLoginStatus()
  },

  onShow() {
    this.updateNotificationBadge()
  },

  getSystemInfo() {
    try {
      const res = wx.getSystemInfoSync()
      this.globalData.systemInfo = res
    } catch (e) {
      console.error('获取系统信息失败', e)
    }
  },

  checkLoginStatus() {
    const token = wx.getStorageSync('access_token')
    if (token) {
      this.globalData.token = token
      this.fetchUserInfo()
    }
  },

  async fetchUserInfo() {
    try {
      const res = await api.request({
        url: '/api/users/me',
        method: 'GET'
      })
      if (res) {
        this.globalData.userInfo = res
      }
    } catch (e) {
      if (e.statusCode === 401) {
        auth.logout()
      }
    }
  },

  updateNotificationBadge() {
    if (!this.globalData.token) return
    api.request({
      url: '/api/notifications/unread-count',
      method: 'GET'
    }).then(res => {
      if (res && res.count > 0) {
        wx.setTabBarBadge({
          index: 3,
          text: res.count > 99 ? '99+' : String(res.count)
        })
      } else {
        wx.removeTabBarBadge({ index: 3 })
      }
    }).catch(() => {})
  },

  setToken(token) {
    this.globalData.token = token
    wx.setStorageSync('access_token', token)
  },

  clearToken() {
    this.globalData.token = null
    this.globalData.userInfo = null
    wx.removeStorageSync('access_token')
    wx.removeStorageSync('user_info')
  }
})
