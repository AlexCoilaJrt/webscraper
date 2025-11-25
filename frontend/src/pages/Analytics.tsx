import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  Alert,
  Chip,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  LinearProgress,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  TrendingFlat,
  Refresh,
  Newspaper,
  Category,
} from '@mui/icons-material';
import { api } from '../services/api';
import ReactECharts from '../components/analytics/ReactEChartsLite';

interface TrendData {
  period: string;
  articles_count: number;
  images_count: number;
  newspapers_count: number;
}

interface SentimentData {
  positive: number;
  negative: number;
  neutral: number;
  total: number;
  by_newspaper: Record<string, { positive: number; negative: number; neutral: number }>;
  by_category: Record<string, { positive: number; negative: number; neutral: number }>;
}

interface WordCloudData {
  text: string;
  value: number;
}

interface ComparisonData {
  newspaper: string;
  total_articles: number;
  total_images: number;
  categories_count: number;
  avg_content_length: number;
  articles_per_day: number;
}

const Analytics: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState('week');
  
  // Datos de tendencias
  const [trendsData, setTrendsData] = useState<TrendData[]>([]);
  const [topCategories, setTopCategories] = useState<Array<{category: string; count: number}>>([]);
  const [topNewspapers, setTopNewspapers] = useState<Array<{newspaper: string; count: number}>>([]);
  
  // Datos de sentimientos
  const [sentimentData, setSentimentData] = useState<SentimentData | null>(null);
  
  // Datos de nube de palabras
  const [wordCloudData, setWordCloudData] = useState<WordCloudData[]>([]);
  
  // Datos de comparación
  const [comparisonData, setComparisonData] = useState<ComparisonData[]>([]);

  const fetchAnalyticsData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Obtener datos de tendencias
      const trendsResponse = await api.get(`/analytics/trends?period=${period}`);
      const trendsData = trendsResponse.data as any;
      setTrendsData(trendsData.trends);
      setTopCategories(trendsData.top_categories);
      setTopNewspapers(trendsData.top_newspapers);
      
      // Obtener datos de sentimientos
      const sentimentResponse = await api.get('/analytics/sentiment');
      setSentimentData(sentimentResponse.data as any);
      
      // Obtener datos de nube de palabras
      const wordCloudResponse = await api.get('/analytics/wordcloud');
      const wordCloudData = wordCloudResponse.data as any;
      setWordCloudData(wordCloudData.words);
      
      // Obtener datos de comparación
      const comparisonResponse = await api.get('/analytics/comparison');
      const comparisonData = comparisonResponse.data as any;
      setComparisonData(comparisonData.newspaper_stats);
      
    } catch (err) {
      setError('Error cargando datos de análisis');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalyticsData();
  }, [period]); // eslint-disable-line react-hooks/exhaustive-deps

  const handlePeriodChange = (event: any) => {
    setPeriod(event.target.value);
  };

  const COLORS = ['#0ea5e9', '#0284c7', '#0369a1', '#075985', '#0c4a6e'];

  // Opciones de ECharts
  const buildTimeSeriesOptions = () => {
    const x = trendsData.map(t => t.period);
    const y = trendsData.map(t => t.articles_count);
    // Media móvil simple de ventana 3
    const ma = y.map((_, i) => {
      const start = Math.max(0, i - 2);
      const arr = y.slice(start, i + 1);
      const avg = arr.reduce((s, v) => s + v, 0) / arr.length;
      return parseFloat(avg.toFixed(2));
    });
    return {
      tooltip: { trigger: 'axis' },
      grid: { left: 40, right: 20, top: 30, bottom: 30 },
      xAxis: { type: 'category', data: x, boundaryGap: false },
      yAxis: { type: 'value' },
      legend: { data: ['Artículos', 'Media móvil'], bottom: 0 },
      series: [
        {
          name: 'Artículos',
          type: 'line',
          areaStyle: { opacity: 0.15 },
          smooth: true,
          showSymbol: false,
          data: y,
          color: '#0ea5e9'
        },
        {
          name: 'Media móvil',
          type: 'line',
          smooth: true,
          showSymbol: false,
          data: ma,
          color: '#0369a1'
        }
      ]
    };
  };

  const buildSentimentDonut = () => {
    if (!sentimentData) return {};
    const total = sentimentData.total || 1;
    const pos = Math.round((sentimentData.positive / total) * 100);
    const neg = Math.round((sentimentData.negative / total) * 100);
    const neu = Math.round((sentimentData.neutral / total) * 100);
    return {
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      legend: { bottom: 0 },
      series: [
        {
          name: 'Sentimiento',
          type: 'pie',
          radius: ['50%', '70%'],
          avoidLabelOverlap: false,
          label: { show: true, position: 'center', formatter: `${pos}%\nPositivo`, fontSize: 18 },
          emphasis: { label: { show: true, fontSize: 20, fontWeight: 'bold' } },
          labelLine: { show: false },
          data: [
            { value: sentimentData.positive, name: 'Positivo', itemStyle: { color: '#10b981' } },
            { value: sentimentData.neutral, name: 'Neutral', itemStyle: { color: '#f59e0b' } },
            { value: sentimentData.negative, name: 'Negativo', itemStyle: { color: '#ef4444' } }
          ]
        }
      ]
    };
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress size={60} />
      </Box>
    );
  }

  if (error) {
    return (
      <Box p={3}>
        <Alert severity="error" action={
          <IconButton color="inherit" size="small" onClick={fetchAnalyticsData}>
            <Refresh />
          </IconButton>
        }>
          {error}
        </Alert>
      </Box>
    );
  }

  return (
    <Box p={3}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" fontWeight="bold" color="primary">
          📊 Análisis Avanzado
        </Typography>
        <Box display="flex" gap={2} alignItems="center">
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Período</InputLabel>
            <Select value={period} onChange={handlePeriodChange} label="Período">
              <MenuItem value="day">Diario</MenuItem>
              <MenuItem value="week">Semanal</MenuItem>
              <MenuItem value="month">Mensual</MenuItem>
            </Select>
          </FormControl>
          <Tooltip title="Actualizar datos">
            <IconButton onClick={fetchAnalyticsData} color="primary">
              <Refresh />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Layout con Box en lugar de Grid */}
      <Box display="flex" flexDirection="column" gap={3}>
        {/* Primera fila - Gráfico de Tendencias y Análisis de Sentimientos */}
        <Box display="flex" gap={3} flexWrap="wrap">
          {/* Gráfico de Tendencias - ECharts */}
          <Box flex="2" minWidth="400px">
            <Card elevation={2}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  📈 Tendencias de Contenido
                </Typography>
                <Box sx={{ height: 320 }}>
                  <ReactECharts style={{ height: 300 }} option={buildTimeSeriesOptions()} />
                </Box>
              </CardContent>
            </Card>
          </Box>

          {/* Análisis de Sentimientos - Donut */}
          <Box flex="1" minWidth="300px">
            <Card elevation={2}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  😊 Análisis de Sentimientos
                </Typography>
                {sentimentData && (<ReactECharts style={{ height: 300 }} option={buildSentimentDonut()} />)}
              </CardContent>
            </Card>
          </Box>
        </Box>

        {/* Segunda fila - Top Categorías y Top Periódicos */}
        <Box display="flex" gap={3} flexWrap="wrap">
          {/* Top Categorías */}
          <Box flex="1" minWidth="300px">
            <Card elevation={2}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  🏷️ Top Categorías
                </Typography>
                <List>
                  {topCategories.slice(0, 8).map((item, index) => (
                    <ListItem key={item.category} divider={index < 7}>
                      <ListItemIcon>
                        <Category color="primary" />
                      </ListItemIcon>
                      <ListItemText
                        primary={item.category}
                        secondary={`${item.count} artículos`}
                      />
                      <Chip
                        label={item.count}
                        size="small"
                        color="primary"
                        variant="outlined"
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Box>

          {/* Top Periódicos */}
          <Box flex="1" minWidth="300px">
            <Card elevation={2}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  📰 Top Periódicos
                </Typography>
                <List>
                  {topNewspapers.slice(0, 8).map((item, index) => (
                    <ListItem key={item.newspaper} divider={index < 7}>
                      <ListItemIcon>
                        <Newspaper color="primary" />
                      </ListItemIcon>
                      <ListItemText
                        primary={item.newspaper}
                        secondary={`${item.count} artículos`}
                      />
                      <Chip
                        label={item.count}
                        size="small"
                        color="primary"
                        variant="outlined"
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Box>
        </Box>

        {/* Tercera fila - Nube de Palabras y Comparación de Periódicos */}
        <Box display="flex" gap={3} flexWrap="wrap">
          {/* Nube de Palabras */}
          <Box flex="1" minWidth="400px">
            <Card elevation={2}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  ☁️ Palabras Más Frecuentes
                </Typography>
                <Box
                  sx={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: 1,
                    maxHeight: 300,
                    overflow: 'auto',
                    p: 2,
                    backgroundColor: '#f8fafc',
                    borderRadius: 2,
                  }}
                >
                  {wordCloudData.slice(0, 30).map((word, index) => (
                    <Chip
                      key={word.text}
                      label={word.text}
                      size="small"
                      sx={{
                        fontSize: Math.min(16, Math.max(10, word.value / 5)),
                        backgroundColor: COLORS[index % COLORS.length],
                        color: 'white',
                        '&:hover': {
                          backgroundColor: COLORS[index % COLORS.length],
                          opacity: 0.8,
                        },
                      }}
                    />
                  ))}
                </Box>
              </CardContent>
            </Card>
          </Box>

          {/* Comparación de Periódicos - Versión Simple */}
          <Box flex="1" minWidth="400px">
            <Card elevation={2}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  📊 Comparación de Periódicos
                </Typography>
                <Box sx={{ height: 300, overflow: 'auto' }}>
                  {comparisonData.slice(0, 8).map((newspaper, index) => (
                    <Box key={newspaper.newspaper} mb={2}>
                      <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                        <Typography variant="subtitle1" fontWeight="bold">
                          {newspaper.newspaper}
                        </Typography>
                        <Chip 
                          label={`${newspaper.total_articles} artículos`}
                          size="small"
                          color="primary"
                          variant="outlined"
                        />
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={Math.min(100, (newspaper.total_articles / Math.max(...comparisonData.map(n => n.total_articles))) * 100)}
                        sx={{ height: 8, borderRadius: 4 }}
                      />
                      <Box display="flex" justifyContent="space-between" mt={1}>
                        <Typography variant="body2" color="text.secondary">
                          {newspaper.total_images} imágenes
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {newspaper.categories_count} categorías
                        </Typography>
                      </Box>
                    </Box>
                  ))}
                </Box>
              </CardContent>
            </Card>
          </Box>
        </Box>

        {/* Cuarta fila - Estadísticas Detalladas */}
        <Box>
          <Card elevation={2}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                📈 Estadísticas Detalladas por Periódico
              </Typography>
              <Box display="flex" flexWrap="wrap" gap={2}>
                {comparisonData.map((newspaper, index) => (
                  <Paper
                    key={newspaper.newspaper}
                    elevation={1}
                    sx={{
                      p: 2,
                      minWidth: 250,
                      flex: '1 1 250px',
                      backgroundColor: index % 2 === 0 ? '#f8fafc' : 'white',
                      border: '1px solid #e2e8f0',
                    }}
                  >
                    <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                      {newspaper.newspaper}
                    </Typography>
                    
                    <Box mb={1}>
                      <Typography variant="body2" color="text.secondary">
                        Artículos por día
                      </Typography>
                      <LinearProgress
                        variant="determinate"
                        value={Math.min(100, (newspaper.articles_per_day / Math.max(...comparisonData.map(n => n.articles_per_day))) * 100)}
                        sx={{ height: 8, borderRadius: 4 }}
                      />
                      <Typography variant="body2" fontWeight="bold">
                        {newspaper.articles_per_day}
                      </Typography>
                    </Box>
                    
                    <Box display="flex" justifyContent="space-between" mb={1}>
                      <Typography variant="body2">Artículos:</Typography>
                      <Typography variant="body2" fontWeight="bold">
                        {newspaper.total_articles}
                      </Typography>
                    </Box>
                    
                    <Box display="flex" justifyContent="space-between" mb={1}>
                      <Typography variant="body2">Imágenes:</Typography>
                      <Typography variant="body2" fontWeight="bold">
                        {newspaper.total_images}
                      </Typography>
                    </Box>
                    
                    <Box display="flex" justifyContent="space-between">
                      <Typography variant="body2">Categorías:</Typography>
                      <Typography variant="body2" fontWeight="bold">
                        {newspaper.categories_count}
                      </Typography>
                    </Box>
                  </Paper>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Box>
      </Box>
    </Box>
  );
};

export default Analytics;