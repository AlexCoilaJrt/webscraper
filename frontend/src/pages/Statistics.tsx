import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  LinearProgress,
  Alert,
  Button,
  Avatar,
  Fade,
  Zoom,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tabs,
  Tab,
} from '@mui/material';
import {
  TrendingUp as TrendingIcon,
  Article as ArticleIcon,
  Image as ImageIcon,
  Newspaper as NewspaperIcon,
  Category as CategoryIcon,
  Timeline as TimelineIcon,
  BarChart as BarChartIcon,
  PieChart as PieChartIcon,
  Refresh as RefreshIcon,
  Speed as SpeedIcon,
  Storage as StorageIcon,
  Public as PublicIcon,
} from '@mui/icons-material';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement,
} from 'chart.js';
import { Bar, Pie, Line } from 'react-chartjs-2';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import { apiService, Statistics as StatisticsType } from '../services/api';

// Registrar componentes de Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  ChartTooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement
);

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`stats-tabpanel-${index}`}
      aria-labelledby={`stats-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const Statistics: React.FC = () => {
  const [statistics, setStatistics] = useState<StatisticsType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [timeRange, setTimeRange] = useState('7d');

  const loadStatistics = async () => {
    try {
      setLoading(true);
      const stats = await apiService.getStatistics();
      setStatistics(stats);
      setError(null);
    } catch (err) {
      setError('Error cargando estadísticas');
      console.error('Error loading statistics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStatistics();
  }, []);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleTimeRangeChange = (event: any) => {
    setTimeRange(event.target.value);
  };

  // Configuración de colores para gráficos
  const colors = {
    primary: '#1976d2',
    secondary: '#42a5f5',
    success: '#4caf50',
    warning: '#ff9800',
    error: '#f44336',
    info: '#00bcd4',
    purple: '#9c27b0',
    pink: '#e91e63',
  };

  // Datos para gráfico de barras - Artículos por categoría
  const categoryChartData = {
    labels: statistics?.categories?.map(cat => cat.category) || [],
    datasets: [
      {
        label: 'Artículos',
        data: statistics?.categories?.map(cat => cat.articles_count) || [],
        backgroundColor: [
          colors.primary,
          colors.secondary,
          colors.success,
          colors.warning,
          colors.error,
          colors.info,
          colors.purple,
          colors.pink,
        ],
        borderColor: [
          colors.primary,
          colors.secondary,
          colors.success,
          colors.warning,
          colors.error,
          colors.info,
          colors.purple,
          colors.pink,
        ],
        borderWidth: 2,
        borderRadius: 8,
        borderSkipped: false,
      },
    ],
  };

  // Datos para gráfico de pastel - Distribución de periódicos
  const newspaperChartData = {
    labels: statistics?.newspapers?.map(news => news.newspaper) || [],
    datasets: [
      {
        data: statistics?.newspapers?.map(news => news.articles_count) || [],
        backgroundColor: [
          colors.primary,
          colors.secondary,
          colors.success,
          colors.warning,
          colors.error,
          colors.info,
          colors.purple,
          colors.pink,
        ],
        borderColor: '#ffffff',
        borderWidth: 3,
        hoverOffset: 10,
      },
    ],
  };

  // Datos para gráfico de líneas - Tendencias temporales (datos de ejemplo)
  const timelineChartData = {
    labels: ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'],
    datasets: [
      {
        label: 'Artículos',
        data: [12, 19, 8, 15, 22, 18, 25],
        borderColor: colors.primary,
        backgroundColor: `${colors.primary}20`,
        borderWidth: 3,
        fill: true,
        tension: 0.4,
        pointBackgroundColor: colors.primary,
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
        pointRadius: 6,
      },
      {
        label: 'Imágenes',
        data: [8, 15, 12, 10, 18, 14, 20],
        borderColor: colors.secondary,
        backgroundColor: `${colors.secondary}20`,
        borderWidth: 3,
        fill: true,
        tension: 0.4,
        pointBackgroundColor: colors.secondary,
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
        pointRadius: 6,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          usePointStyle: true,
          padding: 20,
          font: {
            size: 12,
            weight: 'bold' as const,
          },
        },
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#ffffff',
        bodyColor: '#ffffff',
        borderColor: colors.primary,
        borderWidth: 1,
        cornerRadius: 8,
        displayColors: true,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(0, 0, 0, 0.1)',
        },
        ticks: {
          font: {
            size: 11,
          },
        },
      },
      x: {
        grid: {
          color: 'rgba(0, 0, 0, 0.1)',
        },
        ticks: {
          font: {
            size: 11,
          },
        },
      },
    },
  };

  const pieChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
        labels: {
          usePointStyle: true,
          padding: 15,
          font: {
            size: 11,
            weight: 'bold' as const,
          },
        },
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#ffffff',
        bodyColor: '#ffffff',
        borderColor: colors.primary,
        borderWidth: 1,
        cornerRadius: 8,
        callbacks: {
          label: function(context: any) {
            const label = context.label || '';
            const value = context.parsed;
            const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0);
            const percentage = ((value / total) * 100).toFixed(1);
            return `${label}: ${value} (${percentage}%)`;
          },
        },
      },
    },
  };

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 8 }}>
          <LinearProgress sx={{ width: '100%', maxWidth: 400 }} />
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Alert severity="error" sx={{ mb: 4, borderRadius: 2 }}>
          {error}
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Fade in timeout={800}>
        <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography
              variant="h3"
              component="h1"
              gutterBottom
              sx={{
                fontWeight: 700,
                background: 'linear-gradient(45deg, #1976d2, #42a5f5)',
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              📊 Estadísticas del Scraper
            </Typography>
            <Typography variant="h6" color="text.secondary">
              Análisis completo de rendimiento y datos extraídos
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Período</InputLabel>
              <Select
                value={timeRange}
                onChange={handleTimeRangeChange}
                label="Período"
              >
                <MenuItem value="1d">Último día</MenuItem>
                <MenuItem value="7d">Última semana</MenuItem>
                <MenuItem value="30d">Último mes</MenuItem>
                <MenuItem value="90d">Últimos 3 meses</MenuItem>
              </Select>
            </FormControl>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={loadStatistics}
              sx={{ borderRadius: 2 }}
            >
              Actualizar
            </Button>
          </Box>
        </Box>
      </Fade>

      {/* Métricas Principales */}
      <Fade in timeout={1000}>
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Zoom in timeout={1200}>
              <Card
                sx={{
                  height: '100%',
                  background: 'linear-gradient(135deg, #1976d2 0%, #42a5f5 100%)',
                  color: 'white',
                  position: 'relative',
                  overflow: 'hidden',
                }}
              >
                <CardContent sx={{ position: 'relative', zIndex: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)', mr: 2 }}>
                      <ArticleIcon />
                    </Avatar>
                    <Box>
                      <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                        {statistics?.general?.total_articles || 0}
                      </Typography>
                      <Typography variant="body2" sx={{ opacity: 0.9 }}>
                        Total Artículos
                      </Typography>
                    </Box>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <TrendingIcon sx={{ mr: 1, fontSize: 20 }} />
                    <Typography variant="body2" sx={{ opacity: 0.9 }}>
                      +12% vs mes anterior
                    </Typography>
                  </Box>
                </CardContent>
                <Box
                  sx={{
                    position: 'absolute',
                    top: -20,
                    right: -20,
                    width: 100,
                    height: 100,
                    borderRadius: '50%',
                    background: 'rgba(255,255,255,0.1)',
                    zIndex: 1,
                  }}
                />
              </Card>
            </Zoom>
          </Grid>

          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Zoom in timeout={1400}>
              <Card
                sx={{
                  height: '100%',
                  background: 'linear-gradient(135deg, #4caf50 0%, #8bc34a 100%)',
                  color: 'white',
                  position: 'relative',
                  overflow: 'hidden',
                }}
              >
                <CardContent sx={{ position: 'relative', zIndex: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)', mr: 2 }}>
                      <ImageIcon />
                    </Avatar>
                    <Box>
                      <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                        {statistics?.general?.total_images_downloaded || 0}
                      </Typography>
                      <Typography variant="body2" sx={{ opacity: 0.9 }}>
                        Imágenes Descargadas
                      </Typography>
                    </Box>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <TrendingIcon sx={{ mr: 1, fontSize: 20 }} />
                    <Typography variant="body2" sx={{ opacity: 0.9 }}>
                      +8% vs mes anterior
                    </Typography>
                  </Box>
                </CardContent>
                <Box
                  sx={{
                    position: 'absolute',
                    top: -20,
                    right: -20,
                    width: 100,
                    height: 100,
                    borderRadius: '50%',
                    background: 'rgba(255,255,255,0.1)',
                    zIndex: 1,
                  }}
                />
              </Card>
            </Zoom>
          </Grid>

          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Zoom in timeout={1600}>
              <Card
                sx={{
                  height: '100%',
                  background: 'linear-gradient(135deg, #ff9800 0%, #ffc107 100%)',
                  color: 'white',
                  position: 'relative',
                  overflow: 'hidden',
                }}
              >
                <CardContent sx={{ position: 'relative', zIndex: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)', mr: 2 }}>
                      <NewspaperIcon />
                    </Avatar>
                    <Box>
                      <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                        {statistics?.general?.total_newspapers || 0}
                      </Typography>
                      <Typography variant="body2" sx={{ opacity: 0.9 }}>
                        Periódicos Únicos
                      </Typography>
                    </Box>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <PublicIcon sx={{ mr: 1, fontSize: 20 }} />
                    <Typography variant="body2" sx={{ opacity: 0.9 }}>
                      Fuentes activas
                    </Typography>
                  </Box>
                </CardContent>
                <Box
                  sx={{
                    position: 'absolute',
                    top: -20,
                    right: -20,
                    width: 100,
                    height: 100,
                    borderRadius: '50%',
                    background: 'rgba(255,255,255,0.1)',
                    zIndex: 1,
                  }}
                />
              </Card>
            </Zoom>
          </Grid>

          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Zoom in timeout={1800}>
              <Card
                sx={{
                  height: '100%',
                  background: 'linear-gradient(135deg, #9c27b0 0%, #e91e63 100%)',
                  color: 'white',
                  position: 'relative',
                  overflow: 'hidden',
                }}
              >
                <CardContent sx={{ position: 'relative', zIndex: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)', mr: 2 }}>
                      <CategoryIcon />
                    </Avatar>
                    <Box>
                      <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                        {statistics?.general?.total_categories || 0}
                      </Typography>
                      <Typography variant="body2" sx={{ opacity: 0.9 }}>
                        Categorías Únicas
                      </Typography>
                    </Box>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <TrendingIcon sx={{ mr: 1, fontSize: 20 }} />
                    <Typography variant="body2" sx={{ opacity: 0.9 }}>
                      +15% vs mes anterior
                    </Typography>
                  </Box>
                </CardContent>
                <Box
                  sx={{
                    position: 'absolute',
                    top: -20,
                    right: -20,
                    width: 100,
                    height: 100,
                    borderRadius: '50%',
                    background: 'rgba(255,255,255,0.1)',
                    zIndex: 1,
                  }}
                />
              </Card>
            </Zoom>
          </Grid>
        </Grid>
      </Fade>

      {/* Tabs de Análisis */}
      <Fade in timeout={2000}>
        <Paper sx={{ borderRadius: 3, overflow: 'hidden', boxShadow: 3 }}>
          <Tabs
            value={tabValue}
            onChange={handleTabChange}
            sx={{
              borderBottom: 1,
              borderColor: 'divider',
              bgcolor: 'grey.50',
              '& .MuiTab-root': {
                textTransform: 'none',
                fontWeight: 600,
                minHeight: 60,
              },
            }}
          >
            <Tab
              icon={<BarChartIcon />}
              label="Análisis por Categorías"
              iconPosition="start"
            />
            <Tab
              icon={<PieChartIcon />}
              label="Distribución de Periódicos"
              iconPosition="start"
            />
            <Tab
              icon={<TimelineIcon />}
              label="Tendencias Temporales"
              iconPosition="start"
            />
            <Tab
              icon={<StorageIcon />}
              label="Detalles de Sesiones"
              iconPosition="start"
            />
          </Tabs>

          <TabPanel value={tabValue} index={0}>
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 8 }}>
                <Card sx={{ height: 400 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                      <BarChartIcon sx={{ mr: 1 }} />
                      Artículos por Categoría
                    </Typography>
                    <Box sx={{ height: 300, mt: 2 }}>
                      <Bar data={categoryChartData} options={chartOptions} />
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
              <Grid size={{ xs: 12, md: 4 }}>
                <Card sx={{ height: 400 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Top Categorías
                    </Typography>
                    <Box sx={{ mt: 2 }}>
                      {statistics?.categories?.slice(0, 5).map((category, index) => (
                        <Box key={category.category} sx={{ mb: 2 }}>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                            <Typography variant="body2" sx={{ fontWeight: 600 }}>
                              {category.category}
                            </Typography>
                            <Typography variant="body2" color="primary" sx={{ fontWeight: 600 }}>
                              {category.articles_count}
                            </Typography>
                          </Box>
                          <LinearProgress
                            variant="determinate"
                            value={(category.articles_count / (statistics?.categories?.[0]?.articles_count || 1)) * 100}
                            sx={{
                              height: 8,
                              borderRadius: 4,
                              bgcolor: 'grey.200',
                              '& .MuiLinearProgress-bar': {
                                borderRadius: 4,
                                background: `linear-gradient(90deg, ${colors.primary}, ${colors.secondary})`,
                              },
                            }}
                          />
                        </Box>
                      ))}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 6 }}>
                <Card sx={{ height: 400 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                      <PieChartIcon sx={{ mr: 1 }} />
                      Distribución de Periódicos
                    </Typography>
                    <Box sx={{ height: 300, mt: 2 }}>
                      <Pie data={newspaperChartData} options={pieChartOptions} />
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <Card sx={{ height: 400 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Periódicos Más Activos
                    </Typography>
                    <TableContainer>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Periódico</TableCell>
                            <TableCell align="right">Artículos</TableCell>
                            <TableCell align="right">Imágenes</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {statistics?.newspapers?.map((newspaper) => (
                            <TableRow key={newspaper.newspaper}>
                              <TableCell>
                                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                  <Avatar sx={{ width: 24, height: 24, mr: 1, bgcolor: colors.primary }}>
                                    <NewspaperIcon sx={{ fontSize: 16 }} />
                                  </Avatar>
                                  {newspaper.newspaper}
                                </Box>
                              </TableCell>
                              <TableCell align="right">
                                <Chip
                                  label={newspaper.articles_count}
                                  size="small"
                                  color="primary"
                                  variant="outlined"
                                />
                              </TableCell>
                              <TableCell align="right">
                                <Chip
                                  label={newspaper.images_count || 0}
                                  size="small"
                                  color="secondary"
                                  variant="outlined"
                                />
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            <Card sx={{ height: 500 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                  <TimelineIcon sx={{ mr: 1 }} />
                  Tendencias de Extracción
                </Typography>
                <Box sx={{ height: 400, mt: 2 }}>
                  <Line data={timelineChartData} options={chartOptions} />
                </Box>
              </CardContent>
            </Card>
          </TabPanel>

          <TabPanel value={tabValue} index={3}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                  <StorageIcon sx={{ mr: 1 }} />
                  Sesiones de Scraping Recientes
                </Typography>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Fecha</TableCell>
                        <TableCell>URL</TableCell>
                        <TableCell>Método</TableCell>
                        <TableCell align="right">Artículos</TableCell>
                        <TableCell align="right">Imágenes</TableCell>
                        <TableCell align="right">Duración</TableCell>
                        <TableCell align="right">Estado</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {[
                        {
                          start_time: new Date().toISOString(),
                          url: 'https://diariosinfronteras.com.pe/category/policiales/',
                          method: 'hybrid',
                          articles_found: 17,
                          images_downloaded: 17,
                          duration_seconds: 4,
                          status: 'completed'
                        },
                        {
                          start_time: new Date(Date.now() - 3600000).toISOString(),
                          url: 'https://diariosinfronteras.com.pe/category/policiales/',
                          method: 'optimized',
                          articles_found: 25,
                          images_downloaded: 0,
                          duration_seconds: 9,
                          status: 'completed'
                        }
                      ].map((session: any, index: number) => (
                        <TableRow key={index}>
                          <TableCell>
                            <Box>
                              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                                {format(new Date(session.start_time), 'dd MMM yyyy', { locale: es })}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {format(new Date(session.start_time), 'HH:mm:ss', { locale: es })}
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Tooltip title={session.url}>
                              <Typography
                                variant="body2"
                                sx={{
                                  maxWidth: 200,
                                  overflow: 'hidden',
                                  textOverflow: 'ellipsis',
                                  whiteSpace: 'nowrap',
                                }}
                              >
                                {session.url}
                              </Typography>
                            </Tooltip>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={session.method}
                              size="small"
                              color={session.method === 'hybrid' ? 'primary' : 'default'}
                              variant="outlined"
                            />
                          </TableCell>
                          <TableCell align="right">
                            <Chip
                              label={session.articles_found}
                              size="small"
                              color="primary"
                              variant="outlined"
                            />
                          </TableCell>
                          <TableCell align="right">
                            <Chip
                              label={session.images_downloaded}
                              size="small"
                              color="secondary"
                              variant="outlined"
                            />
                          </TableCell>
                          <TableCell align="right">
                            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                              <SpeedIcon sx={{ mr: 0.5, fontSize: 16 }} />
                              {session.duration_seconds}s
                            </Box>
                          </TableCell>
                          <TableCell align="right">
                            <Chip
                              label={session.status}
                              size="small"
                              color={session.status === 'completed' ? 'success' : 'warning'}
                              variant="filled"
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </TabPanel>
        </Paper>
      </Fade>
    </Container>
  );
};

export default Statistics;