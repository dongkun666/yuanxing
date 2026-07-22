const api = require('./api.js')
const app = getApp()

function login() {
  return new Promise((resolve, reject) => {
    wx.login({
      success: async (res) => {
        if (res.code) {
          try {
            const result = await api.request({
              url: '/api/gateway/wx-mini/login',
              method: 'POST',
              data: {
                code: res.code
              }
            })
            if (result.access_token) {
              wx.setStorageSync('access_token', result.access_token)
              wx.setStorageSync('refresh_token', result.refresh_token)
              app.globalData.token = result.access_token
              resolve(result)
            } else {
              reject(new Error('登录失败'))
            }
          } catch (err) {
            reject(err)
          }
        } else {
          reject(new Error('获取微信登录凭证失败'))
        }
      },
      fail: reject
    })
  })
}

function getUserProfile() {
  return new Promise((resolve, reject) => {
    wx.getUserProfile({
      desc: '用于完善会员资料',
      success: (res) => {
        resolve(res.userInfo)
      },
      fail: reject
    })
  })
}

async function updateUserInfo(userInfo) {
  try {
    const result = await api.request({
      url: '/api/gateway/wx-mini/update-profile',
      method: 'PUT',
      data: userInfo
    })
    app.globalData.userInfo = result
    wx.setStorageSync('user_info', result)
    return result
  } catch (err) {
    throw err
  }
}

function isLoggedIn() {
  const token = wx.getStorageSync('access_token')
  return !!token
}

function logout() {
  wx.removeStorageSync('access_token')
  wx.removeStorageSync('refresh_token')
  wx.removeStorageSync('user_info')
  if (app.globalData) {
    app.globalData.token = null
    app.globalData.userInfo = null
  }
}

function requireLogin(page) {
  if (!isLoggedIn()) {
    wx.navigateTo({
      url: '/pages/login/login'
    })
    return false
  }
  return true
}

module.exports = {
  login,
  getUserProfile,
  updateUserInfo,
  isLoggedIn,
  logout,
  requireLogin
}
