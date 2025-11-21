// Configuration for the Web Scraper Frontend

export const config = {
  // API Configuration
  api: {
    baseUrl: process.env.REACT_APP_API_URL || 'http://localhost:5001/api',
    timeout: 30000,
  },
  
  // Pagination
  pagination: {
    articlesPerPage: 12,
    imagesPerPage: 20,
  },
  
  // Scraping Configuration
  scraping: {
    defaultMaxArticles: 50,
    defaultMaxImages: 50,
    maxArticlesLimit: 2000,
    maxImagesLimit: 500,
  },
  
  // UI Configuration
  ui: {
    theme: {
      primary: '#1976d2',
      secondary: '#dc004e',
    },
    breakpoints: {
      xs: 0,
      sm: 600,
      md: 900,
      lg: 1200,
      xl: 1536,
    },
  },
  
  // Image Configuration
  images: {
    maxDisplaySize: '60vh',
    supportedFormats: ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'],
  },
};

export default config;


