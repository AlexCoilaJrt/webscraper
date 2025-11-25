import React, { useState, useEffect, useCallback, useMemo } from 'react';
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
  Grid,
  TextField,
  Button,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Refresh,
  SentimentSatisfied,
  SentimentNeutral,
  SentimentDissatisfied,
  TrendingUp,
  TrendingDown,
  Newspaper,
  Category,
  Timeline,
  CompareArrows,
  EmojiEmotions,
} from '@mui/icons-material';
import { api, apiService } from '../services/api';
import ReactECharts from '../components/analytics/ReactEChartsLite';

interface SentimentAnalysisData {
  total: number;
  positive: number;
  negative: number;
  neutral: number;
  average_score: number;
  emotions_summary: Record<string, number>;
  polarization_distribution: {
    high: number;
    medium: number;
    low: number;
  };
  by_newspaper: Record<string, {
    positive: number;
    negative: number;
    neutral: number;
    total: number;
    average_score: number;
  }>;
  by_category: Record<string, {
    positive: number;
    negative: number;
    neutral: number;
    total: number;
    average_score: number;
  }>;
  timeline: Array<{
    date: string;
    positive: number;
    negative: number;
    neutral: number;
    total: number;
    average_score: number;
  }>;
  topic_comparison?: Record<string, {
    average_score: number;
    positive_pct: number;
    negative_pct: number;
    total: number;
  }>;
  viral_comments_comparison?: {
    total: number;
    positive: number;
    negative: number;
    neutral: number;
    average_score: number;
    by_topic: Record<string, {
      positive: number;
      negative: number;
      neutral: number;
      total: number;
      average_score: number;
    }>;
  } | null;
}

