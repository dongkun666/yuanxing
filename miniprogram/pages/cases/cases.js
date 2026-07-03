const api = require('../../utils/api.js')
const auth = require('../../utils/auth.js')

Page({
  data: {
    cases: [],
    keyword: '',
    causeCategory: '',
    year: '',
    court: '',
    loading: false,
    hasMore: true,
    page: 1,
    pageSize: 20,
    showFilter: false,
    categories: [
      { label: '全部', value: '' },
      { label: '合同纠纷', value: '合同纠纷' },
      { label: '侵权纠纷', value: '侵权纠纷' },
      { label: '婚姻家庭', value: '婚姻家庭' },
      { label: '劳动争议', value: '劳动争议' },
      { label: '知识产权', value: '知识产权' },
      { label: '刑事', value: '刑事' },
      { label: '行政', value: '行政' }
    ]
  },

  onLoad(options) {
    if (options.keyword) {
      this.setData({ keyword: decodeURIComponent(options.keyword) })
    }
    this.loadCases()
  },

  onPullDownRefresh() {
    this.setData({ page: 1, cases: [], hasMore: true })
    this.loadCases().then(() => {
      wx.stopPullDownRefresh()
    })
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) {
      this.setData({ page: this.data.page + 1 })
      this.loadCases()
    }
  },

  async loadCases() {
    if (this.data.loading) return
    
    this.setData({ loading: true })
    
    try {
      const params = []
      params.push(`limit=${this.data.pageSize}`)
      params.push(`offset=${(this.data.page - 1) * this.data.pageSize}`)
      
      if (this.data.keyword) {
        params.push(`cause=${encodeURIComponent(this.data.keyword)}`)
      }
      if (this.data.causeCategory) {
        params.push(`cause_category=${encodeURIComponent(this.data.causeCategory)}`)
      }
      if (this.data.year) {
        params.push(`year=${this.data.year}`)
      }
      if (this.data.court) {
        params.push(`court=${encodeURIComponent(this.data.court)}`)
      }

      const res = await api.request({
        url: `/api/cases?${params.join('&')}`,
        method: 'GET'
      })

      const newCases = res || []
      const hasMore = newCases.length === this.data.pageSize
      
      this.setData({
        cases: this.data.page === 1 ? newCases : [...this.data.cases, ...newCases],
        hasMore
      })
    } catch (e) {
      console.error('加载判例失败', e)
      wx.showToast({ title: '加载失败', icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  },

  onSearchInput(e) {
    this.setData({ keyword: e.detail.value })
  },

  onSearch() {
    this.setData({ page: 1, cases: [], hasMore: true })
    this.loadCases()
  },

  onCategoryTap(e) {
    const value = e.currentTarget.dataset.value
    this.setData({ 
      causeCategory: value,
      page: 1, 
      cases: [], 
      hasMore: true 
    })
    this.loadCases()
  },

  toggleFilter() {
    this.setData({ showFilter: !this.data.showFilter })
  },

  onCaseTap(e) {
    const docId = e.currentTarget.dataset.docId
    wx.navigateTo({
      url: `/pages/case-detail/case-detail?docId=${docId}`
    })
  }
})
