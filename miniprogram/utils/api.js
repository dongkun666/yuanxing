const app = getApp()

const BASE_URL = 'https://api.lexprime.com'

function request(options) {
  return new Promise((resolve, reject) => {
    const token = wx.getStorageSync('access_token')
    const header = {
      'Content-Type': 'application/json',
      ...options.header
    }
    
    if (token) {
      header['Authorization'] = `Bearer ${token}`
    }

    wx.request({
      url: BASE_URL + options.url,
      method: options.method || 'GET',
      data: options.data || {},
      header: header,
      success: (res) => {
        if (res.statusCode === 200) {
          resolve(res.data)
        } else if (res.statusCode === 401) {
          wx.removeStorageSync('access_token')
          wx.showToast({
            title: '登录已过期',
            icon: 'none'
          })
          reject(res)
        } else {
          wx.showToast({
            title: res.data?.detail || res.data?.message || '请求失败',
            icon: 'none'
          })
          reject(res)
        }
      },
      fail: (err) => {
        wx.showToast({
          title: '网络错误',
          icon: 'none'
        })
        reject(err)
      }
    })
  })
}

function uploadFile(options) {
  return new Promise((resolve, reject) => {
    const token = wx.getStorageSync('access_token')
    const header = {}
    
    if (token) {
      header['Authorization'] = `Bearer ${token}`
    }

    wx.uploadFile({
      url: BASE_URL + options.url,
      filePath: options.filePath,
      name: options.name || 'file',
      formData: options.formData || {},
      header: header,
      success: (res) => {
        const data = JSON.parse(res.data)
        if (res.statusCode === 200) {
          resolve(data)
        } else {
          wx.showToast({
            title: data.detail || data.message || '上传失败',
            icon: 'none'
          })
          reject(res)
        }
      },
      fail: (err) => {
        wx.showToast({
          title: '上传失败',
          icon: 'none'
        })
        reject(err)
      }
    })
  })
}

module.exports = {
  request,
  uploadFile,
  BASE_URL
}
