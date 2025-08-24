# Dynamic Base Path Configuration

The React app now supports dynamic base path configuration, allowing it to work in various proxy environments without rebuilding.

## How It Works

The app determines its API base path using a priority system:

1. **Runtime Configuration** (highest priority)
   - Injected via `window.API_CONFIG` in the HTML
   - Set by the server when serving the app

2. **Environment Variables** (build time)
   - `REACT_APP_BASE_PATH` for explicit configuration
   - `PUBLIC_URL` for asset paths

3. **URL Auto-Detection**
   - Detects Jupyter notebook proxy patterns
   - Recognizes common proxy patterns

4. **Default** (no prefix)
   - Standard deployment at root

## Usage Methods

### Method 1: Runtime Configuration (Recommended for Proxies)

The server injects configuration when serving the app:

```javascript
// Automatically injected by run_sandbox.py
window.API_CONFIG = {
  baseUrl: '/notebook/pxj363/josh-testing/proxy/8000',
  basePath: '/notebook/pxj363/josh-testing/proxy/8000'
};
```

### Method 2: Build-Time Configuration

```bash
# Build with specific base path
REACT_APP_BASE_PATH=/my/base/path npm run build

# Or use PUBLIC_URL (also sets asset paths)
PUBLIC_URL=/my/base/path/app npm run build
```

### Method 3: Auto-Detection

The app automatically detects these URL patterns:
- `/notebook/*/proxy/[PORT]` - Jupyter notebooks
- `/proxy/[PORT]` - Simple proxy
- `/app` - Standard app deployment

### Method 4: Manual Configuration (Development)

```javascript
// In browser console or component
import { setApiConfig } from './utils/apiConfig';
import { reinitializeApi } from './services/api';

// Set custom base path
setApiConfig({
  baseUrl: '/custom/path',
  basePath: '/custom/path'
});

// Reinitialize API client
reinitializeApi();
```

## Testing Configuration

### In Development

```bash
# Start with custom base path
REACT_APP_BASE_PATH=/notebook/test/proxy/8000 npm start
```

### In Browser Console

```javascript
// Test utility is available in development
testApiConfig.current();  // Show current config
testApiConfig.testJupyter();  // Test Jupyter proxy
testApiConfig.testProxy(8080);  // Test proxy on port 8080
testApiConfig.testCustom('/my/path');  // Test custom path
testApiConfig.reset();  // Reset to auto-detection
testApiConfig.testCall();  // Make test API call
```

## Deployment Scenarios

### Jupyter Notebook Proxy

```bash
# Server knows the proxy path
./run_sandbox.sh

# App automatically uses: /notebook/pxj363/josh-testing/proxy/8000/api
```

### Reverse Proxy with Path

```nginx
location /myapp/ {
    proxy_pass http://localhost:8000/;
    proxy_set_header X-Forwarded-Path /myapp;
}
```

```bash
# Build and run
PUBLIC_URL=/myapp/app npm run build
BASE_PATH=/myapp python run_sandbox.py
```

### Docker/Kubernetes with Ingress

```yaml
# Ingress configuration
spec:
  rules:
  - http:
      paths:
      - path: /platform
        backend:
          service:
            name: ai-platform
            port: 8000
```

```dockerfile
# Dockerfile
ENV PUBLIC_URL=/platform/app
ENV BASE_PATH=/platform
RUN npm run build
```

## Troubleshooting

### Check Current Configuration

1. Open browser DevTools Console
2. Check the config:
   ```javascript
   window.API_CONFIG  // Runtime config (if set)
   apiConfig.getConfig()  // Active config
   ```

### API Calls Not Working

1. Verify base path:
   ```javascript
   console.log(apiConfig.getApiBaseUrl());
   // Should output: /your/base/path/api
   ```

2. Test API endpoint:
   ```javascript
   testApiConfig.testCall();
   ```

3. Check network tab for actual request URLs

### Wrong Base Path Detected

Override with manual configuration:
```javascript
setApiConfig({ baseUrl: '/correct/path' });
reinitializeApi();
```

## API Structure

### Core Module: `utils/apiConfig.ts`

- `apiConfig.getConfig()` - Get current configuration
- `apiConfig.getApiBaseUrl()` - Get API base URL
- `apiConfig.buildUrl(endpoint)` - Build full URL
- `apiConfig.setConfig(config)` - Override configuration
- `apiConfig.reset()` - Reset to auto-detection

### Integration: `services/api.ts`

- Uses `getApiBaseUrl()` for axios base URL
- `reinitializeApi()` - Recreate axios instance with new config

## Best Practices

1. **For Production Proxies**: Use runtime injection via server
2. **For Static Builds**: Use environment variables at build time
3. **For Development**: Use `REACT_APP_BASE_PATH` or test utilities
4. **Always Test**: Verify configuration after deployment using browser console

## Examples

### Jupyter Notebook Deployment

```bash
# Build once
cd frontend
npm run build

# Run with dynamic configuration
cd ..
./run_sandbox.sh
# App works at any proxy path without rebuilding
```

### Multi-Environment Build

```bash
# Development
REACT_APP_BASE_PATH="" npm run build:dev

# Staging  
REACT_APP_BASE_PATH="/staging" npm run build:staging

# Production
REACT_APP_BASE_PATH="/prod" npm run build:prod
```

### Runtime Reconfiguration

```html
<!-- Inject at serve time -->
<script>
  window.API_CONFIG = {
    baseUrl: getEnvironmentBasePath(),  // Dynamic function
    basePath: getEnvironmentBasePath()
  };
</script>
```

The dynamic base path system ensures the React app can adapt to any deployment environment without requiring rebuilds.