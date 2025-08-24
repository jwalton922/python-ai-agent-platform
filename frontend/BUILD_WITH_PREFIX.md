# Building React App with Path Prefix

The React app is configured to be served from a subdirectory path (`/app`) rather than the root path.

## Quick Build Commands

### Default Build (serves at /app)
```bash
cd frontend
npm run build
```

### Custom Path Build
```bash
cd frontend
# Using npm script
PUBLIC_URL=/custom-path npm run build

# Or using the build script
./build.sh /custom-path
```

## Configuration Details

### 1. package.json Configuration

The app has two key configurations in `package.json`:

- **`homepage: "/app"`** - Sets the default base path for all assets
- **`build:subfolder` script** - Alternative build command with PUBLIC_URL

### 2. Environment Variable Method

You can override the path at build time using the `PUBLIC_URL` environment variable:

```bash
# Linux/Mac
PUBLIC_URL=/my-app npm run build

# Windows Command Prompt
set PUBLIC_URL=/my-app && npm run build

# Windows PowerShell
$env:PUBLIC_URL="/my-app"; npm run build
```

### 3. Using the Build Script

The `build.sh` script simplifies the process:

```bash
# Default path (/app)
./build.sh

# Custom path
./build.sh /dashboard
./build.sh /admin/panel
```

## Important Notes

### Asset Loading
All assets (JS, CSS, images) will be loaded from the specified path:
- With `/app` prefix: `/app/static/js/main.js`
- Without prefix: `/static/js/main.js`

### API Calls
The app is configured with a proxy in development mode. In production:
- API calls should use relative paths: `/api/agents`
- The backend server handles routing appropriately

### Server Configuration
The FastAPI backend is already configured to serve the React app at `/app`:

```python
# backend/main.py
app.mount("/app", StaticFiles(directory=frontend_build, html=True), name="frontend")
```

## Troubleshooting

### Assets Not Loading (404 errors)
- Verify the PUBLIC_URL matches where the app is served
- Check browser Network tab for actual paths being requested
- Ensure the backend mount path matches the build prefix

### Blank Page
- Check browser console for errors
- Verify the `homepage` field in package.json
- Try building without a prefix to test: `PUBLIC_URL=/ npm run build`

### Development Mode
In development (`npm start`), the app always runs at root (`/`). The prefix only applies to production builds.

## Examples

### Deploy at Root
```bash
# Remove homepage from package.json or set to "/"
PUBLIC_URL=/ npm run build
```

### Deploy at /dashboard
```bash
PUBLIC_URL=/dashboard npm run build
# Update backend to mount at /dashboard
```

### Deploy at /v2/app
```bash
PUBLIC_URL=/v2/app npm run build
# Update backend to mount at /v2/app
```

## Testing the Build Locally

After building:
```bash
# Start the backend server
cd ..
python3 run_unified.py

# Access the app at:
# http://localhost:8000/app
```

The app should load correctly with all assets and API calls working.