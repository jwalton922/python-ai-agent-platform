/**
 * Test utility for API configuration
 * Run this in browser console to test different configurations
 */

import { apiConfig, getApiBaseUrl, setApiConfig } from './apiConfig';
import { reinitializeApi } from '../services/api';

export const testApiConfig = {
  /**
   * Test current configuration
   */
  current: () => {
    console.log('Current API Configuration:');
    console.log('Base URL:', getApiBaseUrl());
    console.log('Full config:', apiConfig.getConfig());
    return apiConfig.getConfig();
  },

  /**
   * Test with Jupyter notebook proxy path
   */
  testJupyter: () => {
    console.log('Testing Jupyter proxy configuration...');
    setApiConfig({
      baseUrl: '/notebook/pxj363/josh-testing/proxy/8000',
      basePath: '/notebook/pxj363/josh-testing/proxy/8000'
    });
    reinitializeApi();
    console.log('New API Base URL:', getApiBaseUrl());
    return apiConfig.getConfig();
  },

  /**
   * Test with simple proxy path
   */
  testProxy: (port: number = 8000) => {
    console.log(`Testing proxy/${port} configuration...`);
    setApiConfig({
      baseUrl: `/proxy/${port}`,
      basePath: `/proxy/${port}`
    });
    reinitializeApi();
    console.log('New API Base URL:', getApiBaseUrl());
    return apiConfig.getConfig();
  },

  /**
   * Test with custom base path
   */
  testCustom: (basePath: string) => {
    console.log(`Testing custom base path: ${basePath}`);
    setApiConfig({
      baseUrl: basePath,
      basePath: basePath
    });
    reinitializeApi();
    console.log('New API Base URL:', getApiBaseUrl());
    return apiConfig.getConfig();
  },

  /**
   * Reset to auto-detection
   */
  reset: () => {
    console.log('Resetting to auto-detection...');
    apiConfig.reset();
    reinitializeApi();
    console.log('New API Base URL:', getApiBaseUrl());
    return apiConfig.getConfig();
  },

  /**
   * Make a test API call
   */
  testCall: async () => {
    console.log('Making test API call to /health...');
    try {
      const response = await fetch(getApiBaseUrl().replace('/api', '/health'));
      const data = await response.json();
      console.log('Health check response:', data);
      return data;
    } catch (error) {
      console.error('Health check failed:', error);
      throw error;
    }
  }
};

// Export to window for easy console access in development
if (process.env.NODE_ENV === 'development') {
  (window as any).testApiConfig = testApiConfig;
  console.log('API Config Test Utility loaded. Use window.testApiConfig to test configurations.');
}