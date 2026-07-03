import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

const API_BASE_URL = process.env.NODE_ENV === 'development'
  ? 'http://localhost:8081'
  : 'https://api.lexprime.cn';

const createAxiosInstance = (): AxiosInstance => {
  const instance = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  instance.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem('lexprime_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  instance.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };
      
      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;
        
        try {
          const refreshToken = localStorage.getItem('lexprime_refresh_token');
          if (refreshToken) {
            const response = await axios.post(`${API_BASE_URL}/api/auth/refresh`, {
              refresh_token: refreshToken,
            });
            
            const { access_token, refresh_token: newRefreshToken } = response.data;
            localStorage.setItem('lexprime_token', access_token);
            localStorage.setItem('lexprime_refresh_token', newRefreshToken);
            
            originalRequest.headers!.Authorization = `Bearer ${access_token}`;
            return instance(originalRequest);
          }
        } catch (err) {
          localStorage.removeItem('lexprime_token');
          localStorage.removeItem('lexprime_refresh_token');
          window.location.href = '/login';
        }
      }
      
      return Promise.reject(error);
    }
  );

  return instance;
};

export const apiClient = createAxiosInstance();

export const requestWithRetry = async <T>(
  fn: () => Promise<AxiosResponse<T>>,
  maxRetries: number = 3
): Promise<AxiosResponse<T>> => {
  let lastError: unknown;
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      if (i < maxRetries - 1) {
        await new Promise((resolve) => setTimeout(resolve, Math.pow(2, i) * 1000));
      }
    }
  }
  
  throw lastError;
};