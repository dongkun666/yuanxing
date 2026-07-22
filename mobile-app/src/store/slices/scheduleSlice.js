import {createSlice, createAsyncThunk} from '@reduxjs/toolkit';
import {scheduleApi} from '../../api';

export const fetchSchedule = createAsyncThunk(
  'schedule/fetchSchedule',
  async (params = {}, {rejectWithValue}) => {
    try {
      const response = await scheduleApi.getSchedule(params);
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || '获取日程失败');
    }
  },
);

export const fetchTodaySchedule = createAsyncThunk(
  'schedule/fetchTodaySchedule',
  async (_, {rejectWithValue}) => {
    try {
      const response = await scheduleApi.getTodaySchedule();
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || '获取今日日程失败');
    }
  },
);

export const createSchedule = createAsyncThunk(
  'schedule/createSchedule',
  async (data, {rejectWithValue}) => {
    try {
      const response = await scheduleApi.createSchedule(data);
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || '创建日程失败');
    }
  },
);

export const updateSchedule = createAsyncThunk(
  'schedule/updateSchedule',
  async ({id, data}, {rejectWithValue}) => {
    try {
      const response = await scheduleApi.updateSchedule(id, data);
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || '更新日程失败');
    }
  },
);

export const deleteSchedule = createAsyncThunk(
  'schedule/deleteSchedule',
  async (id, {rejectWithValue}) => {
    try {
      await scheduleApi.deleteSchedule(id);
      return id;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || '删除日程失败');
    }
  },
);

const scheduleSlice = createSlice({
  name: 'schedule',
  initialState: {
    list: [],
    todayList: [],
    loading: false,
    todayLoading: false,
    creating: false,
    error: null,
  },
  reducers: {},
  extraReducers: builder => {
    builder
      .addCase(fetchSchedule.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchSchedule.fulfilled, (state, action) => {
        state.loading = false;
        state.list = action.payload || [];
      })
      .addCase(fetchSchedule.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      .addCase(fetchTodaySchedule.pending, state => {
        state.todayLoading = true;
        state.error = null;
      })
      .addCase(fetchTodaySchedule.fulfilled, (state, action) => {
        state.todayLoading = false;
        state.todayList = action.payload || [];
      })
      .addCase(fetchTodaySchedule.rejected, (state, action) => {
        state.todayLoading = false;
        state.error = action.payload;
      })
      .addCase(createSchedule.pending, state => {
        state.creating = true;
      })
      .addCase(createSchedule.fulfilled, (state, action) => {
        state.creating = false;
        state.list = [action.payload, ...state.list];
      })
      .addCase(createSchedule.rejected, (state, action) => {
        state.creating = false;
        state.error = action.payload;
      })
      .addCase(deleteSchedule.fulfilled, (state, action) => {
        state.list = state.list.filter(item => item.id !== action.payload);
        state.todayList = state.todayList.filter(item => item.id !== action.payload);
      });
  },
});

export default scheduleSlice.reducer;
