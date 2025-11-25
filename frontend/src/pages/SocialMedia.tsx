import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Grid,
  Alert,
  CircularProgress,
  Chip,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Paper,
  Divider,
  IconButton,
  Link,
  Pagination,
  Tooltip,
  Stack,
} from '@mui/material';
import {
  Search as SearchIcon,
  Twitter as TwitterIcon,
  TrendingUp as TrendingUpIcon,
  SentimentSatisfied as PositiveIcon,
  SentimentNeutral as NeutralIcon,
  SentimentDissatisfied as NegativeIcon,
  Category as CategoryIcon,
  Refresh as RefreshIcon,
  BarChart as BarChartIcon,
  ChatBubbleOutline as ChatBubbleOutlineIcon,
  Repeat as RepeatIcon,
  Favorite as FavoriteIcon,
  ArrowUpward as ArrowUpwardIcon,
  Download as DownloadIcon,
} from '@mui/icons-material';
import { Bar, Pie } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
} from 'chart.js';
import apiService from '../services/api';
import * as XLSX from 'xlsx';

// Tipos para las respuestas de la API
interface SocialMediaResponse {
  success: boolean;
  total_scraped?: number;
  total_saved?: number;
  total?: number;
  posts?: SocialMediaPost[];
  error?: string;
  demo_mode?: boolean;
  message?: string;
  suggestion?: string;
  tweets_with_images?: number;
}

interface SocialMediaStatsResponse {
  success: boolean;
  stats?: {
    total_posts?: number;
    by_platform?: { [key: string]: number };
    by_category?: { [key: string]: number };
    by_sentiment?: { [key: string]: number };
  };
}

// Registrar componentes de Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  ChartTooltip,
  Legend
);

interface SocialMediaPost {
  id: number;
  platform: string;
  username: string;
  text: string;
  content?: string;
  cleaned_text?: string;
  likes: number;
  retweets: number;
  replies: number;
  hashtags: string[];
  category: string;
  sentiment: string;
  detected_language: string;
  url: string;
  image_url?: string;
  video_url?: string;
  created_at: string;
  scraped_at: string;
  subreddit?: string;  // Para Reddit
  title?: string;  // Para Reddit (título del post)
  score?: number;
  upvotes?: number;
  downvotes?: number;
  comments?: number;
}

const POSTS_PER_PAGE = 9;