const SentimentAnalysis: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<SentimentAnalysisData | null>(null);
  const [days, setDays] = useState(30);
  const [category, setCategory] = useState('');
  const [newspaper, setNewspaper] = useState('');
  const [topic, setTopic] = useState('');
  const [tabValue, setTabValue] = useState(0);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [alertsLoading, setAlertsLoading] = useState(false);
  const [userPlan, setUserPlan] = useState<string>('freemium');
  const [userSubscription, setUserSubscription] = useState<any>(null);
  
  // Estados para debounce
  const [categoryInput, setCategoryInput] = useState('');
  const [newspaperInput, setNewspaperInput] = useState('');
  const [topicInput, setTopicInput] = useState('');

  // Calcular permisos de acceso basados en el plan
  const canAccessViralComparison = useMemo(() => {
    const hasAccess = userPlan === 'premium' || userPlan === 'enterprise';
    console.log('🔐 Acceso a comparación viral:', { userPlan, hasAccess, dataPresent: !!data?.viral_comments_comparison });
    return hasAccess;
  }, [userPlan, data?.viral_comments_comparison]);
  
  const canAccessAlerts = useMemo(() => {
    return userPlan === 'premium' || userPlan === 'enterprise';
  }, [userPlan]);
  
  // Calcular índices de pestañas dinámicamente
  // Pestañas base: 0=Temporal, 1=Periódico, 2=Categoría, 3=Emociones
  // Luego: 4=Noticias vs Comentarios (si está disponible), 5=Comparación de Medios (si hay topic)
  const baseTabsCount = 4; // Temporal, Periódico, Categoría, Emociones
  
  // Verificar si debe mostrarse la pestaña de comparación viral
  const shouldShowViralTab = canAccessViralComparison && data?.viral_comments_comparison;
  const viralComparisonTabIndex = shouldShowViralTab ? baseTabsCount : -1;
  
  const topicComparisonTabIndex = useMemo(() => {
    if (!topic || !data?.topic_comparison) return -1;
    return shouldShowViralTab ? baseTabsCount + 1 : baseTabsCount;
  }, [topic, data?.topic_comparison, shouldShowViralTab, baseTabsCount]);
  
  // Debug: Log cuando cambian las condiciones
  useEffect(() => {
    console.log('📊 Estado completo de comparación:', {
      userPlan,
      canAccessViralComparison,
      hasViralData: !!data?.viral_comments_comparison,
      viralDataTotal: data?.viral_comments_comparison?.total,
      shouldShowViralTab,
      viralComparisonTabIndex,
      currentTabValue: tabValue
    });
  }, [userPlan, canAccessViralComparison, data?.viral_comments_comparison, shouldShowViralTab, viralComparisonTabIndex, tabValue]);

  const fetchSentimentData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams();
      params.append('days', days.toString());
      if (category) params.append('category', category);
      if (newspaper) params.append('newspaper', newspaper);
      if (topic) params.append('topic', topic);
      
      // Usar timeout extendido para análisis de sentimientos (puede tomar tiempo)
      const response = await api.get(`/analytics/sentiment?${params.toString()}`, {
        timeout: 120000 // 2 minutos para análisis de sentimientos
      });
      
      // Validar que la respuesta tenga la estructura esperada
      if (response.data && typeof response.data === 'object') {
        const sentimentData = response.data as SentimentAnalysisData;
        setData(sentimentData);
        // Debug: verificar datos de comparación
        if (sentimentData.viral_comments_comparison) {
          console.log('✅ Datos de comparación viral recibidos:', {
            total: sentimentData.viral_comments_comparison.total,
            positive: sentimentData.viral_comments_comparison.positive,
            negative: sentimentData.viral_comments_comparison.negative,
            score: sentimentData.viral_comments_comparison.average_score
          });
        } else {
          console.log('⚠️ No hay datos de comparación viral en la respuesta');
        }
      } else {
        throw new Error('Respuesta inválida del servidor');
      }
    } catch (err: any) {
      console.error('Error completo:', err);
      const errorMessage = err.response?.data?.error || err.message || 'Error cargando análisis de sentimientos';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [days, category, newspaper, topic]);

  // Debounce para category
  useEffect(() => {
    const timer = setTimeout(() => {
      setCategory(categoryInput);
    }, 800); // Esperar 800ms después de que el usuario deje de escribir
    
    return () => clearTimeout(timer);
  }, [categoryInput]);

  // Debounce para newspaper
  useEffect(() => {
    const timer = setTimeout(() => {
      setNewspaper(newspaperInput);
    }, 800); // Esperar 800ms después de que el usuario deje de escribir
    
    return () => clearTimeout(timer);
  }, [newspaperInput]);

  // Debounce para topic
  useEffect(() => {
    const timer = setTimeout(() => {
      setTopic(topicInput);
    }, 800); // Esperar 800ms después de que el usuario deje de escribir
    
    return () => clearTimeout(timer);
  }, [topicInput]);

  // Ejecutar búsqueda cuando cambien los filtros (después del debounce)
  useEffect(() => {
    fetchSentimentData();
  }, [fetchSentimentData]);

  const buildSentimentDonutChart = () => {
    if (!data) return {};
    
    return {
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: {c} ({d}%)'
      },
      legend: {
        orient: 'vertical',
        left: 'left'
      },
      series: [
        {
          name: 'Sentimiento',
          type: 'pie',
          radius: ['40%', '70%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#fff',
            borderWidth: 2
          },
          label: {
            show: false,
            position: 'center'
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 20,
              fontWeight: 'bold'
            }
          },
          labelLine: {
            show: false
          },
          data: [
            { value: data.positive, name: 'Positivo', itemStyle: { color: '#10b981' } },
            { value: data.neutral, name: 'Neutral', itemStyle: { color: '#f59e0b' } },
            { value: data.negative, name: 'Negativo', itemStyle: { color: '#ef4444' } }
          ]
        }
      ]
    };
  };

  const buildTimelineChart = () => {
    if (!data || !data.timeline || data.timeline.length === 0) return {};
    
    const dates = data.timeline.map(d => d.date);
    const positive = data.timeline.map(d => d.positive);
    const negative = data.timeline.map(d => d.negative);
    const neutral = data.timeline.map(d => d.neutral);
    const scores = data.timeline.map(d => d.average_score);
    
    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross'
        }
      },
      legend: {
        data: ['Positivo', 'Negativo', 'Neutral', 'Score Promedio']
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: dates
      },
      yAxis: [
        {
          type: 'value',
          name: 'Cantidad',
          position: 'left'
        },
        {
          type: 'value',
          name: 'Score',
          position: 'right',
          min: -1,
          max: 1
        }
      ],
      series: [
        {
          name: 'Positivo',
          type: 'line',
          stack: 'Total',
          data: positive,
          itemStyle: { color: '#10b981' },
          areaStyle: { color: 'rgba(16, 185, 129, 0.2)' }
        },
        {
          name: 'Negativo',
          type: 'line',
          stack: 'Total',
          data: negative,
          itemStyle: { color: '#ef4444' },
          areaStyle: { color: 'rgba(239, 68, 68, 0.2)' }
        },
        {
          name: 'Neutral',
          type: 'line',
          stack: 'Total',
          data: neutral,
          itemStyle: { color: '#f59e0b' },
          areaStyle: { color: 'rgba(245, 158, 11, 0.2)' }
        },
        {
          name: 'Score Promedio',
          type: 'line',
          yAxisIndex: 1,
          data: scores,
          itemStyle: { color: '#3b82f6' },
          lineStyle: { width: 3 }
        }
      ]
    };
  };

  const buildComparisonChart = () => {
    if (!data || !data.viral_comments_comparison) return {};
    
    const news = data;
    const comments = data.viral_comments_comparison; // Ya verificado arriba
    
    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        }
      },
      legend: {
        data: ['Noticias', 'Comentarios Virales']
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: ['Positivo', 'Negativo', 'Neutral']
      },
      yAxis: {
        type: 'value'
      },
      series: [
        {
          name: 'Noticias',
          type: 'bar',
          data: [
            news.positive,
            news.negative,
            news.neutral
          ],
          itemStyle: { color: '#3b82f6' }
        },
        {
          name: 'Comentarios Virales',
          type: 'bar',
          data: [
            comments.positive,
            comments.negative,
            comments.neutral
          ],
          itemStyle: { color: '#10b981' }
        }
      ]
    };
  };

  const buildScoreComparisonChart = () => {
    if (!data || !data.viral_comments_comparison) return {};
    
    const comments = data.viral_comments_comparison; // Ya verificado arriba
    
    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        }
      },
      legend: {
        data: ['Noticias', 'Comentarios Virales']
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: ['Score Promedio']
      },
      yAxis: {
        type: 'value',
        min: -1,
        max: 1
      },
      series: [
        {
          name: 'Noticias',
          type: 'bar',
          data: [data.average_score],
          itemStyle: { color: '#3b82f6' }
        },
        {
          name: 'Comentarios Virales',
          type: 'bar',
          data: [comments.average_score],
          itemStyle: { color: '#10b981' }
        }
      ]
    };
  };

  const fetchAlerts = useCallback(async () => {
    if (!canAccessAlerts) {
      setAlerts([]);
      return;
    }
    setAlertsLoading(true);
    try {
      const response = await apiService.getViralCommentsAlerts(7) as { alerts?: any[]; total_alerts?: number; period_days?: number };
      setAlerts(response.alerts || []);
    } catch (err: any) {
      console.error('Error cargando alertas:', err);
      // Si es error 403, el usuario no tiene acceso
      if (err.response?.status === 403) {
        setAlerts([]);
      }
    } finally {
      setAlertsLoading(false);
    }
  }, [canAccessAlerts]);

  useEffect(() => {
    fetchAlerts();
    fetchUserSubscription();
  }, [fetchAlerts]);

  const fetchUserSubscription = async () => {
    try {
      const response = await api.get('/subscriptions/user-subscription') as { subscription?: any; default_plan?: any };
      if (response.subscription) {
        setUserSubscription(response.subscription);
        // Obtener nombre del plan desde la suscripción (puede estar en plan.name o plan_name)
        let planName = 'freemium';
        if (response.subscription.plan && response.subscription.plan.name) {
          planName = response.subscription.plan.name;
        } else if (response.subscription.plan_name) {
          planName = response.subscription.plan_name;
        }
        console.log('📋 Plan detectado:', planName);
        setUserPlan(planName);
      } else if (response.default_plan) {
        const planName = response.default_plan.name || 'freemium';
        console.log('📋 Plan por defecto:', planName);
        setUserPlan(planName);
      } else {
        console.log('📋 Sin plan, usando freemium');
        setUserPlan('freemium');
      }
    } catch (err) {
      console.error('Error obteniendo suscripción:', err);
      setUserPlan('freemium');
    }
  };

  const buildEmotionsChart = () => {
    if (!data || !data.emotions_summary) return {};
    
    const emotions = Object.entries(data.emotions_summary)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 6);
    
    const emotionLabels: Record<string, string> = {
      'joy': 'Alegría',
      'anger': 'Enojo',
      'fear': 'Miedo',
      'sadness': 'Tristeza',
      'surprise': 'Sorpresa',
      'disgust': 'Disgusto'
    };
    
    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'value'
      },
      yAxis: {
        type: 'category',
        data: emotions.map(([emotion]) => emotionLabels[emotion] || emotion)
      },
      series: [
        {
          type: 'bar',
          data: emotions.map(([, value]) => Math.round(value * 100)),
          itemStyle: {
            color: (params: any) => {
              const colors = ['#10b981', '#ef4444', '#f59e0b', '#3b82f6', '#8b5cf6', '#ec4899'];
              return colors[params.dataIndex % colors.length];
            }
          },
          label: {
            show: true,
            position: 'right',
            formatter: '{c}%'
          }
        }
      ]
    };
  };

  const buildNewspaperComparisonChart = () => {
    if (!data || !data.by_newspaper) return {};
    
    const newspapers = Object.entries(data.by_newspaper)
      .sort((a, b) => b[1].total - a[1].total)
      .slice(0, 10);
    
    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        }
      },
      legend: {
        data: ['Positivo', 'Negativo', 'Neutral']
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: newspapers.map(([name]) => name),
        axisLabel: {
          rotate: 45,
          interval: 0
        }
      },
      yAxis: {
        type: 'value'
      },
      series: [
        {
          name: 'Positivo',
          type: 'bar',
          stack: 'sentiment',
          data: newspapers.map(([, data]) => data.positive),
          itemStyle: { color: '#10b981' }
        },
        {
          name: 'Neutral',
          type: 'bar',
          stack: 'sentiment',
          data: newspapers.map(([, data]) => data.neutral),
          itemStyle: { color: '#f59e0b' }
        },
        {
          name: 'Negativo',
          type: 'bar',
          stack: 'sentiment',
          data: newspapers.map(([, data]) => data.negative),
          itemStyle: { color: '#ef4444' }
        }
      ]
    };
  };

  const buildTopicComparisonChart = () => {
    if (!data || !data.topic_comparison) return {};
    
    const comparisons = Object.entries(data.topic_comparison);
    
    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        }
      },
      legend: {
        data: ['Score Promedio', '% Positivo', '% Negativo']
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: comparisons.map(([name]) => name)
      },
      yAxis: [
        {
          type: 'value',
          name: 'Score',
          min: -1,
          max: 1,
          position: 'left'
        },
        {
          type: 'value',
          name: 'Porcentaje',
          min: 0,
          max: 100,
          position: 'right'
        }
      ],
      series: [
        {
          name: 'Score Promedio',
          type: 'bar',
          yAxisIndex: 0,
          data: comparisons.map(([, data]) => data.average_score),
          itemStyle: {
            color: (params: any) => {
              const score = params.value;
              if (score > 0.1) return '#10b981';
              if (score < -0.1) return '#ef4444';
              return '#f59e0b';
            }
          }
        },
        {
          name: '% Positivo',
          type: 'line',
          yAxisIndex: 1,
          data: comparisons.map(([, data]) => data.positive_pct),
          itemStyle: { color: '#10b981' }
        },
        {
          name: '% Negativo',
          type: 'line',
          yAxisIndex: 1,
          data: comparisons.map(([, data]) => data.negative_pct),
          itemStyle: { color: '#ef4444' }
        }
      ]
    };
  };

  const getSentimentColor = (score: number) => {
    if (score > 0.1) return 'success';
    if (score < -0.1) return 'error';
    return 'warning';
  };

  const getSentimentIcon = (score: number) => {
    if (score > 0.1) return <SentimentSatisfied />;
    if (score < -0.1) return <SentimentDissatisfied />;
    return <SentimentNeutral />;
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Análisis de Sentimientos
        </Typography>
        <IconButton onClick={fetchSentimentData} color="primary">
          <Refresh />
        </IconButton>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Filtros */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, md: 3 }}>
              <FormControl fullWidth>
                <InputLabel>Días</InputLabel>
                <Select value={days} onChange={(e) => setDays(e.target.value as number)}>
                  <MenuItem value={7}>Últimos 7 días</MenuItem>
                  <MenuItem value={15}>Últimos 15 días</MenuItem>
                  <MenuItem value={30}>Últimos 30 días</MenuItem>
                  <MenuItem value={60}>Últimos 60 días</MenuItem>
                  <MenuItem value={90}>Últimos 90 días</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, md: 3 }}>
              <TextField
                fullWidth
                label="Categoría"
                value={categoryInput}
                onChange={(e) => setCategoryInput(e.target.value)}
                placeholder="Ej: Economía"
              />
            </Grid>
            <Grid size={{ xs: 12, md: 3 }}>
              <TextField
                fullWidth
                label="Periódico"
                value={newspaperInput}
                onChange={(e) => setNewspaperInput(e.target.value)}
                placeholder="Ej: El Comercio"
              />
            </Grid>
            <Grid size={{ xs: 12, md: 3 }}>
              <TextField
                fullWidth
                label="Tema específico"
                value={topicInput}
                onChange={(e) => setTopicInput(e.target.value)}
                placeholder="Ej: inflación"
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    setTopic(topicInput);
                    fetchSentimentData();
                  }
                }}
              />
            </Grid>
          </Grid>
          {(topic || topicInput) && (
            <Box sx={{ mt: 2 }}>
              <Button 
                variant="contained" 
                onClick={() => {
                  setTopic(topicInput);
                  fetchSentimentData();
                }} 
                startIcon={<CompareArrows />}
              >
                Comparar Medios sobre este Tema
              </Button>
            </Box>
          )}
        </CardContent>
      </Card>

      {data && (
        <>
          {/* Interpretación y Descripción */}
          <Card sx={{ mb: 3, bgcolor: 'info.light', color: 'info.contrastText' }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <EmojiEmotions sx={{ mr: 1, fontSize: 28 }} />
                <Typography variant="h6" fontWeight="bold">
                  📊 Interpretación de los Resultados
                </Typography>
              </Box>
              <Typography variant="body2" paragraph>
                <strong>¿Qué significan estos datos?</strong>
              </Typography>
              <Box component="ul" sx={{ pl: 3, mb: 2 }}>
                <li>
                  <strong>Score Promedio:</strong> Un valor entre -1 (muy negativo) y +1 (muy positivo). 
                  Valores cercanos a 0 indican neutralidad. Un score positivo indica tendencia optimista, 
                  mientras que negativo sugiere preocupación o crítica.
                </li>
                <li>
                  <strong>Polarización:</strong> Mide qué tan extremas son las opiniones. 
                  Alta polarización indica opiniones muy divididas (muchos muy positivos y muchos muy negativos), 
                  mientras que baja polarización sugiere consenso o neutralidad general.
                </li>
                <li>
                  <strong>Evolución Temporal:</strong> Observa cómo cambia el sentimiento a lo largo del tiempo. 
                  Una tendencia ascendente en positivo indica mejoría en la percepción, mientras que una 
                  tendencia descendente sugiere empeoramiento.
                </li>
                <li>
                  <strong>Comparación entre Medios:</strong> Permite identificar si diferentes fuentes de noticias 
                  tienen enfoques distintos sobre el mismo tema, lo que puede revelar sesgos o perspectivas diferentes.
                </li>
              </Box>
              <Alert severity="info" sx={{ mt: 2 }}>
                <Typography variant="body2">
                  <strong>💡 Consejo:</strong> Estos análisis son herramientas de apoyo. Combínalos con contexto 
                  y conocimiento del tema para tomar decisiones informadas. Los sentimientos pueden variar según 
                  el momento, el tema y la fuente.
                </Typography>
              </Alert>
            </CardContent>
          </Card>

          {/* Métricas principales */}
          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid size={{ xs: 12, md: 3 }}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" mb={1}>
                    <SentimentSatisfied color="success" sx={{ mr: 1 }} />
                    <Typography variant="h6">Positivo</Typography>
                  </Box>
                  <Typography variant="h4">{data.positive}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {((data.positive / data.total) * 100).toFixed(1)}% del total
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid size={{ xs: 12, md: 3 }}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" mb={1}>
                    <SentimentNeutral color="warning" sx={{ mr: 1 }} />
                    <Typography variant="h6">Neutral</Typography>
                  </Box>
                  <Typography variant="h4">{data.neutral}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {((data.neutral / data.total) * 100).toFixed(1)}% del total
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid size={{ xs: 12, md: 3 }}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" mb={1}>
                    <SentimentDissatisfied color="error" sx={{ mr: 1 }} />
                    <Typography variant="h6">Negativo</Typography>
                  </Box>
                  <Typography variant="h4">{data.negative}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {((data.negative / data.total) * 100).toFixed(1)}% del total
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid size={{ xs: 12, md: 3 }}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" mb={1}>
                    {getSentimentIcon(data.average_score)}
                    <Typography variant="h6" sx={{ ml: 1 }}>Score Promedio</Typography>
                  </Box>
                  <Typography variant="h4" color={`${getSentimentColor(data.average_score)}.main`}>
                    {data.average_score.toFixed(3)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total: {data.total} artículos
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Alertas de Sentimiento Negativo */}
          {canAccessAlerts && alerts.length > 0 && (
            <Card sx={{ mb: 3, bgcolor: 'error.light', color: 'error.contrastText' }}>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <SentimentDissatisfied sx={{ mr: 1, fontSize: 28 }} />
                  <Typography variant="h6" fontWeight="bold">
                    ⚠️ Alertas: Sentimiento Negativo en Comentarios Virales
                  </Typography>
                </Box>
                <Typography variant="body2" paragraph>
                  Los siguientes temas tienen un alto porcentaje de comentarios negativos:
                </Typography>
                {alerts.map((alert, idx) => (
                  <Alert 
                    key={idx} 
                    severity={alert.severity === 'high' ? 'error' : 'warning'} 
                    sx={{ mb: 1 }}
                  >
                    <Typography variant="subtitle2" fontWeight="bold">
                      {alert.topic}
                    </Typography>
                    <Typography variant="body2">
                      <strong>{alert.negative_percentage.toFixed(1)}%</strong> de comentarios negativos 
                      ({alert.negative_count} de {alert.total_comments} comentarios)
                      {' • '}
                      Score promedio: <strong>{alert.average_score.toFixed(3)}</strong>
                    </Typography>
                  </Alert>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Mensaje de upgrade para funcionalidades avanzadas */}
          {!canAccessViralComparison && data && (
            <Card sx={{ mb: 3, bgcolor: 'info.light' }}>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <TrendingUp sx={{ mr: 1, fontSize: 28 }} />
                  <Typography variant="h6" fontWeight="bold">
                    💎 Funcionalidad Premium Disponible
                  </Typography>
                </Box>
                <Typography variant="body2" paragraph>
                  La comparación de sentimientos entre noticias y comentarios virales está disponible 
                  para planes Premium y Enterprise. Actualiza tu plan para acceder a esta funcionalidad avanzada.
                </Typography>
                <Button 
                  variant="contained" 
                  color="primary"
                  href="/subscriptions"
                  sx={{ mt: 1 }}
                >
                  Ver Planes y Precios
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Tabs */}
          <Paper sx={{ mb: 3 }}>
            <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
              <Tab icon={<Timeline />} label="Evolución Temporal" />
              <Tab icon={<Newspaper />} label="Por Periódico" />
              <Tab icon={<Category />} label="Por Categoría" />
              <Tab icon={<EmojiEmotions />} label="Emociones" />
              {shouldShowViralTab && (
                <Tab 
                  icon={<CompareArrows />} 
                  label="Noticias vs Comentarios"
                />
              )}
              {topic && data.topic_comparison && (
                <Tab icon={<CompareArrows />} label="Comparación de Medios" />
              )}
            </Tabs>
          </Paper>

          {/* Contenido de tabs */}
          {tabValue === 0 && (
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 6 }}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Distribución de Sentimientos
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Este gráfico muestra la proporción de noticias positivas, negativas y neutrales. 
                      Un equilibrio entre positivo y negativo puede indicar cobertura balanceada, mientras que 
                      un predominio de uno sobre otro sugiere una tendencia clara en el tema analizado.
                    </Typography>
                    <ReactECharts option={buildSentimentDonutChart()} style={{ height: '400px' }} />
                  </CardContent>
                </Card>
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Polarización
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      La polarización mide qué tan extremas son las opiniones. Alta polarización significa 
                      opiniones muy divididas (muchos muy a favor y muchos muy en contra), media indica 
                      cierto desacuerdo, y baja sugiere consenso o neutralidad general.
                    </Typography>
                    <Box sx={{ mt: 2 }}>
                      <Box sx={{ mb: 2 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography>Alta</Typography>
                          <Typography>{data.polarization_distribution.high}</Typography>
                        </Box>
                        <LinearProgress 
                          variant="determinate" 
                          value={(data.polarization_distribution.high / data.total) * 100}
                          color="error"
                        />
                      </Box>
                      <Box sx={{ mb: 2 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography>Media</Typography>
                          <Typography>{data.polarization_distribution.medium}</Typography>
                        </Box>
                        <LinearProgress 
                          variant="determinate" 
                          value={(data.polarization_distribution.medium / data.total) * 100}
                          color="warning"
                        />
                      </Box>
                      <Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography>Baja</Typography>
                          <Typography>{data.polarization_distribution.low}</Typography>
                        </Box>
                        <LinearProgress 
                          variant="determinate" 
                          value={(data.polarization_distribution.low / data.total) * 100}
                          color="success"
                        />
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
              <Grid size={{ xs: 12 }}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Evolución del Sentimiento en el Tiempo
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Este gráfico muestra cómo cambia el sentimiento día a día. Observa las tendencias: 
                      si la línea azul (Score Promedio) sube, el sentimiento general mejora; si baja, empeora. 
                      Las líneas de colores muestran la cantidad de noticias positivas (verde), negativas (rojo) 
                      y neutrales (naranja) por día. Esto te ayuda a identificar momentos clave de cambio en 
                      la percepción pública.
                    </Typography>
                    <ReactECharts option={buildTimelineChart()} style={{ height: '400px' }} />
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}

          {tabValue === 1 && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Comparación por Periódico
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Compara cómo diferentes medios de comunicación cubren las noticias. Esto puede revelar 
                  sesgos editoriales o enfoques distintos. Un medio con más noticias positivas puede tener 
                  una perspectiva más optimista, mientras que uno con más negativas puede ser más crítico 
                  o enfocarse en problemas.
                </Typography>
                <ReactECharts option={buildNewspaperComparisonChart()} style={{ height: '500px' }} />
                <TableContainer sx={{ mt: 3 }}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Periódico</TableCell>
                        <TableCell align="right">Total</TableCell>
                        <TableCell align="right">Positivo</TableCell>
                        <TableCell align="right">Neutral</TableCell>
                        <TableCell align="right">Negativo</TableCell>
                        <TableCell align="right">Score Promedio</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {Object.entries(data.by_newspaper)
                        .sort((a, b) => b[1].total - a[1].total)
                        .map(([name, npData]) => (
                          <TableRow key={name}>
                            <TableCell>{name}</TableCell>
                            <TableCell align="right">{npData.total}</TableCell>
                            <TableCell align="right">{npData.positive}</TableCell>
                            <TableCell align="right">{npData.neutral}</TableCell>
                            <TableCell align="right">{npData.negative}</TableCell>
                            <TableCell align="right">
                              <Chip
                                label={npData.average_score.toFixed(3)}
                                color={getSentimentColor(npData.average_score)}
                                size="small"
                              />
                            </TableCell>
                          </TableRow>
                        ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          )}

          {tabValue === 2 && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Comparación por Categoría
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Analiza qué categorías de noticias tienen sentimientos más positivos o negativos. 
                  Por ejemplo, noticias de tecnología suelen ser más positivas, mientras que noticias 
                  de política pueden ser más polarizadas. Esto te ayuda a entender qué temas generan 
                  más optimismo o preocupación.
                </Typography>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Categoría</TableCell>
                        <TableCell align="right">Total</TableCell>
                        <TableCell align="right">Positivo</TableCell>
                        <TableCell align="right">Neutral</TableCell>
                        <TableCell align="right">Negativo</TableCell>
                        <TableCell align="right">Score Promedio</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {Object.entries(data.by_category)
                        .sort((a, b) => b[1].total - a[1].total)
                        .map(([cat, catData]) => (
                          <TableRow key={cat}>
                            <TableCell>{cat}</TableCell>
                            <TableCell align="right">{catData.total}</TableCell>
                            <TableCell align="right">{catData.positive}</TableCell>
                            <TableCell align="right">{catData.neutral}</TableCell>
                            <TableCell align="right">{catData.negative}</TableCell>
                            <TableCell align="right">
                              <Chip
                                label={catData.average_score.toFixed(3)}
                                color={getSentimentColor(catData.average_score)}
                                size="small"
                              />
                            </TableCell>
                          </TableRow>
                        ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          )}

          {tabValue === 3 && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Emociones Detectadas
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Identifica las emociones predominantes en las noticias: Alegría (noticias positivas y 
                  esperanzadoras), Enojo (críticas y frustraciones), Miedo (preocupaciones y alertas), 
                  Tristeza (pérdidas y problemas), Sorpresa (eventos inesperados) y Disgusto (rechazo). 
                  Esto te ayuda a entender el tono emocional general de las noticias.
                </Typography>
                <ReactECharts option={buildEmotionsChart()} style={{ height: '400px' }} />
                {Object.keys(data.emotions_summary).length === 0 && (
                  <Alert severity="info" sx={{ mt: 2 }}>
                    No se detectaron emociones en los artículos analizados
                  </Alert>
                )}
              </CardContent>
            </Card>
          )}

          {tabValue === viralComparisonTabIndex && shouldShowViralTab && (
            <Grid container spacing={3}>
              <Grid size={{ xs: 12 }}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Comparación: Noticias vs Comentarios Virales
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Esta comparación muestra la diferencia entre el sentimiento de las noticias y las opiniones 
                      de los usuarios en comentarios virales. Si hay una gran diferencia, puede indicar que las 
                      noticias no reflejan completamente la opinión pública, o viceversa. Observa si los comentarios 
                      son más positivos o negativos que las noticias sobre el mismo tema.
                    </Typography>
                    <ReactECharts option={buildComparisonChart()} style={{ height: '400px' }} />
                  </CardContent>
                </Card>
              </Grid>
              <Grid size={{ xs: 12 }}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Comparación de Scores Promedio
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Compara el score promedio de sentimiento entre noticias y comentarios virales. 
                      Un score más alto indica sentimiento más positivo. Si los comentarios tienen un score 
                      significativamente más bajo que las noticias, puede indicar descontento público.
                    </Typography>
                    <ReactECharts option={buildScoreComparisonChart()} style={{ height: '300px' }} />
                    {data.viral_comments_comparison && (
                      <Box sx={{ mt: 3, display: 'flex', gap: 2, justifyContent: 'center' }}>
                        <Chip 
                          label={`Noticias: ${data.average_score.toFixed(3)}`} 
                          color={getSentimentColor(data.average_score)}
                          sx={{ fontSize: '1rem', padding: '8px 16px' }}
                        />
                        <Chip 
                          label={`Comentarios: ${data.viral_comments_comparison.average_score.toFixed(3)}`} 
                          color={getSentimentColor(data.viral_comments_comparison.average_score)}
                          sx={{ fontSize: '1rem', padding: '8px 16px' }}
                        />
                      </Box>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}

          {tabValue === topicComparisonTabIndex && topic && data.topic_comparison && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Comparación de Medios: "{topic}"
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Esta comparación muestra cómo diferentes medios cubren el mismo tema específico. 
                  Observa las diferencias en el score promedio y los porcentajes de positivo/negativo. 
                  Grandes diferencias pueden indicar sesgos editoriales o enfoques distintos. Un medio 
                  con score más alto tiende a ser más optimista sobre el tema, mientras que uno con 
                  score más bajo puede ser más crítico.
                </Typography>
                <ReactECharts option={buildTopicComparisonChart()} style={{ height: '400px' }} />
                <TableContainer sx={{ mt: 3 }}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Periódico</TableCell>
                        <TableCell align="right">Artículos</TableCell>
                        <TableCell align="right">% Positivo</TableCell>
                        <TableCell align="right">% Negativo</TableCell>
                        <TableCell align="right">Score Promedio</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {Object.entries(data.topic_comparison)
                        .sort((a, b) => b[1].total - a[1].total)
                        .map(([name, compData]) => (
                          <TableRow key={name}>
                            <TableCell>{name}</TableCell>
                            <TableCell align="right">{compData.total}</TableCell>
                            <TableCell align="right">
                              <Chip label={`${compData.positive_pct}%`} color="success" size="small" />
                            </TableCell>
                            <TableCell align="right">
                              <Chip label={`${compData.negative_pct}%`} color="error" size="small" />
                            </TableCell>
                            <TableCell align="right">
                              <Chip
                                label={compData.average_score.toFixed(3)}
                                color={getSentimentColor(compData.average_score)}
                                size="small"
                              />
                            </TableCell>
                          </TableRow>
                        ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </Box>
  );
};

export default SentimentAnalysis;


