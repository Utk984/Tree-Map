# 🚀 Deployment Guide

This guide explains how to deploy the Tree Map application to GitHub Pages.

## 📋 Prerequisites

- GitHub account
- Node.js installed locally
- Python environment for the API

## 🌐 Deployment Options

### Option 1: Frontend on GitHub Pages + Backend on Cloud Service (Recommended)

#### Frontend (GitHub Pages)
1. **Push your code to GitHub:**
   ```bash
   git add .
   git commit -m "Add GitHub Pages deployment configuration"
   git push origin main
   ```

2. **Enable GitHub Pages:**
   - Go to your repository on GitHub
   - Navigate to Settings → Pages
   - Select "GitHub Actions" as the source
   - The workflow will automatically deploy your React app

3. **Update Configuration:**
   - Edit `src/config.ts`
   - Update `productionApiUrl` with your deployed API URL
   - Update `githubPagesBaseUrl` with your actual GitHub Pages URL

#### Backend (Cloud Service)
Deploy your Python API to one of these services:

**Railway (Recommended - Easy & Free):**
1. Go to [railway.app](https://railway.app)
2. Connect your GitHub account
3. Create new project from GitHub repository
4. Add environment variables if needed
5. Deploy!

**Render:**
1. Go to [render.com](https://render.com)
2. Create new Web Service
3. Connect your GitHub repository
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `python api_server.py`

**Heroku:**
1. Install Heroku CLI
2. Create `Procfile`: `web: python api_server.py`
3. Deploy: `git push heroku main`

### Option 2: Static Data Approach (No Backend Needed)

If you want to avoid backend deployment, you can pre-generate all tree views:

1. **Generate Static Images:**
   ```bash
   # Run this script to generate all tree view images
   python generate_static_views.py
   ```

2. **Update Frontend:**
   - Modify the app to load static images instead of calling the API
   - Host everything on GitHub Pages

## 🔧 Configuration

### Environment Variables

Create these files for different environments:

**Development (.env.local):**
```
VITE_API_BASE_URL=http://localhost:5001
```

**Production:**
Update `src/config.ts` with your production API URL.

### GitHub Pages Configuration

The app is configured to work with GitHub Pages subdirectory structure:
- Base URL: `/Tree-Map/` (update in `vite.config.ts` if your repo name is different)
- Automatic deployment via GitHub Actions

## 🚀 Quick Start

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Initial deployment setup"
   git push origin main
   ```

2. **Deploy Backend:**
   - Choose a cloud service (Railway recommended)
   - Deploy your Python API
   - Update `src/config.ts` with the API URL

3. **Enable GitHub Pages:**
   - Go to repository Settings → Pages
   - Select "GitHub Actions" source
   - Your app will be available at `https://yourusername.github.io/Tree-Map`

## 🔍 Troubleshooting

### Common Issues:

1. **CORS Errors:**
   - Make sure your API server has CORS enabled
   - Check that the API URL in `config.ts` is correct

2. **404 Errors:**
   - Verify the GitHub Pages base URL in `vite.config.ts`
   - Check that the repository name matches the base URL

3. **API Connection Issues:**
   - Ensure your backend is deployed and running
   - Check the API URL configuration
   - Verify CORS settings on your API server

### Testing Locally:

```bash
# Test production build locally
npm run build
npm run preview
```

## 📊 Performance Considerations

- The app loads 115k+ tree points and 99k+ street view points
- Consider implementing pagination or clustering for better performance
- The API generates tree views on-demand, which may be slow for large datasets

## 🔐 Security Notes

- GitHub Pages only serves static files
- Your API will be publicly accessible
- Consider adding authentication if needed
- Use HTTPS for all API calls in production
