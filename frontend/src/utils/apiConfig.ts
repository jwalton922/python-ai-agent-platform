/**
 * API Configuration Utility
 * Dynamically determines the API base path from various sources
 */

interface ApiConfig {
  baseUrl: string;
  basePath: string;
}

class ApiConfigManager {
  private config: ApiConfig | null = null;

  /**
   * Get API configuration, checking multiple sources in order of priority:
   * 1. Window global variable (for runtime configuration)
   * 2. Environment variable (build-time)
   * 3. URL path detection
   * 4. Default fallback
   */
  getConfig(): ApiConfig {
    if (this.config) {
      return this.config;
    }

    // Method 1: Check for runtime configuration in window object
    // This allows injecting configuration at runtime via script tag
    if (typeof window !== 'undefined' && (window as any).API_CONFIG) {
      const windowConfig = (window as any).API_CONFIG;
      this.config = {
        baseUrl: windowConfig.baseUrl || '',
        basePath: windowConfig.basePath || ''
      };
      console.log('API Config from window:', this.config);
      return this.config;
    }

    // Method 2: Check environment variables (build time)
    if (process.env.REACT_APP_BASE_PATH) {
      this.config = {
        baseUrl: process.env.REACT_APP_BASE_PATH,
        basePath: process.env.REACT_APP_BASE_PATH
      };
      console.log('API Config from env:', this.config);
      return this.config;
    }

    // Method 3: Detect from current URL path
    if (typeof window !== 'undefined') {
      const path = window.location.pathname;
      
      // Check if we're running under a known proxy pattern
      const proxyPatterns = [
        /^\/notebook\/[^\/]+\/[^\/]+\/proxy\/\d+/,  // Jupyter notebook proxy
        /^\/proxy\/\d+/,  // Simple proxy
        /^\/app/,  // Deployed under /app
      ];
      
      for (const pattern of proxyPatterns) {
        const match = path.match(pattern);
        if (match) {
          // Extract base path up to /proxy/PORT or /app
          let basePath = match[0];
          
          // Remove /app from the end if present (that's our app mount point)
          if (basePath.endsWith('/app')) {
            basePath = basePath.slice(0, -4);
          }
          
          this.config = {
            baseUrl: basePath,
            basePath: basePath
          };
          console.log('API Config detected from URL:', this.config);
          return this.config;
        }
      }
    }

    // Method 4: Use PUBLIC_URL if set
    const publicUrl = process.env.PUBLIC_URL || '';
    if (publicUrl && publicUrl !== '/app') {
      // Extract base path from PUBLIC_URL (remove /app suffix)
      const basePath = publicUrl.replace(/\/app$/, '');
      this.config = {
        baseUrl: basePath,
        basePath: basePath
      };
      console.log('API Config from PUBLIC_URL:', this.config);
      return this.config;
    }

    // Default: No prefix (standard deployment)
    this.config = {
      baseUrl: '',
      basePath: ''
    };
    console.log('API Config using default (no prefix)');
    return this.config;
  }

  /**
   * Build a full API URL with the base path
   */
  buildUrl(endpoint: string): string {
    const config = this.getConfig();
    
    // Ensure endpoint starts with /
    if (!endpoint.startsWith('/')) {
      endpoint = '/' + endpoint;
    }
    
    // Build full URL
    return config.baseUrl + endpoint;
  }

  /**
   * Get the API base URL for axios or fetch
   */
  getApiBaseUrl(): string {
    const config = this.getConfig();
    return config.baseUrl + '/api';
  }

  /**
   * Override configuration at runtime
   * Useful for testing or dynamic reconfiguration
   */
  setConfig(config: Partial<ApiConfig>): void {
    this.config = {
      baseUrl: config.baseUrl || '',
      basePath: config.basePath || config.baseUrl || ''
    };
    console.log('API Config manually set:', this.config);
  }

  /**
   * Reset configuration (forces re-detection)
   */
  reset(): void {
    this.config = null;
  }
}

// Export singleton instance
export const apiConfig = new ApiConfigManager();

// Export convenience functions
export const getApiBaseUrl = () => apiConfig.getApiBaseUrl();
export const buildApiUrl = (endpoint: string) => apiConfig.buildUrl(endpoint);
export const setApiConfig = (config: Partial<ApiConfig>) => apiConfig.setConfig(config);

// For debugging in development
if (process.env.NODE_ENV === 'development') {
  (window as any).apiConfig = apiConfig;
}