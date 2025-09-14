import axios from 'axios';

const API_BASE_URL = 'http://localhost:5001/api';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types
export interface Article {
  id: number;
  title: string;
  content: string;
  summary: string;
  author: string;
  date: string;
  category: string;
  newspaper: string;
  url: string;
  images_found: number;
  images_downloaded: number;
  images_data: any[];
  scraped_at: string;
  article_id: string;
}

export interface Image {
  id: number;
  article_id: string;
  url: string;
  local_path: string;
  alt_text: string;
  title: string;
  width: number;
  height: number;
  format: string;
  size_bytes: number;
  relevance_score: number;
  downloaded_at: string;
}

export interface ScrapingStatus {
  is_running: boolean;
  progress: number;
  total: number;
  current_url: string;
  articles_found: number;
  images_found: number;
  error: string | null;
  start_time: string | null;
  end_time: string | null;
  analysis?: any;
  suggested_method?: string;
  confidence?: number;
}

export interface ScrapingConfig {
  url: string;
  max_articles: number;
  max_images: number;
  method: 'auto' | 'hybrid' | 'optimized' | 'selenium' | 'requests';
  download_images: boolean;
  category: string;
  newspaper: string;
  region: string;
}

export interface Statistics {
  general: {
    total_articles: number;
    total_newspapers: number;
    total_categories: number;
    total_images_found: number;
    total_images_downloaded: number;
  };
  newspapers: Array<{
    newspaper: string;
    articles_count: number;
    images_count: number;
  }>;
  categories: Array<{
    category: string;
    articles_count: number;
  }>;
  sessions: Array<{
    session_id: string;
    url_scraped: string;
    articles_found: number;
    images_found: number;
    duration_seconds: number;
    method_used: string;
    created_at: string;
  }>;
}

export interface Newspaper {
  newspaper: string;
  articles_count: number;
  total_images_found: number;
  total_images_downloaded: number;
  first_scraped: string;
  last_scraped: string;
}

export interface NewspapersResponse {
  newspapers: Newspaper[];
  total: number;
}

export interface DeleteNewspaperResponse {
  message: string;
  deleted: {
    articles: number;
    images: number;
    files: number;
  };
}

// API functions
export const apiService = {
  // Health check
  healthCheck: async () => {
    const response = await api.get('/health');
    return response.data;
  },

  // Get configuration
  getConfig: async () => {
    const response = await api.get('/config');
    return response.data;
  },

  // Get scraping status
  getStatus: async (): Promise<ScrapingStatus> => {
    const response = await api.get('/status');
    return response.data as ScrapingStatus;
  },

  // Start scraping
  startScraping: async (config: ScrapingConfig) => {
    const response = await api.post('/start-scraping', config);
    return response.data;
  },

  // Stop scraping
  stopScraping: async () => {
    const response = await api.post('/stop-scraping');
    return response.data;
  },

  // Get articles
  getArticles: async (params: {
    page?: number;
    limit?: number;
    newspaper?: string;
    category?: string;
    region?: string;
  } = {}) => {
    const response = await api.get('/articles', { params });
    return response.data;
  },

  // Get article filters
  getArticleFilters: async () => {
    const response = await api.get('/articles/filters');
    return response.data;
  },

  // Get single article
  getArticle: async (articleId: string): Promise<Article> => {
    const response = await api.get(`/articles/${articleId}`);
    return response.data as Article;
  },

  // Get images
  getImages: async (params: {
    page?: number;
    limit?: number;
    article_id?: string;
  } = {}) => {
    const response = await api.get('/images', { params });
    return response.data;
  },

  // Get statistics
  getStatistics: async (): Promise<Statistics> => {
    const response = await api.get('/stats');
    return response.data as Statistics;
  },

  // Get image URL
  getImageUrl: (filename: string) => {
    return `${API_BASE_URL}/images/${filename}`;
  },

  // Clear all data
  clearAllData: async () => {
    const response = await api.delete('/clear-all');
    return response.data;
  },

  // Get newspapers list
  getNewspapers: async (): Promise<NewspapersResponse> => {
    const response = await api.get('/newspapers');
    return response.data as NewspapersResponse;
  },

  // Delete newspaper data
  deleteNewspaper: async (newspaperName: string): Promise<DeleteNewspaperResponse> => {
    const response = await api.delete(`/newspapers/${encodeURIComponent(newspaperName)}`);
    return response.data as DeleteNewspaperResponse;
  },
};

export default apiService;
