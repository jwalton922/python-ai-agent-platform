/**
 * Proxy configuration for development server
 * This allows testing with different base paths in development
 */

const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // Get base path from environment or use default
  const BASE_PATH = process.env.REACT_APP_BASE_PATH || '';
  
  // Proxy API requests
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://localhost:8000',
      changeOrigin: true,
      pathRewrite: BASE_PATH ? {
        '^/api': `${BASE_PATH}/api`
      } : undefined,
      onProxyReq: (proxyReq, req, res) => {
        console.log(`Proxying: ${req.method} ${req.url} -> ${BASE_PATH}/api${req.url.replace('/api', '')}`);
      }
    })
  );

  // Proxy Streamlit if needed
  app.use(
    '/streamlit',
    createProxyMiddleware({
      target: 'http://localhost:8501',
      changeOrigin: true,
      ws: true,
      pathRewrite: BASE_PATH ? {
        '^/streamlit': `${BASE_PATH}/streamlit`
      } : undefined
    })
  );
};