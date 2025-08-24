// Configuration for API endpoints with support for proxy environments

// Get the base path from the build-time PUBLIC_URL or default to empty
const PUBLIC_URL = process.env.PUBLIC_URL || '';

// Extract the base path (everything before /app)
const BASE_PATH = PUBLIC_URL.replace(/\/app$/, '');

// API base URL for all API calls
export const API_BASE_URL = BASE_PATH + '/api';

// Specific API endpoints
export const API_ENDPOINTS = {
  // Agent endpoints
  agents: `${API_BASE_URL}/agents`,
  
  // Workflow endpoints  
  workflows: `${API_BASE_URL}/workflows`,
  
  // Activity endpoints
  activities: `${API_BASE_URL}/activities`,
  
  // Chat endpoints
  chat: `${API_BASE_URL}/chat`,
  
  // Health check
  health: `${BASE_PATH}/health`,
} as const;

// Helper function to build API URLs
export function buildApiUrl(endpoint: string, params?: Record<string, any>): string {
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;
  
  if (params) {
    const queryString = new URLSearchParams(params).toString();
    return queryString ? `${url}?${queryString}` : url;
  }
  
  return url;
}

// Export for debugging
if (process.env.NODE_ENV === 'development') {
  console.log('Config loaded:', {
    PUBLIC_URL,
    BASE_PATH,
    API_BASE_URL,
    API_ENDPOINTS
  });
}