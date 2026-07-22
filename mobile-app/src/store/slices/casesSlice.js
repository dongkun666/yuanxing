import {createSlice, createAsyncThunk} from '@reduxjs/toolkit';
import {casesApi} from '../../api';

export const fetchCases = createAsyncThunk(
  'cases/fetchCases',
  async (params = {}, {rejectWithValue}) => {
    try {
      const response = await casesApi.getCases(params);
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || '获取判例失败');
    }
  },
);

export const searchCases = createAsyncThunk(
  'cases/searchCases',
  async ({query, filters}, {rejectWithValue}) => {
    try {
      const response = await casesApi.searchCases(query, filters);
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || '搜索失败');
    }
  },
);

export const fetchCaseDetail = createAsyncThunk(
  'cases/fetchCaseDetail',
  async (docId, {rejectWithValue}) => {
    try {
      const response = await casesApi.getCaseDetail(docId);
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || '获取案件详情失败');
    }
  },
);

const casesSlice = createSlice({
  name: 'cases',
  initialState: {
    list: [],
    detail: null,
    searchResults: [],
    searchTotal: 0,
    loading: false,
    detailLoading: false,
    searchLoading: false,
    error: null,
    page: 1,
    hasMore: true,
  },
  reducers: {
    resetCases: state => {
      state.list = [];
      state.page = 1;
      state.hasMore = true;
    },
    resetDetail: state => {
      state.detail = null;
    },
  },
  extraReducers: builder => {
    builder
      .addCase(fetchCases.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchCases.fulfilled, (state, action) => {
        state.loading = false;
        const newCases = action.payload || [];
        if (state.page === 1) {
          state.list = newCases;
        } else {
          state.list = [...state.list, ...newCases];
        }
        state.hasMore = newCases.length === 20;
      })
      .addCase(fetchCases.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      .addCase(fetchCaseDetail.pending, state => {
        state.detailLoading = true;
        state.error = null;
      })
      .addCase(fetchCaseDetail.fulfilled, (state, action) => {
        state.detailLoading = false;
        state.detail = action.payload;
      })
      .addCase(fetchCaseDetail.rejected, (state, action) => {
        state.detailLoading = false;
        state.error = action.payload;
      })
      .addCase(searchCases.pending, state => {
        state.searchLoading = true;
        state.error = null;
      })
      .addCase(searchCases.fulfilled, (state, action) => {
        state.searchLoading = false;
        state.searchResults = action.payload.items;
        state.searchTotal = action.payload.total;
      })
      .addCase(searchCases.rejected, (state, action) => {
        state.searchLoading = false;
        state.error = action.payload;
      });
  },
});

export const {resetCases, resetDetail} = casesSlice.actions;
export default casesSlice.reducer;