const SocialMedia: React.FC = () => {
  const [query, setQuery] = useState('');
  const [url, setUrl] = useState('');
  const [scrapeMode, setScrapeMode] = useState<'query' | 'url'>('query');
  const [platform, setPlatform] = useState<'twitter' | 'facebook' | 'reddit' | 'youtube'>('twitter');
  const [maxPosts, setMaxPosts] = useState(100);
  const [filterLanguage, setFilterLanguage] = useState('');
  const [scraping, setScraping] = useState(false);
  const [posts, setPosts] = useState<SocialMediaPost[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [filterCategory, setFilterCategory] = useState('');
  const [filterSentiment, setFilterSentiment] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [minInteractions, setMinInteractions] = useState<string>('');
  const [topMetric, setTopMetric] = useState<'none' | 'likes' | 'retweets' | 'replies' | 'engagement'>('none');
  const [topLimit, setTopLimit] = useState<string>('');

  const platformFilters: Array<{
    value: 'twitter' | 'facebook' | 'reddit' | 'youtube';
    label: string;
    color: string;
    description: string;
  }> = [
    { value: 'twitter', label: 'Twitter/X', color: '#1d9bf0', description: 'Menciones y hashtags de X (Twitter)' },
    { value: 'facebook', label: 'Facebook', color: '#1877f2', description: 'Posts públicos extraídos de Facebook' },
    { value: 'reddit', label: 'Reddit', color: '#ff4500', description: 'Posts y comentarios de subreddits' },
    { value: 'youtube', label: 'YouTube', color: '#ff0000', description: 'Videos y metadatos de canales' },
  ];

  const languageOptions = [
    { value: '', label: 'Todos' },
    { value: 'es', label: 'Español' },
    { value: 'en', label: 'Inglés' },
    { value: 'pt', label: 'Portugués' },
    { value: 'fr', label: 'Francés' },
    { value: 'de', label: 'Alemán' },
    { value: 'it', label: 'Italiano' },
  ];

  const handleExportExcel = () => {
    if (!posts.length) {
      setError('No hay posts disponibles para exportar.');
      return;
    }

    setError(null);

    const formatted = posts.map((post, index) => ({
      '#': index + 1,
      Plataforma: post.platform,
      Usuario: post.username,
      Título: post.title || '',
      Contenido: post.content || post.text || '',
      Hashtags: Array.isArray(post.hashtags) ? post.hashtags.join(', ') : '',
      Categoría: post.category || '',
      Sentimiento: post.sentiment || '',
      Subreddit: post.subreddit || '',
      URL: post.url || '',
      'Imagen URL': post.image_url || '',
      'Video URL': post.video_url || '',
      Likes: post.likes ?? post.upvotes ?? 0,
      Compartidos: post.retweets ?? 0,
      Comentarios: post.replies ?? post.comments ?? 0,
      Score: post.score ?? 0,
      'Fecha Publicación': post.created_at ? new Date(post.created_at).toLocaleString('es-PE') : '',
      'Fecha Scraping': post.scraped_at ? new Date(post.scraped_at).toLocaleString('es-PE') : '',
    }));

    const worksheet = XLSX.utils.json_to_sheet(formatted);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Posts');

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `posts_${platform}_${timestamp}.xlsx`;
    XLSX.writeFile(workbook, filename);
    setSuccess(`📁 Archivo exportado: ${filename}`);
  };

  const handleExportAllExcel = async () => {
    try {
      setError(null);
      setSuccess(null);

      const aggregatedPosts: SocialMediaPost[] = [];

      const minInteractionsValue = minInteractions ? Number(minInteractions) : undefined;
      const effectiveTopMetric = topMetric === 'none' ? undefined : topMetric;
      const effectiveTopLimit = effectiveTopMetric && topLimit ? Number(topLimit) : undefined;

      for (const item of platformFilters) {
        const response = await apiService.getSocialMediaPosts({
          platform: item.value,
          category: filterCategory || undefined,
          sentiment: filterSentiment || undefined,
          language: filterLanguage || undefined,
          startDate: startDate || undefined,
          endDate: endDate || undefined,
          minInteractions: typeof minInteractionsValue === 'number' && !Number.isNaN(minInteractionsValue)
            ? minInteractionsValue
            : undefined,
          topMetric: effectiveTopMetric,
          topLimit: effectiveTopLimit,
          limit: effectiveTopLimit || 1000,
        }) as SocialMediaResponse;

        if (response.success && response.posts && response.posts.length) {
          aggregatedPosts.push(
            ...response.posts.map((post: any) => ({
              ...post,
              platform: item.value,
            }))
          );
        }
      }

      if (!aggregatedPosts.length) {
        setError('No se encontraron posts para exportar.');
        return;
      }

      const formatted = aggregatedPosts.map((post, index) => ({
        '#': index + 1,
        Plataforma: post.platform,
        Usuario: post.username,
        Título: post.title || '',
        Contenido: post.content || post.text || '',
        Hashtags: Array.isArray(post.hashtags) ? post.hashtags.join(', ') : '',
        Categoría: post.category || '',
        Sentimiento: post.sentiment || '',
        Subreddit: post.subreddit || '',
        URL: post.url || '',
        'Imagen URL': post.image_url || '',
        'Video URL': post.video_url || '',
        Likes: post.likes ?? post.upvotes ?? 0,
        Compartidos: post.retweets ?? 0,
        Comentarios: post.replies ?? post.comments ?? 0,
        Score: post.score ?? 0,
        'Fecha Publicación': post.created_at ? new Date(post.created_at).toLocaleString('es-PE') : '',
        'Fecha Scraping': post.scraped_at ? new Date(post.scraped_at).toLocaleString('es-PE') : '',
      }));

      const worksheet = XLSX.utils.json_to_sheet(formatted);
      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet, 'Posts');

      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const filename = `posts_todas_las_plataformas_${timestamp}.xlsx`;
      XLSX.writeFile(workbook, filename);
      setSuccess(`📁 Archivo exportado: ${filename}`);
    } catch (err: any) {
      console.error('Error exportando todas las redes:', err);
      setError('Ocurrió un error al exportar todas las redes. Inténtalo nuevamente.');
    }
  };

  // Cargar posts y estadísticas al montar
  useEffect(() => {
    loadPosts();
    loadStats();
  }, [filterCategory, filterSentiment, platform, filterLanguage, startDate, endDate, minInteractions, topMetric, topLimit]);

  useEffect(() => {
    setCurrentPage(1);
  }, [posts]);

  const loadPosts = async () => {
    try {
      console.log('🔄 Cargando posts...');
      const minInteractionsValue = minInteractions ? Number(minInteractions) : undefined;
      const effectiveTopMetric = topMetric === 'none' ? undefined : topMetric;
      const effectiveTopLimit = effectiveTopMetric && topLimit ? Number(topLimit) : undefined;
      const response = await apiService.getSocialMediaPosts({
        platform,
        category: filterCategory || undefined,
        sentiment: filterSentiment || undefined,
        language: filterLanguage || undefined,
        startDate: startDate || undefined,
        endDate: endDate || undefined,
        minInteractions: typeof minInteractionsValue === 'number' && !Number.isNaN(minInteractionsValue)
          ? minInteractionsValue
          : undefined,
        topMetric: effectiveTopMetric,
        topLimit: effectiveTopLimit,
        limit: effectiveTopLimit || 100,
      }) as SocialMediaResponse;
      
      console.log('📥 Respuesta recibida:', {
        success: response.success,
        total: response.total,
        postsCount: response.posts?.length || 0
      });
      
      if (response.success && response.posts) {
        // Parsear hashtags si vienen como string y asegurar image_url
        const parsedPosts = response.posts.map((post: any) => {
          let hashtags = post.hashtags || [];
          if (typeof post.hashtags === 'string') {
            try {
              hashtags = JSON.parse(post.hashtags || '[]');
            } catch (e) {
              hashtags = [];
            }
          }
          
          // Asegurar que image_url y video_url estén presentes
          const imageUrl = post.image_url || null;
          const videoUrl = post.video_url || null;
          
          // Log para debug
          if (imageUrl) {
            console.log(`✅ Post ${post.id} tiene imagen: ${imageUrl.substring(0, 50)}...`);
          }
          if (videoUrl) {
            console.log(`✅ Post ${post.id} tiene video: ${videoUrl.substring(0, 50)}...`);
          }
          
          // Para Reddit: Si username es "unknown", usar subreddit o "Reddit"
          let username = post.username || '';
          if (post.platform === 'reddit' && (username === 'unknown' || username === 'Unknown' || !username)) {
            const subreddit = post.subreddit || (post as any).subreddit;
            if (subreddit && subreddit !== 'all') {
              username = subreddit.startsWith('r/') ? subreddit : `r/${subreddit}`;
            } else {
              username = 'Reddit';
            }
          }
          
          return {
            ...post,
            hashtags: Array.isArray(hashtags) ? hashtags : [],
            image_url: imageUrl,  // Asegurar que image_url esté presente
            video_url: videoUrl,   // Asegurar que video_url esté presente
            username: username,  // Username procesado (con fallback para Reddit)
            subreddit: post.subreddit || (post as any).subreddit,  // Preservar subreddit
            title: post.title || (post as any).title  // Preservar título para Reddit
          };
        });
        
        console.log(`✅ Posts parseados: ${parsedPosts.length}`);
        setPosts(parsedPosts);
        
        // Log para verificar
        const postsWithImages = parsedPosts.filter(p => p.image_url);
        console.log(`📊 Total posts: ${parsedPosts.length}, Con imágenes: ${postsWithImages.length}`);
      } else {
        console.warn('⚠️ No hay posts en la respuesta o success=false');
        console.log('Respuesta completa:', response);
        setPosts([]);
      }
    } catch (err: any) {
      console.error('❌ Error cargando posts:', err);
      setError(err.response?.data?.error || 'Error cargando posts');
      setPosts([]);
    }
  };

  const loadStats = async () => {
    try {
      const response = await apiService.getSocialMediaStats() as SocialMediaStatsResponse;
      if (response.success) {
        setStats(response.stats || null);
      }
    } catch (err: any) {
      console.error('Error cargando estadísticas:', err);
    }
  };

  const handleScrape = async () => {
    if (scrapeMode === 'query' && !query.trim()) {
      setError('Por favor ingresa un hashtag o palabra clave');
      return;
    }
    
    if (scrapeMode === 'url' && !url.trim()) {
      const platformName = platform === 'facebook' ? 'Facebook' : platform === 'reddit' ? 'Reddit' : platform === 'youtube' ? 'YouTube' : 'Twitter/X';
      setError(`Por favor ingresa una URL de ${platformName}`);
      return;
    }
    
    // Si el modo es URL pero el campo query tiene contenido, usar query
    const actualQuery = scrapeMode === 'url' ? url : query;
    if (!actualQuery.trim()) {
      setError('Por favor ingresa una URL o palabra clave');
      return;
    }

    setScraping(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await apiService.scrapeSocialMedia(
        scrapeMode === 'url' ? url : query,
        maxPosts,
        filterLanguage || undefined,
        scrapeMode === 'url' ? 'url' : 'query',
        platform
      ) as SocialMediaResponse;

              if (response.success) {
                // Usar el mensaje del backend directamente si existe, sino construir uno
                let message = response.message || '';
                
                if (!message) {
                  // Si no hay mensaje del backend, construir uno
                  const totalSaved = response.total_saved || 0;
                  const totalScraped = response.total_scraped || 0;
                  const tweetsWithImages = response.tweets_with_images || 0;
                  
                  if (response.demo_mode) {
                    message = `⚠️ ⚠️ ⚠️ MODO DEMO ACTIVADO\n\n` +
                            `❌ NO se pudieron extraer tweets REALES del enlace\n` +
                            `🔒 Twitter/X requiere autenticación para acceder al contenido\n\n` +
                            `📊 ${totalSaved} posts DEMO generados para fines académicos\n` +
                            `📝 Estos son posts de ejemplo basados en el enlace proporcionado\n` +
                            `🖼️ ${tweetsWithImages} posts con imágenes incluidas\n` +
                            `💾 Datos guardados en la base de datos correctamente\n\n` +
                            `ℹ️ Para obtener tweets REALES, necesitarías:\n` +
                            `- Autenticación en Twitter/X\n` +
                            `- API oficial de Twitter/X\n` +
                            `- O usar herramientas especializadas`;
                  } else {
                    message = `✅ ✅ ✅ SCRAPING REAL COMPLETADO EXITOSAMENTE\n\n` +
                            `🎉 Estos son tweets REALES extraídos del enlace\n` +
                            `📊 ${totalScraped} tweets REALES extraídos de Twitter/X\n` +
                            `💾 ${totalSaved} posts guardados en la base de datos\n` +
                            `🖼️ ${tweetsWithImages} posts con imágenes incluidas`;
                  }
                }
        
        setSuccess(message);
        
        // SOLO usar los posts de la respuesta si están disponibles Y si el scraping fue exitoso
        if (response.success && response.posts && response.posts.length > 0) {
          console.log(`✅ ✅ ✅ Usando ${response.posts.length} posts REALES de la respuesta del scraping`);
          // Parsear los posts de la respuesta
          const parsedPosts = response.posts.map((post: any) => {
            let hashtags = post.hashtags || [];
            if (typeof post.hashtags === 'string') {
              try {
                hashtags = JSON.parse(post.hashtags || '[]');
              } catch (e) {
                hashtags = [];
              }
            }
            
            // Para Reddit: Si username es "unknown", usar subreddit o "Reddit"
            let username = post.username || '';
            if (post.platform === 'reddit' && (username === 'unknown' || username === 'Unknown' || !username)) {
              const subreddit = post.subreddit || (post as any).subreddit;
              if (subreddit && subreddit !== 'all') {
                username = subreddit.startsWith('r/') ? subreddit : `r/${subreddit}`;
              } else {
                username = 'Reddit';
              }
            }
            
            const postData = {
              ...post,
              hashtags: Array.isArray(hashtags) ? hashtags : [],
              image_url: post.image_url || null,
              video_url: post.video_url || null,
              username: username,  // Username procesado (con fallback para Reddit)
              subreddit: post.subreddit || (post as any).subreddit,  // Preservar subreddit
              title: post.title || (post as any).title  // Preservar título para Reddit
            };
            
            // Log para verificar image_url
            if (postData.image_url) {
              console.log(`✅ Post ${postData.id} tiene imagen REAL: ${postData.image_url.substring(0, 50)}...`);
            }
            
            return postData;
          });
          
          setPosts(parsedPosts);
          console.log(`📊 ✅ Posts REALES establecidos: ${parsedPosts.length}`);
          console.log(`🖼️ Posts con imágenes REALES: ${parsedPosts.filter(p => p.image_url).length}`);
          
          // Cargar estadísticas solo si hay posts reales
          await loadStats();
        } else {
          // Si el scraping falló, LIMPIAR los posts viejos y NO cargar desde BD
          console.log('❌ Scraping falló o no hay posts REALES - LIMPIANDO posts viejos');
          setPosts([]); // LIMPIAR posts viejos
          // Resetear estadísticas
          setStats({
            total: 0,
            by_platform: {},
            unique_categories: 0
          });
          // NO cargar posts viejos de la base de datos si el scraping falló
        }
        
        // Limpiar campos
        setQuery(''); // Limpiar query
        setUrl(''); // Limpiar URL
      } else {
        // Si hay error, mostrar mensaje de error y LIMPIAR posts viejos
        const errorMsg = response.error || 'Error en el scraping';
        const message = response.message || errorMsg;
        const suggestion = response.suggestion || '';
        setError(message + (suggestion ? `\n\n💡 ${suggestion}` : ''));
        // LIMPIAR posts viejos cuando hay error
        setPosts([]);
        // Resetear estadísticas
        setStats({
          total: 0,
          by_platform: {},
          unique_categories: 0
        });
        console.log('❌ Error en scraping - NO se cargarán posts viejos');
      }
    } catch (err: any) {
      // Si hay error, intentar mostrar mensaje del servidor o usar uno genérico
      const errorMsg = err.response?.data?.error || err.response?.data?.message || err.message || 'Error al realizar scraping';
      console.error('❌ Error en scraping:', err);
      
      // SIEMPRE limpiar posts viejos cuando hay error
      setPosts([]);
      setStats({
        total: 0,
        by_platform: {},
        unique_categories: 0
      });
      
      // Solo mostrar datos si el scraping fue exitoso
      if (err.response?.data?.success && err.response?.data?.posts && err.response?.data?.posts.length > 0) {
        setSuccess(err.response.data.message || '✅ Scraping completado');
        // Aquí sí podemos cargar los posts porque el scraping fue exitoso
        const parsedPosts = err.response.data.posts.map((post: any) => {
          let hashtags = post.hashtags || [];
          if (typeof post.hashtags === 'string') {
            try {
              hashtags = JSON.parse(post.hashtags || '[]');
            } catch (e) {
              hashtags = [];
            }
          }
          return {
            ...post,
            hashtags: Array.isArray(hashtags) ? hashtags : [],
            image_url: post.image_url || null,
            video_url: post.video_url || null
          };
        });
        setPosts(parsedPosts);
        await loadStats();
      } else {
        setError(errorMsg);
        console.log('❌ Error en scraping - NO se cargarán posts viejos');
      }
    } finally {
      setScraping(false);
    }
  };

  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case 'positive':
        return <PositiveIcon sx={{ color: 'success.main' }} />;
      case 'negative':
        return <NegativeIcon sx={{ color: 'error.main' }} />;
      default:
        return <NeutralIcon sx={{ color: 'warning.main' }} />;
    }
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive':
        return 'success';
      case 'negative':
        return 'error';
      default:
        return 'warning';
    }
  };

  const getCategoryColor = (category: string) => {
    if (!category) return 'default';
    const colors: { [key: string]: 'default' | 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info' } = {
      'tecnología': 'primary',
      'tecnologia': 'primary',
      'deportes': 'success',
      'política': 'error',
      'politica': 'error',
      'entretenimiento': 'warning',
      'negocios': 'info',
      'salud': 'secondary',
      'general': 'default',
    };
    return colors[category.toLowerCase()] || 'default';
  };

  const totalPages = Math.max(1, Math.ceil(posts.length / POSTS_PER_PAGE));
  const paginatedPosts = posts.slice((currentPage - 1) * POSTS_PER_PAGE, currentPage * POSTS_PER_PAGE);

  const handlePageChange = (_event: React.ChangeEvent<unknown>, value: number) => {
    setCurrentPage(value);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Datos para gráficos
  const categoryChartData = stats?.by_category ? {
    labels: Object.keys(stats.by_category),
    datasets: [
      {
        label: 'Posts por Categoría',
        data: Object.values(stats.by_category),
        backgroundColor: [
          'rgba(54, 162, 235, 0.6)',
          'rgba(255, 99, 132, 0.6)',
          'rgba(255, 206, 86, 0.6)',
          'rgba(75, 192, 192, 0.6)',
          'rgba(153, 102, 255, 0.6)',
          'rgba(255, 159, 64, 0.6)',
        ],
      },
    ],
  } : null;

  const sentimentChartData = stats?.by_sentiment ? {
    labels: Object.keys(stats.by_sentiment),
    datasets: [
      {
        label: 'Distribución de Sentimientos',
        data: Object.values(stats.by_sentiment),
        backgroundColor: [
          'rgba(75, 192, 192, 0.6)',
          'rgba(255, 99, 132, 0.6)',
          'rgba(255, 206, 86, 0.6)',
        ],
      },
    ],
  } : null;

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 'bold' }}>
          <TwitterIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Redes Sociales - Proyecto Académico
        </Typography>
        <Alert severity="info" sx={{ mt: 2, mb: 2 }}>
          <strong>⚠️ DISCLAIMER:</strong> Este módulo es solo para fines educativos y académicos.
          El scraping se realiza de manera responsable con delays y límites éticos.
        </Alert>
        <Alert severity="info" sx={{ mb: 2 }}>
          <strong>📚 PROYECTO ACADÉMICO:</strong> Este sistema funciona en modo demostración académico.
          Si Twitter/X requiere autenticación, se generarán automáticamente tweets de ejemplo basados en tu búsqueda.
          El sistema procesa, analiza y categoriza los datos normalmente para fines educativos.
        </Alert>
      </Box>

      {/* Panel de Scraping */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            🔍 Configuración de Scraping
          </Typography>
          
          {/* Selector de plataforma */}
          <Box sx={{ mb: 2 }}>
            <FormControl fullWidth>
              <InputLabel>Plataforma</InputLabel>
              <Select
                value={platform}
                onChange={(e) => {
                  setPlatform(e.target.value as 'twitter' | 'facebook' | 'reddit' | 'youtube');
                  setQuery('');
                  setUrl('');
                }}
                label="Plataforma"
                disabled={scraping}
              >
                <MenuItem value="twitter">Twitter/X</MenuItem>
                <MenuItem value="facebook">Facebook</MenuItem>
                <MenuItem value="reddit">Reddit</MenuItem>
                <MenuItem value="youtube">YouTube</MenuItem>
              </Select>
            </FormControl>
          </Box>

          {/* Selector de modo */}
          <Box sx={{ mb: 2 }}>
            <FormControl fullWidth>
              <InputLabel>Modo de Scraping</InputLabel>
              <Select
                value={scrapeMode}
                onChange={(e) => {
                  setScrapeMode(e.target.value as 'query' | 'url');
                  setQuery('');
                  setUrl('');
                }}
                label="Modo de Scraping"
                disabled={scraping}
              >
                <MenuItem value="query">Búsqueda por Hashtag/Palabra Clave</MenuItem>
                <MenuItem value="url">Scraping desde URL {platform === 'facebook' ? 'de Facebook' : platform === 'reddit' ? 'de Reddit' : platform === 'youtube' ? 'de YouTube' : 'de Twitter/X'}</MenuItem>
              </Select>
            </FormControl>
          </Box>

          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(4, 1fr)' }, gap: 2, mt: 1 }}>
            {scrapeMode === 'query' ? (
              <Box>
                <TextField
                  fullWidth
                  label="Hashtag o Palabra Clave"
                  placeholder="#tecnologia o tecnologia"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  disabled={scraping}
                />
              </Box>
            ) : (
              <Box>
                <TextField
                  fullWidth
                  label={`URL de ${platform === 'facebook' ? 'Facebook' : platform === 'reddit' ? 'Reddit' : platform === 'youtube' ? 'YouTube' : 'Twitter/X'}`}
                  placeholder={
                    platform === 'facebook' 
                      ? 'https://facebook.com/pagina' 
                      : platform === 'reddit'
                      ? 'https://reddit.com/r/subreddit o https://www.reddit.com/r/subreddit'
                      : platform === 'youtube'
                      ? 'https://www.youtube.com/@canal o https://www.youtube.com/channel/UCxxxxx'
                      : 'https://twitter.com/usuario o https://x.com/usuario'
                  }
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  disabled={scraping}
                  helperText={
                    platform === 'facebook'
                      ? 'URL de perfil o página de Facebook'
                      : platform === 'reddit'
                      ? 'URL del subreddit de Reddit (ej: https://reddit.com/r/python)'
                      : platform === 'youtube'
                      ? 'URL del canal de YouTube (ej: https://www.youtube.com/@canal o https://www.youtube.com/channel/UCxxxxx)'
                      : 'URL de perfil o página de Twitter/X'
                  }
                />
              </Box>
            )}
            <Box>
              <TextField
                fullWidth
                type="number"
                label="Máximo Posts"
                value={maxPosts}
                onChange={(e) => setMaxPosts(Math.max(parseInt(e.target.value) || 50, 1))}
                inputProps={{ min: 1 }}
                disabled={scraping}
                helperText="Cantidad de posts a extraer (sin límite para fines académicos)"
              />
            </Box>
            <Box>
              <FormControl fullWidth>
                <InputLabel>Idioma</InputLabel>
                <Select
                  value={filterLanguage}
                  onChange={(e) => setFilterLanguage(e.target.value)}
                  label="Idioma"
                  disabled={scraping}
                >
                  <MenuItem value="">Todos</MenuItem>
                  <MenuItem value="es">Español</MenuItem>
                  <MenuItem value="en">Inglés</MenuItem>
                </Select>
              </FormControl>
            </Box>
            <Box>
              <Button
                fullWidth
                variant="contained"
                startIcon={scraping ? <CircularProgress size={20} /> : <SearchIcon />}
                onClick={handleScrape}
                disabled={scraping || (scrapeMode === 'query' ? !query.trim() : !url.trim())}
                sx={{ height: '56px' }}
              >
                {scraping ? 'Scrapeando...' : 'Iniciar Scraping'}
              </Button>
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Mensajes de Error/Success */}
      {error && (
        <Alert 
          severity="error" 
          sx={{ mb: 2, whiteSpace: 'pre-line' }} 
          onClose={() => setError(null)}
        >
          {error}
        </Alert>
      )}
      {success && (
        <Alert 
          severity="success" 
          sx={{ 
            mb: 2,
            whiteSpace: 'pre-line',  // Permitir saltos de línea
            fontSize: '0.95rem',
            '& .MuiAlert-message': {
              width: '100%'
            }
          }} 
          onClose={() => setSuccess(null)}
        >
          <Typography component="div" sx={{ fontWeight: 600, mb: 1, fontSize: '1rem' }}>
            {success.split('\n')[0]}
          </Typography>
          {success.split('\n').slice(1).filter(line => line.trim()).map((line, idx) => (
            <Typography key={idx} component="div" sx={{ fontSize: '0.9rem', mt: 0.5 }}>
              {line}
            </Typography>
          ))}
        </Alert>
      )}

      {/* Estadísticas */}
      {stats && (
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 3, mb: 4 }}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6" color="primary">
              Total Posts
            </Typography>
            <Typography variant="h4" sx={{ mt: 1 }}>
              {stats.total_posts || 0}
            </Typography>
          </Paper>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6" color="primary">
              Por Plataforma
            </Typography>
            <Typography variant="h4" sx={{ mt: 1 }}>
              {stats.by_platform?.twitter || 0}
            </Typography>
          </Paper>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6" color="primary">
              Categorías Únicas
            </Typography>
            <Typography variant="h4" sx={{ mt: 1 }}>
              {Object.keys(stats.by_category || {}).length}
            </Typography>
          </Paper>
        </Box>
      )}

      {/* Gráficos */}
      {stats && (
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, gap: 3, mb: 4 }}>
          {categoryChartData && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <CategoryIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Posts por Categoría
                </Typography>
                <Box sx={{ height: 300 }}>
                  <Bar data={categoryChartData} options={{ maintainAspectRatio: false }} />
                </Box>
              </CardContent>
            </Card>
          )}
          {sentimentChartData && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <TrendingUpIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Distribución de Sentimientos
                </Typography>
                <Box sx={{ height: 300 }}>
                  <Pie data={sentimentChartData} options={{ maintainAspectRatio: false }} />
                </Box>
              </CardContent>
            </Card>
          )}
        </Box>
      )}

      {/* Filtros */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Stack
            direction={{ xs: 'column', md: 'row' }}
            spacing={2}
            justifyContent="space-between"
            alignItems={{ xs: 'flex-start', md: 'center' }}
            sx={{ mb: 3 }}
          >
            <Box sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 1.5 }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                Filtrar por red social:
              </Typography>
              {platformFilters.map((item) => {
                const isActive = platform === item.value;
                return (
                  <Tooltip key={item.value} title={item.description} arrow>
                    <Chip
                      label={item.label}
                      onClick={() => {
                        if (platform === item.value) return;
                        setPlatform(item.value);
                        setQuery('');
                        setUrl('');
                      }}
                      variant={isActive ? 'filled' : 'outlined'}
                      sx={{
                        bgcolor: isActive ? item.color : 'transparent',
                        color: isActive ? '#fff' : 'text.primary',
                        borderColor: item.color,
                        fontWeight: isActive ? 600 : 500,
                        '&:hover': {
                          bgcolor: isActive ? item.color : `${item.color}10`,
                        },
                      }}
                    />
                  </Tooltip>
                );
              })}
            </Box>

            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5} sx={{ width: { xs: '100%', md: 'auto' } }}>
              <Button
                variant="outlined"
                startIcon={<DownloadIcon />}
                onClick={handleExportExcel}
                disabled={!posts.length}
              >
                Descargar Excel
              </Button>
              <Button
                variant="contained"
                color="primary"
                startIcon={<DownloadIcon />}
                onClick={handleExportAllExcel}
              >
                Todas las redes (Excel)
              </Button>
            </Stack>
          </Stack>

          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mb: 2, flexWrap: 'wrap' }}>
            <FormControl sx={{ minWidth: 150 }}>
              <InputLabel>Categoría</InputLabel>
              <Select
                value={filterCategory}
                onChange={(e) => setFilterCategory(e.target.value)}
                label="Categoría"
              >
                <MenuItem value="">Todas</MenuItem>
                <MenuItem value="tecnología">Tecnología</MenuItem>
                <MenuItem value="deportes">Deportes</MenuItem>
                <MenuItem value="política">Política</MenuItem>
                <MenuItem value="entretenimiento">Entretenimiento</MenuItem>
                <MenuItem value="negocios">Negocios</MenuItem>
                <MenuItem value="salud">Salud</MenuItem>
                <MenuItem value="general">General</MenuItem>
              </Select>
            </FormControl>
            <FormControl sx={{ minWidth: 150 }}>
              <InputLabel>Sentimiento</InputLabel>
              <Select
                value={filterSentiment}
                onChange={(e) => setFilterSentiment(e.target.value)}
                label="Sentimiento"
              >
                <MenuItem value="">Todos</MenuItem>
                <MenuItem value="positive">Positivo</MenuItem>
                <MenuItem value="neutral">Neutral</MenuItem>
                <MenuItem value="negative">Negativo</MenuItem>
              </Select>
            </FormControl>
            <FormControl sx={{ minWidth: 150 }}>
              <InputLabel>Idioma</InputLabel>
              <Select
                value={filterLanguage}
                onChange={(e) => setFilterLanguage(e.target.value)}
                label="Idioma"
              >
                {languageOptions.map((lang) => (
                  <MenuItem key={lang.value || 'all'} value={lang.value}>
                    {lang.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <IconButton onClick={loadPosts} color="primary">
              <RefreshIcon />
            </IconButton>
          </Box>

          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
            <TextField
              label="Desde"
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              InputLabelProps={{ shrink: true }}
              sx={{ minWidth: 160 }}
            />
            <TextField
              label="Hasta"
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              InputLabelProps={{ shrink: true }}
              sx={{ minWidth: 160 }}
            />
            <TextField
              label="Mínimo interacciones"
              type="number"
              value={minInteractions}
              onChange={(e) => setMinInteractions(e.target.value)}
              inputProps={{ min: 0 }}
              sx={{ minWidth: 200 }}
            />
            <FormControl sx={{ minWidth: 180 }}>
              <InputLabel>Top por métrica</InputLabel>
              <Select
                value={topMetric}
                onChange={(e) => setTopMetric(e.target.value as typeof topMetric)}
                label="Top por métrica"
              >
                <MenuItem value="none">Sin orden especial</MenuItem>
                <MenuItem value="likes">Más likes</MenuItem>
                <MenuItem value="retweets">Más compartidos</MenuItem>
                <MenuItem value="replies">Más comentarios</MenuItem>
                <MenuItem value="engagement">Mayor engagement total</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label="Top N"
              type="number"
              value={topLimit}
              onChange={(e) => setTopLimit(e.target.value)}
              inputProps={{ min: 1 }}
              disabled={topMetric === 'none'}
              sx={{ minWidth: 140 }}
            />
            <Button
              variant="text"
              onClick={() => {
                setStartDate('');
                setEndDate('');
                setMinInteractions('');
                setTopMetric('none');
                setTopLimit('');
                setFilterLanguage('');
              }}
            >
              Limpiar filtros avanzados
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* Lista de Posts */}
      <Typography variant="h5" gutterBottom sx={{ mb: 2 }}>
        Posts Extraídos ({posts.length})
      </Typography>

      {posts.length === 0 ? (
        <Card>
          <CardContent>
            <Typography variant="body1" color="text.secondary" align="center" sx={{ py: 4 }}>
              No hay posts disponibles. Realiza un scraping para comenzar.
            </Typography>
          </CardContent>
        </Card>
      ) : (
        <>
          {posts.length > POSTS_PER_PAGE && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
              <Pagination
                count={totalPages}
                page={currentPage}
                onChange={handlePageChange}
                color="primary"
                shape="rounded"
                showFirstButton
                showLastButton
              />
            </Box>
          )}

          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)', lg: 'repeat(3, 1fr)' }, gap: 2 }}>
            {paginatedPosts.map((post) => (
              <Box key={post.id}>
                <Card
                  sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    borderRadius: 2,
                    boxShadow: 2,
                    height: '100%',
                    '&:hover': {
                      boxShadow: 4,
                    }
                  }}
                >
                  <CardContent
                    sx={{
                      p: 2,
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 1.5
                    }}
                  >
                    {/* Header estilo Twitter/X */}
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1.5 }}>
                      <Box sx={{ 
                        width: 40, 
                        height: 40, 
                        borderRadius: '50%', 
                        bgcolor: post.platform === 'reddit' ? '#ff4500' : 'primary.main',  // Color naranja para Reddit
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'white',
                        fontWeight: 'bold',
                        mr: 1.5,
                        fontSize: '0.9rem'
                      }}>
                        {/* Mostrar inicial del username o subreddit, o "R" para Reddit */}
                        {(() => {
                          const displayName = post.username.replace('@', '').replace('r/', '').trim();
                          if (displayName && displayName.length > 0 && displayName !== 'unknown' && displayName !== 'Unknown') {
                            return displayName.charAt(0).toUpperCase();
                          } else if (post.platform === 'reddit') {
                            return 'R';  // "R" para Reddit
                          } else {
                            return displayName.charAt(0)?.toUpperCase() || 'U';
                          }
                        })()}
                      </Box>
                      <Box sx={{ flexGrow: 1 }}>
                        <Typography variant="subtitle2" sx={{ fontWeight: 'bold', color: 'text.primary' }}>
                          {(() => {
                            const displayName = post.username.replace('@', '').trim();
                            if ((displayName === 'unknown' || displayName === 'Unknown' || !displayName) && post.platform === 'reddit') {
                              const subreddit = (post as any).subreddit;
                              if (subreddit && subreddit !== 'all') {
                                return subreddit.startsWith('r/') ? subreddit : `r/${subreddit}`;
                              }
                              return 'Reddit';
                            }
                            return displayName;
                          })()}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {post.platform === 'reddit'
                            ? (() => {
                                const subredditLabel = post.subreddit || (post as any).subreddit;
                                if (subredditLabel && subredditLabel !== 'all') {
                                  return subredditLabel.startsWith('r/') ? subredditLabel : `r/${subredditLabel}`;
                                }
                                return 'Reddit';
                              })()
                            : post.username}
                        </Typography>
                      </Box>
                      {post.created_at && (
                        <Typography variant="caption" color="text.secondary">
                          {new Date(post.created_at).toLocaleDateString('es-PE', { 
                            month: 'short', 
                            day: 'numeric' 
                          })}
                        </Typography>
                      )}
                    </Box>
                    
                    {/* Contenido */}
                    {post.platform === 'reddit' ? (() => {
                      const title = (post.title || '').trim();
                      const body = (post.content || '').trim();
                      const fallbackText = (post.text || '').trim();

                      if (!title && !body && fallbackText) {
                        return (
                          <Box
                            sx={{
                              mb: post.image_url ? 2 : 1.5,
                              whiteSpace: 'pre-wrap',
                              wordBreak: 'break-word',
                              lineHeight: 1.6,
                              maxHeight: 220,
                              overflowY: 'auto',
                              pr: 1
                            }}
                          >
                            <Typography variant="body2">
                              {fallbackText}
                            </Typography>
                          </Box>
                        );
                      }

                      return (
                        <Box
                          sx={{
                            display: 'flex',
                            flexDirection: 'column',
                            gap: 1,
                            mb: post.image_url ? 2 : 1.5,
                            maxHeight: 260,
                            overflowY: 'auto',
                            pr: 1
                          }}
                        >
                          {title && (
                            <Typography
                              variant="subtitle1"
                              sx={{
                                fontWeight: 600,
                                whiteSpace: 'pre-wrap',
                                wordBreak: 'break-word'
                              }}
                            >
                              {title}
                            </Typography>
                          )}
                          {body && body !== title && (
                            <Typography
                              variant="body2"
                              sx={{
                                whiteSpace: 'pre-wrap',
                                wordBreak: 'break-word',
                                lineHeight: 1.6
                              }}
                            >
                              {body}
                            </Typography>
                          )}
                        </Box>
                      );
                    })() : (
                      <Box
                        sx={{
                          mb: post.image_url ? 2 : 1.5,
                          maxHeight: 220,
                          overflowY: 'auto',
                          pr: 1
                        }}
                      >
                        <Typography
                          variant="body1"
                          sx={{
                            whiteSpace: 'pre-wrap',
                            wordBreak: 'break-word',
                            lineHeight: 1.5
                          }}
                        >
                          {post.text.split(' ').map((word, idx) => {
                            if (word.startsWith('#')) {
                              return (
                                <span key={idx} style={{ color: '#1d9bf0', fontWeight: 500 }}>
                                  {word}{' '}
                                </span>
                              );
                            }
                            if (word.startsWith('@')) {
                              return (
                                <span key={idx} style={{ color: '#1d9bf0', fontWeight: 500 }}>
                                  {word}{' '}
                                </span>
                              );
                            }
                            if (word.startsWith('http')) {
                              return (
                                <span key={idx} style={{ color: '#1d9bf0' }}>
                                  {word}{' '}
                                </span>
                              );
                            }
                            return word + ' ';
                          })}
                        </Typography>
                      </Box>
                    )}
                    
                    {/* Video (prioridad sobre imagen) */}
                    {post.video_url && post.video_url.trim() !== '' ? (
                      <Box 
                        sx={{ 
                          mb: 2,
                          borderRadius: 2,
                          overflow: 'hidden',
                          border: '1px solid',
                          borderColor: 'divider',
                          bgcolor: '#000',
                          minHeight: '200px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center'
                        }}
                      >
                        <video 
                          controls
                          style={{ 
                            width: '100%', 
                            maxHeight: '400px',
                            objectFit: 'contain',
                            backgroundColor: '#000'
                          }}
                          src={post.video_url}
                          onError={(e: any) => {
                            const target = e.currentTarget;
                            target.style.display = 'none';
                            const parent = target.parentElement;
                            if (parent && post.video_url) {
                              const urlPreview = post.video_url.length > 30 
                                ? post.video_url.substring(0, 30) + '...' 
                                : post.video_url;
                              parent.innerHTML = `
                                <div style="padding: 20px; text-align: center; color: #fff; width: 100%;">
                                  <span>🎥 Video no disponible</span>
                                  <br/>
                                  <small style="font-size: 0.7rem; color: #999;">${urlPreview}</small>
                                </div>
                              `;
                            }
                          }}
                          onLoadedData={() => {
                            console.log('✅ Video cargado exitosamente:', post.video_url);
                          }}
                        />
                      </Box>
                    ) : post.image_url && post.image_url.trim() !== '' ? (
                      /* Imagen estilo Twitter/X */
                      <Box 
                        sx={{ 
                          mb: 2,
                          borderRadius: 2,
                          overflow: 'hidden',
                          border: '1px solid',
                          borderColor: 'divider',
                          cursor: 'pointer',
                          backgroundColor: '#f0f0f0',
                          minHeight: '200px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          position: 'relative',
                          '&:hover': {
                            opacity: 0.9
                          }
                        }}
                      >
                        <img 
                          src={post.image_url} 
                          alt="Tweet media"
                          style={{
                            width: '100%',
                            height: 'auto',
                            display: 'block',
                            maxHeight: '400px',
                            minHeight: '200px',
                            objectFit: 'cover',
                            backgroundColor: '#f0f0f0'
                          }}
                          onError={(e) => {
                            console.error('❌ Error cargando imagen:', post.image_url);
                            const target = e.currentTarget;
                            target.style.display = 'none';
                            const parent = target.parentElement;
                            if (parent && post.image_url) {
                              const urlPreview = post.image_url.length > 30 
                                ? post.image_url.substring(0, 30) + '...' 
                                : post.image_url;
                              parent.innerHTML = `
                                <div style="padding: 20px; text-align: center; color: #999; width: 100%;">
                                  <span>🖼️ Imagen no disponible</span>
                                  <br/>
                                  <small style="font-size: 0.7rem;">${urlPreview}</small>
                                </div>
                              `;
                            }
                          }}
                          onLoad={() => {
                            console.log('✅ Imagen cargada exitosamente:', post.image_url);
                          }}
                        />
                      </Box>
                    ) : (
                      <Box
                        sx={{
                          mb: 2,
                          borderRadius: 2,
                          border: '1px dashed',
                          borderColor: 'divider',
                          backgroundColor: '#fafafa',
                          minHeight: '100px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: '#ccc',
                          fontSize: '0.75rem'
                        }}
                      >
                        Sin imagen (image_url: {post.image_url ? 'presente' : 'null'})
                      </Box>
                    )}

                    {/* Categoría y Sentimiento */}
                    <Box sx={{ display: 'flex', gap: 1, mb: 1.5, flexWrap: 'wrap' }}>
                      {post.platform === 'reddit' && post.subreddit && (
                        <Chip
                          label={post.subreddit.startsWith('r/') ? post.subreddit : `r/${post.subreddit}`}
                          size="small"
                          sx={{
                            fontSize: '0.7rem',
                            height: '24px',
                            bgcolor: '#ff4500',
                            color: '#fff'
                          }}
                        />
                      )}
                      {post.category && (
                        <Chip 
                          label={post.category} 
                          size="small" 
                          sx={{ fontSize: '0.7rem', height: '24px' }}
                        />
                      )}
                      {post.sentiment && (
                        <Chip 
                          label={post.sentiment} 
                          size="small" 
                          sx={{ 
                            fontSize: '0.7rem', 
                            height: '24px',
                            bgcolor: post.sentiment === 'positive' ? '#e8f5e9' : 
                                    post.sentiment === 'negative' ? '#ffebee' : '#fff3e0',
                            color: post.sentiment === 'positive' ? '#2e7d32' : 
                                   post.sentiment === 'negative' ? '#c62828' : '#ef6c00'
                          }}
                        />
                      )}
                    </Box>
                    
                    {/* Interacciones */}
                    {(() => {
                      const linkLabel =
                        post.platform === 'reddit'
                          ? 'Ver post'
                          : post.platform === 'youtube'
                            ? 'Ver video'
                            : post.platform === 'facebook'
                              ? 'Ver publicación'
                              : 'Ver tweet';
                      const upvotes =
                        (typeof post.upvotes === 'number' ? post.upvotes : undefined) ??
                        (typeof post.likes === 'number' ? post.likes : 0);
                      const scoreValue =
                        (typeof post.score === 'number' ? post.score : undefined) ?? upvotes ?? 0;
                      const commentsCount =
                        (typeof post.comments === 'number' ? post.comments : undefined) ??
                        (typeof post.replies === 'number' ? post.replies : 0);

                      if (post.platform === 'reddit') {
                        return (
                          <Box
                            sx={{
                              display: 'flex',
                              justifyContent: 'space-between',
                              alignItems: 'center',
                              pt: 1.5,
                              borderTop: '1px solid',
                              borderColor: 'divider',
                              color: 'text.secondary'
                            }}
                          >
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <ArrowUpwardIcon sx={{ fontSize: 18, color: '#ff4500' }} />
                              <Typography variant="caption">{upvotes ?? 0}</Typography>
                            </Box>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <ChatBubbleOutlineIcon sx={{ fontSize: 18 }} />
                              <Typography variant="caption">{commentsCount ?? 0}</Typography>
                            </Box>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <BarChartIcon sx={{ fontSize: 18 }} />
                              <Typography variant="caption">{scoreValue ?? 0}</Typography>
                            </Box>
                            {post.url && (
                              <Link
                                href={post.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                sx={{
                                  textDecoration: 'none',
                                  color: '#1d9bf0',
                                  fontSize: '0.75rem',
                                  '&:hover': {
                                    textDecoration: 'underline'
                                  }
                                }}
                              >
                                {linkLabel}
                              </Link>
                            )}
                          </Box>
                        );
                      }

                      return (
                        <Box
                          sx={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            pt: 1.5,
                            borderTop: '1px solid',
                            borderColor: 'divider',
                            color: 'text.secondary'
                          }}
                        >
                          <Box
                            sx={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: 1,
                              cursor: 'pointer',
                              '&:hover': { color: '#1d9bf0' }
                            }}
                          >
                            <ChatBubbleOutlineIcon sx={{ fontSize: 18 }} />
                            <Typography variant="caption">{post.replies}</Typography>
                          </Box>
                          <Box
                            sx={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: 1,
                              cursor: 'pointer',
                              '&:hover': { color: '#00ba7c' }
                            }}
                          >
                            <RepeatIcon sx={{ fontSize: 18 }} />
                            <Typography variant="caption">{post.retweets}</Typography>
                          </Box>
                          <Box
                            sx={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: 1,
                              cursor: 'pointer',
                              '&:hover': { color: '#f91880' }
                            }}
                          >
                            <FavoriteIcon sx={{ fontSize: 18 }} />
                            <Typography variant="caption">{post.likes}</Typography>
                          </Box>
                          <Box
                            sx={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: 1,
                              cursor: 'pointer',
                              '&:hover': { color: '#1d9bf0' }
                            }}
                          >
                            <BarChartIcon sx={{ fontSize: 18 }} />
                            <Typography variant="caption">
                              {Math.floor(post.likes * 2.5 + post.retweets * 3)}
                            </Typography>
                          </Box>
                          {post.url && (
                            <Link
                              href={post.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              sx={{
                                textDecoration: 'none',
                                color: '#1d9bf0',
                                fontSize: '0.75rem',
                                '&:hover': {
                                  textDecoration: 'underline'
                                }
                              }}
                            >
                              {linkLabel}
                            </Link>
                          )}
                        </Box>
                      );
                    })()}
                  </CardContent>
                </Card>
              </Box>
            ))}
          </Box>

          {totalPages > 1 && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
              <Pagination
                count={totalPages}
                page={currentPage}
                onChange={handlePageChange}
                color="primary"
                size="small"
                shape="rounded"
                showFirstButton
                showLastButton
              />
            </Box>
          )}
        </>
      )}
    </Container>
  );
};

export default SocialMedia;

