export const endpoints = {
  baseUrl: __ENV.BASE_URL || 'http://127.0.0.1:8000',
  
  // Travel Plans endpoints
  travelPlans: {
    list: '/api/travel-plans/',
    create: '/api/travel-plans/',
    getById: (id) => `/api/travel-plans/${id}`,
    update: (id) => `/api/travel-plans/${id}`,
    delete: (id) => `/api/travel-plans/${id}`,
    addLocation: (id) => `/api/travel-plans/${id}/locations`,
  },
  
  // Locations endpoints
  locations: {
    list: '/api/locations/',
    create: '/api/locations/',
    getById: (id) => `/api/locations/${id}`,
    update: (id) => `/api/locations/${id}`,
    delete: (id) => `/api/locations/${id}`,
  },
  
  // Health check
  health: '/health',
};

