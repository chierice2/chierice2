import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL + '/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use(async (config) => {
  const token = await AsyncStorage.getItem('@LocalGuide:token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authService = {
  login: async (email: string, password: string) => {
    const response = await api.post('/auth/login', { email, password });
    return response.data;
  },
  register: async (email: string, password: string, name: string, preferred_language: string) => {
    const response = await api.post('/auth/register', { 
      email, 
      password, 
      name, 
      preferred_language 
    });
    return response.data;
  },
  getMe: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },
};

export const cityService = {
  getAll: async () => {
    const response = await api.get('/cities');
    return response.data;
  },
  getById: async (id: string) => {
    const response = await api.get(`/cities/${id}`);
    return response.data;
  },
};

export const eventService = {
  getAll: async (cityId?: string) => {
    const params = cityId ? { city_id: cityId } : {};
    const response = await api.get('/events', { params });
    return response.data;
  },
  getById: async (id: string) => {
    const response = await api.get(`/events/${id}`);
    return response.data;
  },
};

export const placeService = {
  getAll: async (cityId?: string, category?: string) => {
    const params: any = {};
    if (cityId) params.city_id = cityId;
    if (category) params.category = category;
    const response = await api.get('/places', { params });
    return response.data;
  },
  getById: async (id: string) => {
    const response = await api.get(`/places/${id}`);
    return response.data;
  },
};

export const accommodationService = {
  getAll: async (cityId?: string) => {
    const params = cityId ? { city_id: cityId } : {};
    const response = await api.get('/accommodations', { params });
    return response.data;
  },
  getById: async (id: string) => {
    const response = await api.get(`/accommodations/${id}`);
    return response.data;
  },
};

export const itineraryService = {
  getAll: async (cityId?: string, type?: string) => {
    const params: any = {};
    if (cityId) params.city_id = cityId;
    if (type) params.type = type;
    const response = await api.get('/itineraries', { params });
    return response.data;
  },
  getById: async (id: string) => {
    const response = await api.get(`/itineraries/${id}`);
    return response.data;
  },
};

export const favoriteService = {
  getAll: async () => {
    const response = await api.get('/favorites');
    return response.data;
  },
  add: async (itemType: string, itemId: string) => {
    const response = await api.post('/favorites', { item_type: itemType, item_id: itemId });
    return response.data;
  },
  remove: async (favoriteId: string) => {
    await api.delete(`/favorites/${favoriteId}`);
  },
  removeByItem: async (itemType: string, itemId: string) => {
    await api.delete(`/favorites/by-item/${itemType}/${itemId}`);
  },
};

export const seedService = {
  seed: async () => {
    const response = await api.post('/seed');
    return response.data;
  },
};

export default api;