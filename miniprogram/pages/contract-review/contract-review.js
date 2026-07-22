const api = require('../../utils/api.js')
const auth = require('../../utils/auth.js')

Page({
  data: {
    contractType: '',
    contractText: '',
    stance: '审查方',
    isAnalyzing: false,
    reviewResult: null,
    reviewId: '',
    contractTypes: [
      '借款合同',
      '买卖合同',
      '租赁合同',
      '劳动合同',
      '服务合同',
      '技术合同',
      '建设工程合同',
      '其他'
    ],
    stances: ['审查方', '甲方', '乙方']
  },

  onLoad() {
    auth.requireLogin()
  },

  onContractTypeChange(e) {
    const index = e.detail.value
    this.setData({ contractType: this.data.contractTypes[index] })
  },

  onStanceChange(e) {
    const index = e.detail.value
    this.setData({ stance: this.data.stances[index] })
  },

  onTextInput(e) {
    this.setData({ contractText: e.detail.value })
  },

  chooseImage() {
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        const tempFile = res.tempFiles[0]
        this.uploadImage(tempFile.tempFilePath)
      }
    })
  },

  chooseFile() {
    wx.chooseMessageFile({
      count: 1,
      type: 'file',
      extension: ['doc', 'docx', 'pdf', 'txt'],
      success: (res) => {
        const file = res.tempFiles[0]
        this.uploadFile(file.path, file.name)
      }
    })
  },

  async uploadImage(filePath) {
    if (!auth.requireLogin()) return
    
    try {
      wx.showLoading({ title: '识别中...' })
      const res = await api.uploadFile({
        url: '/api/contract-review/ocr',
        filePath: filePath,
        name: 'file'
      })
      wx.hideLoading()
      if (res.contract_text) {
        this.setData({ contractText: res.contract_text })
        wx.showToast({ title: '识别成功', icon: 'success' })
      }
    } catch (e) {
      wx.hideLoading()
      wx.showToast({ title: '识别失败', icon: 'none' })
    }
  },

  async uploadFile(filePath, fileName) {
    if (!auth.requireLogin()) return
    
    try {
      wx.showLoading({ title: '上传中...' })
      const res = await api.uploadFile({
        url: '/api/contract-review/upload-file',
        filePath: filePath,
        name: 'file',
        formData: {
          file_name: fileName
        }
      })
      wx.hideLoading()
      if (res.contract_text) {
        this.setData({ contractText: res.contract_text })
        wx.showToast({ title: '上传成功', icon: 'success' })
      }
    } catch (e) {
      wx.hideLoading()
      wx.showToast({ title: '上传失败', icon: 'none' })
    }
  },

  async startReview() {
    if (!auth.requireLogin()) return
    
    if (!this.data.contractText.trim()) {
      wx.showToast({ title: '请输入或上传合同内容', icon: 'none' })
      return
    }

    if (!this.data.contractType) {
      wx.showToast({ title: '请选择合同类型', icon: 'none' })
      return
    }

    this.setData({ isAnalyzing: true, reviewResult: null })

    try {
      const res = await api.request({
        url: '/api/contract-review/upload',
        method: 'POST',
        data: {
          contract_type: this.data.contractType,
          contract_text: this.data.contractText,
          stance: this.data.stance
        }
      })

      if (res.review_id) {
        this.setData({ reviewId: res.review_id })
        await this.getReviewResult(res.review_id)
      }
    } catch (e) {
      console.error('合同审查失败', e)
      wx.showToast({ title: '审查失败', icon: 'none' })
    } finally {
      this.setData({ isAnalyzing: false })
    }
  },

  async getReviewResult(reviewId) {
    try {
      const res = await api.request({
        url: `/api/contract-review/result/${reviewId}`,
        method: 'GET'
      })
      this.setData({ reviewResult: res })
    } catch (e) {
      console.error('获取审查结果失败', e)
    }
  },

  viewRiskDetail(e) {
    const index = e.currentTarget.dataset.index
    const risk = this.data.reviewResult.risks[index]
    wx.showModal({
      title: risk.title || '风险详情',
      content: risk.description || risk.detail || '暂无详情',
      showCancel: false
    })
  },

  resetReview() {
    this.setData({
      contractType: '',
      contractText: '',
      reviewResult: null,
      reviewId: ''
    })
  },

  exportReport() {
    if (!this.data.reviewId) return
    
    wx.showActionSheet({
      itemList: ['导出 PDF 报告', '导出 Markdown'],
      success: (res) => {
        this.doExport(res.tapIndex === 0 ? 'pdf' : 'markdown')
      }
    })
  },

  async doExport(format) {
    try {
      wx.showLoading({ title: '生成中...' })
      const res = await api.request({
        url: '/api/contract-review/export',
        method: 'POST',
        data: {
          review_id: this.data.reviewId,
          format: format
        }
      })
      wx.hideLoading()
      wx.showToast({ title: '导出成功', icon: 'success' })
    } catch (e) {
      wx.hideLoading()
      wx.showToast({ title: '导出失败', icon: 'none' })
    }
  }
})
