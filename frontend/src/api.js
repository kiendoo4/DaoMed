import axios from "axios";

// Create axios instance with base configuration
const api = axios.create({
  baseURL: "http://localhost:5050",
  timeout: 120000, // Increased to 2 minutes
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log("API Request:", config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    console.error("API Request Error:", error);
    return Promise.reject(error);
  }
);

// Response interceptor for logging
api.interceptors.response.use(
  (response) => {
    console.log("API Response:", response.status, response.config.url);
    return response;
  },
  (error) => {
    console.error(
      "API Response Error:",
      error.response?.status,
      error.config?.url,
      error.message
    );
    return Promise.reject(error);
  }
);

// API functions
export const authAPI = {
  login: (credentials) => api.post("/api/chat/login", credentials),
  register: (userData) => api.post("/api/chat/register", userData),
  logout: () => api.post("/api/chat/logout"),
};

export const chatAPI = {
  sendMessage: (dialogId, message) =>
    api.post(`/api/dialog/${dialogId}/chat`, {
      message,
    }),
  getHistory: () => api.get("/api/chat/history"),
  getConversations: () => api.get("/api/chat/conversations"),
};

export const kbAPI = {
  list: () => api.get("/api/kb/list"),
  upload: (formData, onUploadProgress) =>
    api.post("/api/kb/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 300000, // 5 minutes for upload
      onUploadProgress: onUploadProgress,
    }),
  delete: (id) => api.delete(`/api/kb/${id}`),
  getChunks: (id) => api.get(`/api/kb/${id}/chunks`),
};

export const evaluationAPI = {
  evaluate: (data) => api.post("/api/eval/evaluate", data),
};

export default api;
