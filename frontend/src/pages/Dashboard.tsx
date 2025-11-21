import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  Alert,
  Button,
  Container,
  Avatar,
  Fade,
  Zoom,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
} from '@mui/material';
import {
  Article as ArticleIcon,
  Image as ImageIcon,
  Newspaper as NewspaperIcon,
  Category as CategoryIcon,
  PlayArrow as PlayIcon,
  TrendingUp as TrendingIcon,
  Dashboard as DashboardIcon,
  DeleteForever as DeleteIcon,
  Web as WebIcon,
  Analytics as AnalyticsIcon,
  Storage as StorageIcon,
  Public as PublicIcon,
  CheckCircle as CheckCircleIcon,
  Star as StarIcon,
  CardMembership as CardMembershipIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { apiService, Statistics, ScrapingStatus, Newspaper } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import ChatbotWidget from '../components/ChatbotWidget';
import AdsCarousel from '../components/AdsCarousel';
import ViralComments from '../components/ViralComments';
import { api } from '../services/api';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { isAdmin, hasPermission, refreshPermissions } = useAuth();
  const [statistics, setStatistics] = useState<Statistics | null>(null);
  const [scrapingStatus, setScrapingStatus] = useState<ScrapingStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [clearDialogOpen, setClearDialogOpen] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [newspapers, setNewspapers] = useState<Newspaper[]>([]);
  const [newspapersLoading, setNewspapersLoading] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedNewspaper, setSelectedNewspaper] = useState<Newspaper | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [isAutoUpdating, setIsAutoUpdating] = useState(false);
  const [userSubscription, setUserSubscription] = useState<any>(null);

  const loadUserSubscription = async () => {
    try {
      const response = await api.get('/subscriptions/user-subscription');
      if (response.data && (response.data as any).subscription) {
        setUserSubscription((response.data as any).subscription);
      } else if (response.data && (response.data as any).default_plan) {
        // Si no hay suscripción activa, usar plan freemium por defecto
        setUserSubscription({
          plan_name: 'freemium',
          plan_display_name: 'Plan Gratuito',
          features: (response.data as any).default_plan.features || []
        });
      }
    } catch (err) {
      console.error('Error loading subscription:', err);
    }
  };

  const hasAutoUpdateAccess = () => {
    // Admin siempre tiene acceso
    if (isAdmin) return true;
    // Usuarios con plan Premium o Enterprise tienen acceso
    if (userSubscription) {
      const planName = userSubscription.plan_name?.toLowerCase() || '';
      return planName === 'premium' || planName === 'enterprise';
    }
    return false;
  };

  useEffect(() => {
    loadDashboardData();
    loadNewspapers();
    loadUserSubscription();
    // Refrescar permisos al cargar el Dashboard
    refreshPermissions();
    
    // Poll for scraping status updates (solo si es admin)
    if (isAdmin) {
    const interval = setInterval(loadScrapingStatus, 2000);
    return () => clearInterval(interval);
    }
  }, [isAdmin]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      // Cargar estadísticas siempre
      const statsData = await apiService.getStatistics();
      setStatistics(statsData);
      
      // Solo cargar status si es admin
      if (isAdmin) {
        try {
          const statusData = await apiService.getStatus();
      setScrapingStatus(statusData);
        } catch (err) {
          console.error('Error loading scraping status:', err);
        }
      }
      
      setError(null);
    } catch (err) {
      setError('Error cargando datos del dashboard');
      console.error('Dashboard error:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadScrapingStatus = async () => {
    if (!isAdmin) return; // Solo admin puede ver el estado
    try {
      const statusData = await apiService.getStatus();
      setScrapingStatus(statusData);
    } catch (err) {
      console.error('Error loading scraping status:', err);
    }
  };

  const loadNewspapers = async () => {
    try {
      setNewspapersLoading(true);
      const response = await apiService.getNewspapers();
      setNewspapers(response.newspapers);
    } catch (err) {
      console.error('Error loading newspapers:', err);
    } finally {
      setNewspapersLoading(false);
    }
  };

  const handleDeleteNewspaper = (newspaper: Newspaper) => {
    setSelectedNewspaper(newspaper);
    setDeleteDialogOpen(true);
  };

  const confirmDeleteNewspaper = async () => {
    if (!selectedNewspaper) return;
    
    setDeleting(true);
    try {
      const result = await apiService.deleteNewspaper(selectedNewspaper.newspaper);
      console.log('Periódico eliminado:', result);
      
      // Recargar datos
      await loadDashboardData();
      await loadNewspapers();
      
      setDeleteDialogOpen(false);
      setSelectedNewspaper(null);
      
      alert(`✅ Datos del periódico "${selectedNewspaper.newspaper}" eliminados exitosamente:\n- ${result.deleted.articles} artículos\n- ${result.deleted.images} imágenes\n- ${result.deleted.files} archivos`);
    } catch (err) {
      console.error('Error eliminando periódico:', err);
      alert('❌ Error al eliminar los datos del periódico. Inténtalo de nuevo.');
    } finally {
      setDeleting(false);
    }
  };

  const handleTriggerAutoUpdate = async () => {
    setIsAutoUpdating(true);
    try {
      await apiService.triggerAutoUpdate();
      // Recargar datos después de un breve delay
      setTimeout(() => {
        loadDashboardData();
        loadNewspapers();
      }, 2000);
    } catch (error: any) {
      console.error('Error triggering auto update:', error);
      
      // Mostrar mensaje de error más específico
      if (error?.response?.status === 400) {
        const errorMessage = error?.response?.data?.error || 'Ya hay un scraping en ejecución';
        alert(`⚠️ ${errorMessage}`);
      } else {
        alert('❌ Error al iniciar la actualización automática. Inténtalo de nuevo.');
      }
    } finally {
      setIsAutoUpdating(false);
    }
  };

  const handleClearAllData = async () => {
    setClearing(true);
    try {
      const result = await apiService.clearAllData() as any;
      console.log('Datos borrados:', result);
      
      // Recargar estadísticas después de borrar
      await loadDashboardData();
      
      setClearDialogOpen(false);
      // Mostrar mensaje de éxito (podrías usar un snackbar aquí)
      alert(`✅ Datos borrados exitosamente:\n- ${result.deleted.articles} artículos\n- ${result.deleted.images} imágenes\n- ${result.deleted.stats} estadísticas`);
    } catch (err) {
      console.error('Error borrando datos:', err);
      alert('❌ Error al borrar los datos. Inténtalo de nuevo.');
    } finally {
      setClearing(false);
    }
  };

  // Configuración de colores para el diseño
  const colors = {
    primary: '#0ea5e9', // Celeste claro
    secondary: '#38bdf8', // Celeste más claro
    success: '#0ea5e9',
    warning: '#38bdf8',
    error: '#dc2626',
    info: '#0ea5e9',
    purple: '#0ea5e9',
    pink: '#0ea5e9',
    gradient1: 'linear-gradient(135deg, #0ea5e9 0%, #38bdf8 100%)', // Celeste claro a más claro
    gradient2: 'linear-gradient(135deg, #38bdf8 0%, #0ea5e9 100%)', // Celeste más claro a claro
    gradient3: 'linear-gradient(135deg, #0ea5e9 0%, #38bdf8 100%)', // Celeste claro a más claro
    gradient4: 'linear-gradient(135deg, #38bdf8 0%, #0ea5e9 100%)', // Celeste más claro a claro
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
      {/* Header Principal */}
      <Fade in timeout={800}>
        <Box sx={{ mb: 6, textAlign: 'center', position: 'relative' }}>
          {/* Efecto de fondo decorativo */}
          <Box
            sx={{
              position: 'absolute',
              top: -50,
              left: '50%',
              transform: 'translateX(-50%)',
              width: 200,
              height: 200,
              borderRadius: '50%',
              background: 'linear-gradient(45deg, rgba(25, 118, 210, 0.1), rgba(66, 165, 245, 0.1))',
              filter: 'blur(60px)',
              zIndex: 0,
            }}
          />
          
          <Avatar
            sx={{
              width: 100,
              height: 100,
              mx: 'auto',
              mb: 3,
              background: colors.gradient1,
              boxShadow: '0 20px 40px rgba(14, 165, 233, 0.15)',
              position: 'relative',
              zIndex: 2,
            }}
          >
            <WebIcon sx={{ fontSize: 50 }} />
          </Avatar>
          
          <Typography
            variant="h2"
            component="h1"
            gutterBottom
            sx={{
              fontWeight: 800,
              background: colors.gradient1,
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              mb: 2,
              position: 'relative',
              zIndex: 2,
            }}
          >
            PORTAL DE NOTICIAS
          </Typography>
          
          <Typography 
            variant="h5" 
            color="text.secondary" 
            sx={{ 
              maxWidth: 600, 
              mx: 'auto',
              fontWeight: 400,
              position: 'relative',
              zIndex: 2,
            }}
          >
            Sistema inteligente de extracción y análisis de datos web
          </Typography>
          
          {/* Botón para refrescar permisos (solo para usuarios no admin) */}
          {!isAdmin && (
            <Box sx={{ mt: 2, position: 'relative', zIndex: 2 }}>
              <Button
                variant="outlined"
                size="small"
                onClick={async () => {
                  await refreshPermissions();
                  // Recargar datos del dashboard
                  loadDashboardData();
                }}
                sx={{
                  borderRadius: 2,
                  textTransform: 'none',
                  fontSize: '0.75rem',
                }}
              >
                🔄 Actualizar Permisos
              </Button>
            </Box>
          )}
        </Box>
      </Fade>

      {/* Botón de Limpieza - Solo para Administradores */}
      {isAdmin && (
        <Fade in timeout={1000}>
          <Box sx={{ mb: 4, textAlign: 'center' }}>
            <Button
              variant="outlined"
              color="error"
              startIcon={<DeleteIcon />}
              onClick={() => setClearDialogOpen(true)}
              sx={{
                borderRadius: 3,
                px: 4,
                py: 2,
                fontWeight: 600,
                textTransform: 'none',
                borderWidth: 2,
                fontSize: '1rem',
                '&:hover': {
                  borderWidth: 2,
                  bgcolor: 'error.main',
                  color: 'white',
                  transform: 'translateY(-3px)',
                  boxShadow: '0 10px 25px rgba(244, 67, 54, 0.3)',
                },
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              }}
            >
              Borrar Todos los Datos
            </Button>
          </Box>
        </Fade>
      )}

      {/* Estado del Scraping - Solo para Administradores */}
      {isAdmin && (
      <Fade in timeout={1200}>
        <Card
          sx={{
            mb: 4,
            borderRadius: 4,
            background: scrapingStatus?.is_running 
              ? 'linear-gradient(135deg, #0ea5e9 0%, #38bdf8 100%)'
              : 'linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%)',
            color: scrapingStatus?.is_running ? 'white' : '#0f172a',
            boxShadow: scrapingStatus?.is_running 
              ? '0 10px 30px rgba(14, 165, 233, 0.2)'
              : '0 10px 30px rgba(0, 0, 0, 0.08)',
            overflow: 'hidden',
            position: 'relative',
            border: scrapingStatus?.is_running ? 'none' : '1px solid rgba(0, 0, 0, 0.08)',
          }}
        >
          <CardContent sx={{ p: 4 }}>
            <Grid container spacing={3} alignItems="center">
              <Grid size={{ xs: 12, md: 8 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Avatar
                    sx={{
                      bgcolor: scrapingStatus?.is_running 
                        ? 'rgba(255,255,255,0.2)' 
                        : 'linear-gradient(135deg, #0ea5e9 0%, #38bdf8 100%)',
                      mr: 2,
                      width: 60,
                      height: 60,
                      color: scrapingStatus?.is_running ? 'white' : 'white',
                    }}
                  >
                    {scrapingStatus?.is_running ? (
                      <WebIcon sx={{ fontSize: 30 }} />
                    ) : (
                      <DashboardIcon sx={{ fontSize: 30 }} />
                    )}
                  </Avatar>
                  <Box>
                    <Typography 
                      variant="h4" 
                      sx={{ 
                        fontWeight: 700, 
                        mb: 1,
                        color: scrapingStatus?.is_running ? 'white' : '#0f172a',
                      }}
                    >
                      Estado del Scraping
                    </Typography>
                    <Typography 
                      variant="h6" 
                      sx={{ 
                        color: scrapingStatus?.is_running ? 'rgba(255,255,255,0.95)' : '#475569',
                        fontWeight: 600,
                      }}
                    >
                      {scrapingStatus?.is_running ? 'Sistema activo' : 'Sistema inactivo'}
                    </Typography>
                  </Box>
                </Box>
                
                <Typography 
                  variant="body1" 
                  sx={{ 
                    maxWidth: 500,
                    color: scrapingStatus?.is_running ? 'rgba(255,255,255,0.9)' : '#64748b',
                    fontWeight: 500,
                    lineHeight: 1.7,
                  }}
                >
                  {scrapingStatus?.is_running 
                    ? 'El sistema está extrayendo datos activamente. Puedes monitorear el progreso en tiempo real.'
                    : 'Configura los parámetros y presiona "Iniciar Scraping" para comenzar la extracción de datos.'
                  }
                </Typography>
              </Grid>
              
              <Grid size={{ xs: 12, md: 4 }}>
                <Box sx={{ textAlign: 'center', display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <Button
                    variant="contained"
                    size="large"
                    startIcon={<PlayIcon />}
                    onClick={() => navigate('/scraping')}
                    sx={{
                      borderRadius: 3,
                      px: 4,
                      py: 2,
                      fontSize: '1.1rem',
                      fontWeight: 600,
                      textTransform: 'none',
                      background: scrapingStatus?.is_running 
                        ? 'rgba(255,255,255,0.2)'
                        : 'linear-gradient(135deg, #0ea5e9 0%, #38bdf8 100%)',
                      color: scrapingStatus?.is_running ? 'white' : 'white',
                      border: scrapingStatus?.is_running ? '1px solid rgba(255,255,255,0.3)' : 'none',
                      boxShadow: scrapingStatus?.is_running 
                        ? 'none'
                        : '0 4px 14px rgba(14, 165, 233, 0.3)',
                      '&:hover': {
                        background: scrapingStatus?.is_running 
                          ? 'rgba(255,255,255,0.3)'
                          : 'linear-gradient(135deg, #0284c7 0%, #0ea5e9 100%)',
                        transform: 'translateY(-2px)',
                        boxShadow: scrapingStatus?.is_running 
                          ? '0 4px 12px rgba(255,255,255,0.2)'
                          : '0 6px 20px rgba(14, 165, 233, 0.4)',
                      },
                      transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    }}
                  >
                    {scrapingStatus?.is_running ? 'Monitorear' : 'INICIAR SCRAPING'}
                  </Button>
                  
                  <Button
                    variant="outlined"
                    size="large"
                    startIcon={<WebIcon />}
                    onClick={handleTriggerAutoUpdate}
                    disabled={isAutoUpdating}
                    sx={{
                      borderRadius: 3,
                      px: 4,
                      py: 2,
                      fontSize: '1rem',
                      fontWeight: 600,
                      textTransform: 'none',
                      borderColor: scrapingStatus?.is_running ? 'rgba(255,255,255,0.5)' : '#4caf50',
                      borderWidth: 2,
                      color: scrapingStatus?.is_running ? 'white' : '#4caf50',
                      '&:hover': {
                        borderColor: scrapingStatus?.is_running ? 'rgba(255,255,255,0.7)' : '#45a049',
                        backgroundColor: scrapingStatus?.is_running 
                          ? 'rgba(255,255,255,0.1)'
                          : 'rgba(76, 175, 80, 0.06)',
                        transform: 'translateY(-1px)',
                        borderWidth: 2,
                      },
                      transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    }}
                  >
                    {isAutoUpdating ? 'Actualizando...' : '🔄 ACTUALIZAR AUTOMÁTICO'}
                  </Button>
                </Box>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Fade>
      )}

      {/* Métricas Principales */}
      <Fade in timeout={1400}>
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Zoom in timeout={1600}>
              <Card
                sx={{
                  height: '100%',
                  background: colors.gradient1,
                  color: 'white',
                  position: 'relative',
                  overflow: 'hidden',
                  borderRadius: 4,
                  boxShadow: '0 15px 35px rgba(14, 165, 233, 0.15)',
                  '&:hover': {
                    transform: 'translateY(-8px)',
                    boxShadow: '0 25px 50px rgba(102, 126, 234, 0.4)',
                  },
                  transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
                }}
              >
                <CardContent sx={{ position: 'relative', zIndex: 2, p: 3 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)', mr: 2, width: 50, height: 50 }}>
                      <ArticleIcon sx={{ fontSize: 28 }} />
                    </Avatar>
                    <Box>
                      <Typography 
                        variant="h3" 
                        sx={{ 
                          fontWeight: 'bold', 
                          lineHeight: 1,
                          color: 'white',
                          textShadow: '0 2px 8px rgba(0, 0, 0, 0.3)',
                          fontSize: { xs: '2rem', md: '2.5rem' },
                        }}
                      >
                        {statistics?.general?.total_articles || 0}
                      </Typography>
                      <Typography 
                        variant="body2" 
                        sx={{ 
                          opacity: 0.95, 
                          fontSize: '0.95rem',
                          color: 'white',
                          fontWeight: 600,
                          textShadow: '0 1px 3px rgba(0, 0, 0, 0.2)',
                          mt: 0.5,
                        }}
                      >
                        Artículos Extraídos
                      </Typography>
                    </Box>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                    <TrendingIcon sx={{ mr: 1, fontSize: 20, color: 'white', opacity: 0.9 }} />
                    <Typography 
                      variant="body2" 
                      sx={{ 
                        opacity: 0.95, 
                        fontSize: '0.85rem',
                        color: 'white',
                        fontWeight: 500,
                      }}
                    >
                      +12% vs mes anterior
                    </Typography>
                  </Box>
                </CardContent>
                <Box
                  sx={{
                    position: 'absolute',
                    top: -30,
                    right: -30,
                    width: 120,
                    height: 120,
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
                  background: colors.gradient2,
                  color: 'white',
                  position: 'relative',
                  overflow: 'hidden',
                  borderRadius: 4,
                  boxShadow: '0 15px 35px rgba(14, 165, 233, 0.15)',
                  '&:hover': {
                    transform: 'translateY(-8px)',
                    boxShadow: '0 25px 50px rgba(240, 147, 251, 0.4)',
                  },
                  transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
                }}
              >
                <CardContent sx={{ position: 'relative', zIndex: 2, p: 3 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)', mr: 2, width: 50, height: 50 }}>
                      <ImageIcon sx={{ fontSize: 28 }} />
                    </Avatar>
                    <Box>
                      <Typography 
                        variant="h3" 
                        sx={{ 
                          fontWeight: 'bold', 
                          lineHeight: 1,
                          color: 'white',
                          textShadow: '0 2px 8px rgba(0, 0, 0, 0.3)',
                          fontSize: { xs: '2rem', md: '2.5rem' },
                        }}
                      >
                        {statistics?.general?.total_images_downloaded || 0}
                      </Typography>
                      <Typography 
                        variant="body2" 
                        sx={{ 
                          opacity: 0.95, 
                          fontSize: '0.95rem',
                          color: 'white',
                          fontWeight: 600,
                          textShadow: '0 1px 3px rgba(0, 0, 0, 0.2)',
                          mt: 0.5,
                        }}
                      >
                        Imágenes Descargadas
                      </Typography>
                    </Box>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                    <TrendingIcon sx={{ mr: 1, fontSize: 20, color: 'white', opacity: 0.9 }} />
                    <Typography 
                      variant="body2" 
                      sx={{ 
                        opacity: 0.95, 
                        fontSize: '0.85rem',
                        color: 'white',
                        fontWeight: 500,
                      }}
                    >
                      +8% vs mes anterior
                    </Typography>
                  </Box>
                </CardContent>
                <Box
                  sx={{
                    position: 'absolute',
                    top: -30,
                    right: -30,
                    width: 120,
                    height: 120,
                    borderRadius: '50%',
                    background: 'rgba(255,255,255,0.1)',
                    zIndex: 1,
                  }}
                />
              </Card>
            </Zoom>
          </Grid>

          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Zoom in timeout={2000}>
              <Card
                sx={{
                  height: '100%',
                  background: colors.gradient3,
                  color: 'white',
                  position: 'relative',
                  overflow: 'hidden',
                  borderRadius: 4,
                  boxShadow: '0 15px 35px rgba(79, 172, 254, 0.3)',
                  '&:hover': {
                    transform: 'translateY(-8px)',
                    boxShadow: '0 25px 50px rgba(79, 172, 254, 0.4)',
                  },
                  transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
                }}
              >
                <CardContent sx={{ position: 'relative', zIndex: 2, p: 3 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)', mr: 2, width: 50, height: 50 }}>
                      <NewspaperIcon sx={{ fontSize: 28 }} />
                    </Avatar>
                    <Box>
                      <Typography 
                        variant="h3" 
                        sx={{ 
                          fontWeight: 'bold', 
                          lineHeight: 1,
                          color: 'white',
                          textShadow: '0 2px 8px rgba(0, 0, 0, 0.3)',
                          fontSize: { xs: '2rem', md: '2.5rem' },
                        }}
                      >
                        {statistics?.general?.total_newspapers || 0}
                      </Typography>
                      <Typography 
                        variant="body2" 
                        sx={{ 
                          opacity: 0.95, 
                          fontSize: '0.95rem',
                          color: 'white',
                          fontWeight: 600,
                          textShadow: '0 1px 3px rgba(0, 0, 0, 0.2)',
                          mt: 0.5,
                        }}
                      >
                        Periódicos Monitoreados
                      </Typography>
                    </Box>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                    <PublicIcon sx={{ mr: 1, fontSize: 20, color: 'white', opacity: 0.9 }} />
                    <Typography 
                      variant="body2" 
                      sx={{ 
                        opacity: 0.95, 
                        fontSize: '0.85rem',
                        color: 'white',
                        fontWeight: 500,
                      }}
                    >
                      Fuentes activas
                    </Typography>
                  </Box>
                </CardContent>
                <Box
                  sx={{
                    position: 'absolute',
                    top: -30,
                    right: -30,
                    width: 120,
                    height: 120,
                    borderRadius: '50%',
                    background: 'rgba(255,255,255,0.1)',
                    zIndex: 1,
                  }}
                />
              </Card>
            </Zoom>
          </Grid>

          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Zoom in timeout={2200}>
              <Card
                sx={{
                  height: '100%',
                  background: colors.gradient4,
                  color: 'white',
                  position: 'relative',
                  overflow: 'hidden',
                  borderRadius: 4,
                  boxShadow: '0 15px 35px rgba(67, 233, 123, 0.3)',
                  '&:hover': {
                    transform: 'translateY(-8px)',
                    boxShadow: '0 25px 50px rgba(67, 233, 123, 0.4)',
                  },
                  transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
                }}
              >
                <CardContent sx={{ position: 'relative', zIndex: 2, p: 3 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)', mr: 2, width: 50, height: 50 }}>
                      <CategoryIcon sx={{ fontSize: 28 }} />
                    </Avatar>
                    <Box>
                      <Typography 
                        variant="h3" 
                        sx={{ 
                          fontWeight: 'bold', 
                          lineHeight: 1,
                          color: 'white',
                          textShadow: '0 2px 8px rgba(0, 0, 0, 0.3)',
                          fontSize: { xs: '2rem', md: '2.5rem' },
                        }}
                      >
                        {statistics?.general?.total_categories || 0}
                      </Typography>
                      <Typography 
                        variant="body2" 
                        sx={{ 
                          opacity: 0.95, 
                          fontSize: '0.95rem',
                          color: 'white',
                          fontWeight: 600,
                          textShadow: '0 1px 3px rgba(0, 0, 0, 0.2)',
                          mt: 0.5,
                        }}
                      >
                        Categorías Identificadas
                      </Typography>
                    </Box>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                    <CategoryIcon sx={{ mr: 1, fontSize: 20, color: 'white', opacity: 0.9 }} />
                    <Typography 
                      variant="body2" 
                      sx={{ 
                        opacity: 0.95, 
                        fontSize: '0.85rem',
                        color: 'white',
                        fontWeight: 500,
                      }}
                    >
                      +15% vs mes anterior
                    </Typography>
                  </Box>
                </CardContent>
                <Box
                  sx={{
                    position: 'absolute',
                    top: -30,
                    right: -30,
                    width: 120,
                    height: 120,
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

      {/* Carrusel de Anuncios y Comentarios Virales */}
      <Fade in timeout={1600}>
        <Grid container spacing={3} sx={{ mb: 4 }}>
          {/* Carrusel de Anuncios - Visible para todos */}
          <Grid size={{ xs: 12, md: hasPermission('view_social_media') ? 6 : 12 }}>
            <AdsCarousel />
          </Grid>
          {/* Comentarios Virales - Solo con permiso */}
          {hasPermission('view_social_media') && (
            <Grid size={{ xs: 12, md: 6 }}>
              <ViralComments />
            </Grid>
          )}
        </Grid>
      </Fade>

      {/* Gestión de Periódicos */}
      <Fade in timeout={2400}>
        <Card
          sx={{
            borderRadius: 4,
            background: colors.gradient2,
            color: 'white',
            boxShadow: '0 15px 35px rgba(14, 165, 233, 0.15)',
            overflow: 'hidden',
            position: 'relative',
            mb: 4,
          }}
        >
          <CardContent sx={{ p: 4 }}>
            <Typography variant="h4" sx={{ fontWeight: 700, mb: 3, display: 'flex', alignItems: 'center' }}>
              <NewspaperIcon sx={{ mr: 2, fontSize: 40 }} />
              Gestión de Periódicos
            </Typography>
            
            {newspapersLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <LinearProgress sx={{ width: '100%', maxWidth: 400 }} />
              </Box>
            ) : newspapers.length === 0 ? (
              <Typography variant="body1" sx={{ textAlign: 'center', py: 4, opacity: 0.8 }}>
                No hay periódicos registrados aún
              </Typography>
            ) : (
              <Grid container spacing={2}>
                {newspapers.map((newspaper, index) => (
                  <Grid size={{ xs: 12, sm: 6, md: 4 }} key={newspaper.newspaper}>
                    <Card
                      sx={{
                        background: 'rgba(255, 255, 255, 0.1)',
                        backdropFilter: 'blur(10px)',
                        border: '1px solid rgba(255, 255, 255, 0.2)',
                        borderRadius: 3,
                        '&:hover': {
                          background: 'rgba(255, 255, 255, 0.15)',
                          transform: 'translateY(-2px)',
                        },
                        transition: 'all 0.3s ease',
                      }}
                    >
                      <CardContent sx={{ p: 3 }}>
                        <Typography variant="h6" sx={{ fontWeight: 600, mb: 2, color: 'white' }}>
                          {newspaper.newspaper}
                        </Typography>
                        
                        <Box sx={{ mb: 2 }}>
                          <Typography variant="body2" sx={{ opacity: 0.9, mb: 1 }}>
                            📰 {newspaper.articles_count} artículos
                          </Typography>
                          <Typography variant="body2" sx={{ opacity: 0.9, mb: 1 }}>
                            🖼️ {newspaper.total_images_downloaded} imágenes
                          </Typography>
                          <Typography variant="body2" sx={{ opacity: 0.8, fontSize: '0.8rem' }}>
                            Última extracción: {new Date(newspaper.last_scraped).toLocaleDateString()}
                          </Typography>
                        </Box>
                        
                        <Button
                          variant="outlined"
                          size="small"
                          color="error"
                          startIcon={<DeleteIcon />}
                          onClick={() => handleDeleteNewspaper(newspaper)}
                          sx={{
                            borderColor: 'rgba(255, 255, 255, 0.5)',
                            color: 'white',
                            '&:hover': {
                              borderColor: 'white',
                              backgroundColor: 'rgba(255, 255, 255, 0.1)',
                            },
                          }}
                        >
                          Eliminar
                        </Button>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            )}
          </CardContent>
        </Card>
      </Fade>

      {/* Acciones Rápidas */}
      <Fade in timeout={2600}>
        <Card
          sx={{
            borderRadius: 4,
            background: colors.gradient1,
            color: 'white',
            boxShadow: '0 15px 35px rgba(14, 165, 233, 0.15)',
            overflow: 'hidden',
            position: 'relative',
          }}
        >
          <CardContent sx={{ p: 4 }}>
            <Typography variant="h4" sx={{ fontWeight: 700, mb: 3, display: 'flex', alignItems: 'center' }}>
              <AnalyticsIcon sx={{ mr: 2, fontSize: 40 }} />
              Acciones Rápidas
            </Typography>
            
            <Grid container spacing={3}>
              {hasPermission('view_articles') && (
                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <Button
                    variant="contained"
                    fullWidth
                    startIcon={<ArticleIcon />}
                    onClick={() => navigate('/articles')}
                    sx={{
                      borderRadius: 3,
                      py: 2,
                      bgcolor: 'rgba(255,255,255,0.2)',
                      '&:hover': { 
                        bgcolor: 'rgba(255,255,255,0.3)',
                        transform: 'translateY(-2px)',
                      },
                      transition: 'all 0.3s ease',
                    }}
                  >
                    Ver Artículos
                  </Button>
                </Grid>
              )}
              
              {hasPermission('view_images') && (
                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <Button
                    variant="contained"
                    fullWidth
                    startIcon={<ImageIcon />}
                    onClick={() => navigate('/images')}
                    sx={{
                      borderRadius: 3,
                      py: 2,
                      bgcolor: 'rgba(255,255,255,0.2)',
                      '&:hover': { 
                        bgcolor: 'rgba(255,255,255,0.3)',
                        transform: 'translateY(-2px)',
                      },
                      transition: 'all 0.3s ease',
                    }}
                  >
                    Galería de Imágenes
                  </Button>
                </Grid>
              )}
              
              {hasPermission('view_analytics') && (
                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <Button
                    variant="contained"
                    fullWidth
                    startIcon={<AnalyticsIcon />}
                    onClick={() => navigate('/statistics')}
                    sx={{
                      borderRadius: 3,
                      py: 2,
                      bgcolor: 'rgba(255,255,255,0.2)',
                      '&:hover': { 
                        bgcolor: 'rgba(255,255,255,0.3)',
                        transform: 'translateY(-2px)',
                      },
                      transition: 'all 0.3s ease',
                    }}
                  >
                    Ver Estadísticas
                  </Button>
                </Grid>
              )}
              
              {hasPermission('manage_database') && (
                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <Button
                    variant="contained"
                    fullWidth
                    startIcon={<StorageIcon />}
                    onClick={() => navigate('/database')}
                    sx={{
                      borderRadius: 3,
                      py: 2,
                      bgcolor: 'rgba(255,255,255,0.2)',
                      '&:hover': { 
                        bgcolor: 'rgba(255,255,255,0.3)',
                        transform: 'translateY(-2px)',
                      },
                      transition: 'all 0.3s ease',
                    }}
                  >
                    Configurar BD
                  </Button>
                </Grid>
              )}
            </Grid>
          </CardContent>
        </Card>
      </Fade>

      {/* Diálogo de Confirmación para Borrar Datos */}
      <Dialog
        open={clearDialogOpen}
        onClose={() => setClearDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ 
          bgcolor: 'error.main', 
          color: 'white',
          display: 'flex',
          alignItems: 'center',
          gap: 1
        }}>
          <DeleteIcon />
          ⚠️ Confirmar Borrado de Datos
        </DialogTitle>
        <DialogContent sx={{ pt: 3 }}>
          <DialogContentText variant="body1" sx={{ mb: 2 }}>
            <strong>¿Estás seguro de que quieres borrar TODOS los datos?</strong>
          </DialogContentText>
          <DialogContentText variant="body2" color="text.secondary">
            Esta acción eliminará permanentemente:
          </DialogContentText>
          <Box component="ul" sx={{ mt: 1, pl: 2 }}>
            <li>Todos los artículos extraídos</li>
            <li>Todas las imágenes descargadas</li>
            <li>Todas las estadísticas de scraping</li>
            <li>Todo el historial de extracciones</li>
          </Box>
          <DialogContentText variant="body2" color="error.main" sx={{ mt: 2, fontWeight: 'bold' }}>
            ⚠️ Esta acción NO se puede deshacer.
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ p: 3, gap: 1 }}>
          <Button
            onClick={() => setClearDialogOpen(false)}
            variant="outlined"
            disabled={clearing}
            sx={{ borderRadius: 2 }}
          >
            Cancelar
          </Button>
          <Button
            onClick={handleClearAllData}
            variant="contained"
            color="error"
            disabled={clearing}
            startIcon={clearing ? null : <DeleteIcon />}
            sx={{ borderRadius: 2 }}
          >
            {clearing ? 'Borrando...' : '🗑️ Borrar Todo'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Diálogo de Confirmación para Eliminar Periódico */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ 
          bgcolor: 'error.main', 
          color: 'white',
          display: 'flex',
          alignItems: 'center',
          gap: 1
        }}>
          <DeleteIcon />
          ⚠️ Confirmar Eliminación de Periódico
        </DialogTitle>
        <DialogContent sx={{ pt: 3 }}>
          <DialogContentText variant="body1" sx={{ mb: 2 }}>
            <strong>¿Estás seguro de que quieres eliminar todos los datos de "{selectedNewspaper?.newspaper}"?</strong>
          </DialogContentText>
          <DialogContentText variant="body2" color="text.secondary">
            Esta acción eliminará permanentemente:
          </DialogContentText>
          <Box component="ul" sx={{ mt: 1, pl: 2 }}>
            <li>{selectedNewspaper?.articles_count || 0} artículos</li>
            <li>{selectedNewspaper?.total_images_downloaded || 0} imágenes</li>
            <li>Todas las estadísticas de scraping relacionadas</li>
            <li>Los archivos de imagen físicos</li>
          </Box>
          <DialogContentText variant="body2" color="error.main" sx={{ mt: 2, fontWeight: 'bold' }}>
            ⚠️ Esta acción NO se puede deshacer.
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ p: 3, gap: 1 }}>
          <Button
            onClick={() => setDeleteDialogOpen(false)}
            variant="outlined"
            disabled={deleting}
            sx={{ borderRadius: 2 }}
          >
            Cancelar
          </Button>
          <Button
            onClick={confirmDeleteNewspaper}
            variant="contained"
            color="error"
            disabled={deleting}
            startIcon={deleting ? null : <DeleteIcon />}
            sx={{ borderRadius: 2 }}
          >
            {deleting ? 'Eliminando...' : 'Eliminar Periódico'}
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Chatbot flotante */}
      <ChatbotWidget />
    </Container>
  );
};

export default Dashboard;