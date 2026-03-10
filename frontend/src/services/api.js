import axios from 'axios';

const API_BASE = '/api';

const api = axios.create({
    baseURL: API_BASE,
    headers: { 'Content-Type': 'application/json' },
});

// ── Attach JWT to every request ─────────────────────────
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// ── Handle 401 globally ─────────────────────────────────
api.interceptors.response.use(
    (res) => res,
    (err) => {
        if (err.response?.status === 401) {
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            window.location.href = '/login';
        }
        return Promise.reject(err);
    }
);

// ── Auth ─────────────────────────────────────────────────
export const loginAPI = (username, password) =>
    api.post('/auth/login', { username, password });

// ── Predict ──────────────────────────────────────────────
export const uploadImageAPI = (formData) =>
    api.post('/predict/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
    });

// ── Patients ─────────────────────────────────────────────
export const getHistoryAPI = (skip = 0, limit = 50, search = '') =>
    api.get('/patients/history', { params: { skip, limit, search } });

export const getRecordAPI = (id) => api.get(`/patients/${id}`);

export const getStatsAPI = () => api.get('/patients/stats');

export default api;
