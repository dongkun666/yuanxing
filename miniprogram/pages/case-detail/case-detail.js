const api = require('../../utils/api.js')
const auth = require('../../utils/auth.js')

Page({
  data: {
    docId: '',
    caseDetail: null,
    loading: true,
    isFavorite: false,
    showFullText: false
  },

  onLoad(options) {
    if (options.docId) {
      this.setData({ docId: options.docId })
      this.loadCaseDetail()
    }
  },

  onShareAppMessage() {
    return {
      title: this.data.caseDetail?.case_name || 'LexPrime 判例详情',
      path: `/pages/case-detail/case-detail?docId=${this.data.docId}`
    }
  },

  async loadCaseDetail() {
    this.setData({ loading: true })
    try {
      const res = await api.request({
        url: `/api/cases/${this.data.docId}`,
        method: 'GET'
      })
      this.setData({ caseDetail: res })
    } catch (e) {
      console.error('加载案件详情失败', e)
      wx.showToast({ title: '加载失败', icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  },

  toggleFullText() {
    this.setData({ showFullText: !this.data.showFullText })
  },

  async toggleFavorite() {
    if (!auth.requireLogin()) return
    
    try {
      if (this.data.isFavorite) {
        await api.request({
          url: `/api/cases/${this.data.docId}/favorite`,
          method: 'DELETE'
        })
        wx.showToast({ title: '已取消收藏', icon: 'success' })
      } else {
        await api.request({
          url: `/api/cases/${this.data.docId}/favorite`,
          method: 'POST'
        })
        wx.showToast({ title: '已收藏', icon: 'success' })
      }
      this.setData({ isFavorite: !this.data.isFavorite })
    } catch (e) {
      console.error('收藏操作失败', e)
    }
  },

  shareCase() {
    wx.showShareMenu({
      withShareTicket: true,
      menus: ['shareAppMessage', 'shareTimeline']
    })
  },

  exportCase() {
    wx.showActionSheet({
      itemList: ['导出为 PDF', '导出为 Word', '复制链接'],
      success: (res) => {
        switch (res.tapIndex) {
          case 0:
            this.exportPDF()
            break
          case 1:
            this.exportWord()
            break
          case 2:
            this.copyLink()
            break
        }
      }
    })
  },

  async exportPDF() {
    try {
      wx.showLoading({ title: '生成中...' })
      const res = await api.request({
        url: `/api/cases/${this.data.docId}/export?format=pdf`,
        method: 'GET'
      })
      wx.hideLoading()
      wx.showToast({ title: '导出成功', icon: 'success' })
    } catch (e) {
      wx.hideLoading()
      wx.showToast({ title: '导出失败', icon: 'none' })
    }
  },

  async exportWord() {
    try {
      wx.showLoading({ title: '生成中...' })
      const res = await api.request({
        url: `/api/cases/${this.data.docId}/export?format=word`,
        method: 'GET'
      })
      wx.hideLoading()
      wx.showToast({ title: '导出成功', icon: 'success' })
    } catch (e) {
      wx.hideLoading()
      wx.showToast({ title: '导出失败', icon: 'none' })
    }
  },

  copyLink() {
    const link = `https://lexprime.com/cases/${this.data.docId}`
    wx.setClipboardData({
      data: link,
      success: () => {
        wx.showToast({ title: '链接已复制', icon: 'success' })
      }
    })
  }
})
