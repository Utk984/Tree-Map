// Configuration for different environments
export const config = {
  // API base URL - will be different for development vs production
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001',
  
  // GitHub Pages base URL (update this to your actual repository name)
  githubPagesBaseUrl: 'https://yourusername.github.io/Tree-Map',
  
  // Production API URL (you'll need to deploy this separately)
  productionApiUrl: 'https://your-api-domain.com'
};

// Determine if we're in production
export const isProduction = import.meta.env.PROD;

// Get the appropriate API URL
export const getApiUrl = () => {
  if (isProduction) {
    // In production, use the deployed API URL
    return config.productionApiUrl;
  } else {
    // In development, use local API
    return config.apiBaseUrl;
  }
};
