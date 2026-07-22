const api = require('../../utils/api.js')
const auth = require('../../utils/auth.js')
const app = getApp()

Page({
  data: {
    email: '',
    password: '',
    isLogging: false,
    agreeTerms: false
  },

  onEmailInput(e) {
    this.setData({ email: e.detail.value })
  },

  onPasswordInput(e) {
    this.setData({ password: e.detail.value })
  },

  toggleAgree() {
    this.setData({ agreeTerms: !this.data.agreeTerms })
  },

  async onWxLogin() {
    if (!this.data.agreeTerms) {
      wx.showToast({ title: '请先同意用户协议', icon: 'none' })
      return
    }

    this.setData({ isLogging: true })
    
    try {
      const result = await auth.login()
      wx.showToast({ title: '登录成功', icon: 'success' })
      
      setTimeout(() => {
        wx.switchTab({ url: '/pages/index/index' })
      }, 1000)
    } catch (e) {
      console.error('微信登录失败', e)
      wx.showToast({ 
        title: e.message || '登录失败', 
        icon: 'none' 
      })
    } finally {
      this.setData({ isLogging: false })
    }
  },

  async onEmailLogin() {
    if (!this.data.agreeTerms) {
      wx.showToast({ title: '请先同意用户协议', icon: 'none' })
      return
    }

    if (!this.data.email) {
      wx.showToast({ title: '请输入邮箱', icon: 'none' })
      return
    }

    if (!this.data.password) {
      wx.showToast({ title: '请输入密码', icon: 'none' })
      return
    }

    this.setData({ isLogging: true })
    
    try {
      const res = await api.request({
        url: '/api/auth/login',
        method: 'POST',
        data: {
          email: this.data.email,
          password: this.data.password
        }
      })

      if (res.access_token) {
        app.setToken(res.access_token)
        wx.setStorageSync('refresh_token', res.refresh_token)
        
        wx.showToast({ title: '登录成功', icon: 'success' })
        
        setTimeout(() => {
          wx.switchTab({ url: '/pages/index/index' })
        }, 1000)
      }
    } catch (e) {
      console.error('登录失败', e)
      wx.showToast({ 
        title: e.data?.detail || '登录失败', 
        icon: 'none' 
      })
    } finally {
      this.setData({ isLogging: false })
    }
  },

  goToRegister() {
    wx.navigateTo({ url: '/pages/register/register' })
  },

  goToForgotPassword() {
    wx.navigateTo({ url: '/pages/forgot-password/forgot-password' })
  },

  showTerms() {
    wx.navigateTo({ url: '/pages/terms/terms' })
  },

  showPrivacy() {
    wx.navigateTo({ url: '/pages/privacy/privacy' })
  }
})
