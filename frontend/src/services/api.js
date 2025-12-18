import axios from 'axios';

// В dev режиме используем относительный путь /api (проксируется через Vite на localhost:8000)
// В production используем переменную окружения или относительный путь
const API_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Добавление токена аутентификации к каждому запросу
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Обработка ошибок и ограничения частоты запросов
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const { status, data } = error.response;

      // Обработка превышения лимита запросов (код 429)
      if (status === 429) {
        const message = data.detail || 'Слишком много запросов. Пожалуйста, подождите немного и попробуйте снова.';
        alert(message);
        console.warn('Rate limit exceeded:', data);
      }

      // Обработка ошибок аутентификации (код 401)
      else if (status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }

      // Обработка серверных ошибок (коды 500 и выше)
      else if (status >= 500) {
        const message = data.detail || 'Ошибка сервера. Пожалуйста, попробуйте позже.';
        console.error('Server error:', data);
        alert(message);
      }

      // Обработка ошибок валидации данных (коды 400, 422)
      else if (status === 400 || status === 422) {
        console.warn('Validation error:', data);
        // Детали ошибок обрабатываются в соответствующих компонентах
      }
    } else if (error.request) {
      // Запрос был отправлен, но ответ не получен
      console.error('Network error:', error.request);
      alert('Ошибка сети. Проверьте подключение к интернету.');
    } else {
      // Ошибка при формировании запроса
      console.error('Request error:', error.message);
    }

    return Promise.reject(error);
  }
);

export default api;

