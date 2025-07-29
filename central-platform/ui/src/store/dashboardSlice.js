import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8005/api';

export const fetchMetrics = createAsyncThunk('dashboard/fetchMetrics', async () => {
  const response = await axios.get(`${API_BASE_URL}/metrics`);
  return response.data;
});

export const fetchWorkflows = createAsyncThunk('dashboard/fetchWorkflows', async () => {
  const response = await axios.get(`${API_BASE_URL}/workflows`);
  return response.data;
});

export const fetchComponents = createAsyncThunk('dashboard/fetchComponents', async () => {
  const response = await axios.get(`${API_BASE_URL}/components`);
  return response.data;
});

const initialState = {
  metrics: {
    activeWorkflows: 0,
    completedTasks: 0,
    systemHealth: '0%',
    alerts: 0,
  },
  workflows: [],
  components: [],
  loading: false,
  error: null,
};

export const dashboardSlice = createSlice({
  name: 'dashboard',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchMetrics.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchMetrics.fulfilled, (state, action) => {
        state.metrics = action.payload;
        state.loading = false;
      })
      .addCase(fetchMetrics.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      })
      .addCase(fetchWorkflows.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchWorkflows.fulfilled, (state, action) => {
        state.workflows = action.payload;
        state.loading = false;
      })
      .addCase(fetchWorkflows.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      })
      .addCase(fetchComponents.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchComponents.fulfilled, (state, action) => {
        state.components = action.payload;
        state.loading = false;
      })
      .addCase(fetchComponents.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      });
  },
});

export default dashboardSlice.reducer;