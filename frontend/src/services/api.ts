import axios from 'axios';

const API_BASE_URL = 'http://localhost:5001/api';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 segundos por defecto
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Types
export interface Article {
  id: number;
  title: string;
  content: string;
  summary: string;
  author: string;
  date: string;
  category: string;
  user_category?: string;
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
    search?: string;
    dateFrom?: string;
    dateTo?: string;
  } = {}, config: Record<string, any> = {}) => {
    const response = await api.get('/articles', { params, ...config });
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

  // Trigger auto update
  triggerAutoUpdate: async () => {
    const response = await api.post('/auto-update');
    return response.data;
  },

  // =============================================================================
  // COMPETITIVE INTELLIGENCE API METHODS
  // =============================================================================

  // Get competitors
  getCompetitors: async () => {
    const response = await api.get('/competitive-intelligence/competitors');
    return response.data;
  },

  // Add competitor
  addCompetitor: async (competitor: {
    name: string;
    keywords: string[];
    domains?: string[];
  }) => {
    const response = await api.post('/competitive-intelligence/competitors', competitor);
    return response.data;
  },

  // Delete competitor
  deleteCompetitor: async (competitorId: number) => {
    const response = await api.delete(`/competitive-intelligence/competitors/${competitorId}`);
    return response.data;
  },

  // Get competitive analytics
  getCompetitiveAnalytics: async (days: number = 30) => {
    const response = await api.get('/competitive-intelligence/analytics', {
      params: { days }
    });
    return response.data;
  },

  // Get competitive alerts
  getCompetitiveAlerts: async (unreadOnly: boolean = true) => {
    const response = await api.get('/competitive-intelligence/alerts', {
      params: { unread_only: unreadOnly }
    });
    return response.data;
  },

  // Mark alert as read
  markAlertRead: async (alertId: number) => {
    const response = await api.post(`/competitive-intelligence/alerts/${alertId}/read`);
    return response.data;
  },

  // Get competitive limits
  getCompetitiveLimits: async () => {
    const response = await api.get('/competitive-intelligence/limits');
    return response.data;
  },

    getAvailableNewspapers: async () => {
      const response = await api.get('/competitive-intelligence/newspapers');
      return response.data;
    },
    
  getAISuggestions: async (competitorName: string, existingKeywords: string[] = []) => {
    const response = await api.post('/competitive-intelligence/ai-suggestions', {
      competitor_name: competitorName,
      existing_keywords: existingKeywords
    });
    return response.data;
  },

  analyzeExistingArticles: async () => {
    const response = await api.post('/competitive-intelligence/analyze-articles');
    return response.data;
  },
  
  autoDetectCompetitor: async (competitorName: string) => {
    const response = await api.post('/competitive-intelligence/auto-detect', {
      competitor_name: competitorName
    });
    return response.data;
  },

  // ===== TRENDING TOPICS PREDICTOR =====
  
  generateTrendingPredictions: async (limit: number = 10) => {
    const response = await api.post('/trending-predictor/generate', { limit }, { timeout: 120000 }); // 2 minutos para análisis complejo
    return response.data;
  },

  getUserPredictions: async (limit: number = 20) => {
    const response = await api.get(`/trending-predictor/predictions?limit=${limit}`);
    return response.data;
  },

  getDailyUsage: async () => {
    const response = await api.get('/trending-predictor/usage');
    return response.data;
  },

  // Get auto update status
  getAutoUpdateStatus: async () => {
    const response = await api.get('/auto-update/status');
    return response.data;
  },

  // ===== CHATBOT =====
  chat: async (payload: {
    message: string;
    date_from?: string;
    date_to?: string;
    limit?: number;
  }): Promise<{
    reply: string;
    data?: any;
    citations?: Array<{ title: string; url: string }>;
    plan?: string;
    limits?: any;
    error?: string;
  }> => {
    const response = await api.post('/chat', payload, { timeout: 60000 }); // 60 segundos para búsquedas complejas
    return response.data as {
      reply: string;
      data?: any;
      citations?: Array<{ title: string; url: string }>;
      plan?: string;
      limits?: any;
      error?: string;
    };
  },

  // ===== BÚSQUEDA AVANZADA =====
  
  // Get search suggestions
  getSearchSuggestions: async () => {
    const response = await api.get('/search/suggestions');
    return response.data;
  },

  // Advanced search
  advancedSearch: async (searchParams: any) => {
    const response = await api.post('/search/advanced', searchParams);
    return response.data;
  },

  // ===== REDES SOCIALES (PROYECTO ACADÉMICO) =====
  
    scrapeSocialMedia: async (query: string, maxPosts: number = 50, filterLanguage?: string, mode: 'query' | 'url' = 'query', platform: 'twitter' | 'facebook' | 'reddit' | 'youtube' = 'twitter') => {
    // Usar timeout optimizado para scraping de redes sociales
    // Facebook optimizado: 10 minutos (600 segundos) - proceso más rápido ahora
    const timeout = platform === 'facebook' ? 600000 : 600000;  // 10 min para todos (proceso optimizado)
    const response = await api.post('/social-media/scrape', {
      query,
      max_posts: maxPosts,
      filter_language: filterLanguage,
      mode: mode,
      platform: platform
        }, {
          timeout: timeout
        });
    return response.data;
  },

  getSocialMediaPosts: async (options: {
    platform?: string;
    category?: string;
    sentiment?: string;
    language?: string;
    limit?: number;
    offset?: number;
    startDate?: string;
    endDate?: string;
    minInteractions?: number;
    topMetric?: 'likes' | 'retweets' | 'replies' | 'engagement';
    topLimit?: number;
  } = {}) => {
    const {
      platform,
      category,
      sentiment,
      language,
      limit = 100,
      offset = 0,
      startDate,
      endDate,
      minInteractions,
      topMetric,
      topLimit,
    } = options;

    const params: any = { limit, offset };
    if (platform) params.platform = platform;
    if (category) params.category = category;
    if (sentiment) params.sentiment = sentiment;
    if (language) params.language = language;
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    if (typeof minInteractions === 'number' && !Number.isNaN(minInteractions)) {
      params.min_interactions = minInteractions;
    }
    if (topMetric) params.top_metric = topMetric;
    if (typeof topLimit === 'number' && !Number.isNaN(topLimit)) {
      params.top_limit = topLimit;
    }

    const response = await api.get('/social-media/posts', { params });
    return response.data;
  },

  getSocialMediaStats: async () => {
    const response = await api.get('/social-media/stats');
    return response.data;
  },

  // ===== COMENTARIOS/OPINIONES =====
  
  getComments: async (articleId: number) => {
    const response = await api.get('/comments', {
      params: { article_id: articleId }
    });
    return response.data;
  },

  createComment: async (comment: {
    article_id: number;
    user_name: string;
    comment_text: string;
  }) => {
    const response = await api.post('/comments', comment);
    return response.data;
  },

  deleteComment: async (commentId: number) => {
    const response = await api.delete(`/comments/${commentId}`);
    return response.data;
  },

  // ===== COMENTARIOS VIRALES =====
  
  getViralComments: async (topic?: string, limit?: number) => {
    const response = await api.get('/viral-comments', {
      params: { topic, limit }
    });
    return response.data;
  },

  createViralComment: async (comment: {
    user_name: string;
    comment_text: string;
    topic: string;
  }) => {
    const response = await api.post('/viral-comments', comment);
    return response.data;
  },

  likeViralComment: async (commentId: number) => {
    const response = await api.post(`/viral-comments/${commentId}/like`);
    return response.data;
  },

  getViralCommentsSentimentAnalysis: async (topic?: string, days: number = 30) => {
    const response = await api.get('/viral-comments/sentiment-analysis', {
      params: { topic, days }
    });
    return response.data;
  },

  getViralCommentsAlerts: async (days: number = 7) => {
    const response = await api.get('/viral-comments/alerts', {
      params: { days }
    });
    return response.data;
  },
};

export { api };
export default apiService;
