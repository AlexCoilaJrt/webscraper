import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
  Box,
  Alert,
  LinearProgress,
  Chip,
  Paper,
  Grid,
  Divider,
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Settings as SettingsIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { apiService, ScrapingConfig, ScrapingStatus } from '../services/api';
import { api } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { Alert as MuiAlert } from '@mui/material';

const ScrapingControl: React.FC = () => {
  const { isAdmin } = useAuth();
  const [userSubscription, setUserSubscription] = useState<any>(null);
  const [usageLimits, setUsageLimits] = useState<any>(null);
  
  const [config, setConfig] = useState<ScrapingConfig>({
    url: '',
    max_articles: 0, // 0 = extraer todos los artículos disponibles (o límite del plan)
    max_images: 50,
    method: 'auto',
    download_images: true,
    category: '',
    newspaper: '',
    region: '',
  });

  const [scrapingStatus, setScrapingStatus] = useState<ScrapingStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    loadStatus();
    loadUserSubscription();
    loadUsageLimits();
    
    // Poll for status updates
    const interval = setInterval(loadStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  const loadUserSubscription = async () => {
    try {
      const response = await api.get('/subscriptions/user-subscription');
      if (response.data && (response.data as any).subscription) {
        setUserSubscription((response.data as any).subscription);
      }
    } catch (err) {
      console.error('Error loading subscription:', err);
    }
  };

  const loadUsageLimits = async () => {
    try {
      const response = await api.get('/subscriptions/usage-limits');
      if (response.data && (response.data as any).limits) {
        setUsageLimits((response.data as any).limits);
        // Ajustar max_images por defecto según el plan
        const maxImages = (response.data as any).limits.max_images;
        if (maxImages && maxImages !== -1 && maxImages < 50) {
          setConfig(prev => ({ ...prev, max_images: maxImages }));
        }
      }
    } catch (err) {
      console.error('Error loading usage limits:', err);
    }
  };

  const loadStatus = async () => {
    try {
      const status = await apiService.getStatus();
      setScrapingStatus(status);
    } catch (err) {
      console.error('Error loading status:', err);
    }
  };

  const handleInputChange = (field: keyof ScrapingConfig) => (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement> | any
  ) => {
    const value = event.target.type === 'checkbox' ? event.target.checked : event.target.value;
    setConfig(prev => ({
      ...prev,
      [field]: field === 'max_articles' || field === 'max_images' ? parseInt(value) || 0 : value,
    }));
  };

  const handleStartScraping = async () => {
    if (!config.url.trim()) {
      setError('Por favor ingresa una URL válida');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setSuccess(null);
      
      await apiService.startScraping(config);
      setSuccess('Scraping iniciado correctamente');
      
      // Load status immediately
      setTimeout(loadStatus, 1000);
      
    } catch (err: any) {
      if (err.response?.status === 409 && err.response?.data?.duplicate) {
        setError(err.response.data.message || 'Esta URL ya ha sido scrapeada anteriormente');
      } else if (err.response?.status === 429) {
        // Límite excedido
        const errorMsg = err.response?.data?.message || err.response?.data?.error || 'Límite de uso excedido';
        setError(errorMsg);
      } else {
        setError(err.response?.data?.error || err.response?.data?.message || 'Error iniciando el scraping');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleStopScraping = async () => {
    try {
      setLoading(true);
      await apiService.stopScraping();
      setSuccess('Scraping detenido');
      setTimeout(loadStatus, 1000);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Error deteniendo el scraping');
    } finally {
      setLoading(false);
    }
  };

  const isRunning = scrapingStatus?.is_running || false;

  const getPlanDisplayName = () => {
    if (isAdmin) return 'Plan Administrador';
    if (userSubscription) return userSubscription.plan_display_name || userSubscription.plan_name || 'Plan Gratuito';
    return 'Plan Gratuito';
  };

  const getRemainingArticles = () => {
    if (!usageLimits) return null;
    if (usageLimits.max_articles === -1) return 'Ilimitado';
    const remaining = usageLimits.max_articles - usageLimits.current_articles;
    return Math.max(0, remaining);
  };

  const getRemainingImages = () => {
    if (!usageLimits) return null;
    if (usageLimits.max_images === -1) return 'Ilimitado';
    return usageLimits.max_images;
  };

  const isNearLimit = () => {
    if (!usageLimits || usageLimits.max_articles === -1) return false;
    const percentage = (usageLimits.current_articles / usageLimits.max_articles) * 100;
    return percentage >= 80;
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4" component="h1">
        Control de Scraping
      </Typography>
        {userSubscription && (
          <Chip 
            label={getPlanDisplayName()} 
            color={isAdmin ? 'error' : userSubscription.plan_name === 'premium' ? 'primary' : userSubscription.plan_name === 'enterprise' ? 'secondary' : 'default'}
            sx={{ fontWeight: 600 }}
          />
        )}
      </Box>

      {/* Información de límites del plan */}
      {usageLimits && !isAdmin && (
        <MuiAlert 
          severity={isNearLimit() ? 'warning' : 'info'} 
          icon={<InfoIcon />}
          sx={{ mb: 3 }}
        >
          <Typography variant="body2" sx={{ fontWeight: 600, mb: 1 }}>
            Límites de tu plan ({getPlanDisplayName()}):
          </Typography>
          <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
            <Typography variant="body2">
              📰 Artículos: <strong>{usageLimits.current_articles}</strong> / {usageLimits.max_articles === -1 ? 'Ilimitado' : usageLimits.max_articles} 
              {usageLimits.max_articles !== -1 && ` (Restantes: ${getRemainingArticles()})`}
            </Typography>
            <Typography variant="body2">
              🖼️ Imágenes por scraping: <strong>{getRemainingImages()}</strong>
            </Typography>
          </Box>
          {isNearLimit() && (
            <Typography variant="body2" sx={{ mt: 1, fontWeight: 600 }}>
              ⚠️ Estás cerca del límite. Considera actualizar tu plan para obtener más capacidad.
            </Typography>
          )}
        </MuiAlert>
      )}

      <Grid container spacing={3}>
        {/* Configuration Panel */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <SettingsIcon sx={{ mr: 1 }} />
                <Typography variant="h6">
                  Configuración del Scraping
                </Typography>
              </Box>

              {error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {error}
                </Alert>
              )}

              {success && (
                <Alert severity="success" sx={{ mb: 2 }}>
                  {success}
                </Alert>
              )}

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                <TextField
                  label="URL a Scrapear"
                  value={config.url}
                  onChange={handleInputChange('url')}
                  placeholder="https://ejemplo.com/noticias"
                  fullWidth
                  disabled={isRunning}
                  helperText="Ingresa la URL del sitio web que quieres scrapear"
                />

                <TextField
                  label="Nombre del Periódico/Noticiero"
                  value={config.newspaper}
                  onChange={handleInputChange('newspaper')}
                  placeholder="El Comercio, La República, CNN, BBC, etc."
                  fullWidth
                  disabled={isRunning}
                  helperText="Especifica el nombre del periódico o noticiero para mejor clasificación"
                />

                <TextField
                  label="Categoría"
                  value={config.category}
                  onChange={handleInputChange('category')}
                  placeholder="Política, Deportes, Tecnología, etc."
                  fullWidth
                  disabled={isRunning}
                  helperText="Asigna una categoría a los artículos que se extraigan"
                />

                <FormControl fullWidth disabled={isRunning}>
                  <InputLabel>Región</InputLabel>
                  <Select
                    value={config.region}
                    onChange={handleInputChange('region')}
                    label="Región"
                  >
                    <MenuItem value="">Auto-detectar</MenuItem>
                    <MenuItem value="nacional">🇵🇪 Nacional</MenuItem>
                    <MenuItem value="extranjero">🌍 Extranjero</MenuItem>
                  </Select>
                  <Box sx={{ mt: 1, fontSize: '0.75rem', color: 'text.secondary' }}>
                    Especifica si el contenido es nacional (Perú) o extranjero para mejor clasificación
                  </Box>
                </FormControl>

                <Grid container spacing={2}>
                  <Grid size={{ xs: 6 }}>
                    <TextField
                      label="Máximo Artículos"
                      type="number"
                      value={config.max_articles}
                      onChange={handleInputChange('max_articles')}
                      fullWidth
                      disabled={isRunning}
                      inputProps={{ 
                        min: 0, 
                        max: isAdmin || (usageLimits && usageLimits.max_articles === -1) ? 2000 : usageLimits?.max_articles || 50
                      }}
                      helperText={
                        isAdmin || (usageLimits && usageLimits.max_articles === -1)
                          ? (config.max_articles === 0 ? "0 = Extraer TODOS los artículos disponibles" : "Ingresa 0 para extraer todos los artículos disponibles")
                          : `Máximo según tu plan: ${usageLimits?.max_articles || 50} artículos/día. 0 = usar límite restante (${getRemainingArticles()})`
                      }
                      placeholder="0 = límite del plan"
                    />
                  </Grid>
                  <Grid size={{ xs: 6 }}>
                    <TextField
                      label="Máximo Imágenes"
                      type="number"
                      value={config.max_images}
                      onChange={handleInputChange('max_images')}
                      fullWidth
                      disabled={isRunning}
                      inputProps={{ 
                        min: 0, 
                        max: isAdmin || (usageLimits && usageLimits.max_images === -1) ? 500 : usageLimits?.max_images || 10
                      }}
                      helperText={
                        isAdmin || (usageLimits && usageLimits.max_images === -1)
                          ? "Máximo de imágenes a descargar"
                          : `Máximo según tu plan: ${usageLimits?.max_images || 10} imágenes por scraping`
                      }
                    />
                  </Grid>
                </Grid>

                <FormControl fullWidth disabled={isRunning}>
                  <InputLabel>Método de Scraping</InputLabel>
                  <Select
                    value={config.method}
                    onChange={handleInputChange('method')}
                    label="Método de Scraping"
                  >
                    <MenuItem value="auto">
                      <Box>
                        <Typography variant="body2" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                          🧠 Análisis Inteligente (Recomendado)
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Analiza la página y elige automáticamente el mejor método
                        </Typography>
                      </Box>
                    </MenuItem>
                    <MenuItem value="improved">
                      <Box>
                        <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                          📰 Mejorado
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Método robusto sin Selenium, ideal para sitios de noticias
                        </Typography>
                      </Box>
                    </MenuItem>
                    <MenuItem value="hybrid">
                      <Box>
                        <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                          🔄 Híbrido
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Combina Selenium y Requests automáticamente
                        </Typography>
                      </Box>
                    </MenuItem>
                    <MenuItem value="optimized">
                      <Box>
                        <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                          ⚡ Optimizado
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Usa cache y paralelismo para máximo rendimiento
                        </Typography>
                      </Box>
                    </MenuItem>
                    <MenuItem value="selenium">
                      <Box>
                        <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                          🤖 Selenium
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Para contenido dinámico y JavaScript
                        </Typography>
                      </Box>
                    </MenuItem>
                    <MenuItem value="requests">
                      <Box>
                        <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                          🚀 Requests
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Rápido para contenido estático
                        </Typography>
                      </Box>
                    </MenuItem>
                  </Select>
                </FormControl>

                <FormControlLabel
                  control={
                    <Switch
                      checked={config.download_images}
                      onChange={handleInputChange('download_images')}
                      disabled={isRunning}
                    />
                  }
                  label="Descargar Imágenes"
                />

                <Divider />

                <Box sx={{ display: 'flex', gap: 2 }}>
                  <Button
                    variant="contained"
                    startIcon={<PlayIcon />}
                    onClick={handleStartScraping}
                    disabled={loading || isRunning || !config.url.trim()}
                    fullWidth
                    size="large"
                  >
                    {loading ? 'Iniciando...' : 'Iniciar Scraping'}
                  </Button>

                  {isRunning && (
                    <Button
                      variant="outlined"
                      startIcon={<StopIcon />}
                      onClick={handleStopScraping}
                      disabled={loading}
                      size="large"
                    >
                      Detener
                    </Button>
                  )}
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Status Panel */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <InfoIcon sx={{ mr: 1 }} />
                <Typography variant="h6">
                  Estado del Scraping
                </Typography>
              </Box>

              {isRunning ? (
                <Paper sx={{ p: 3, backgroundColor: '#e3f2fd' }}>
                  <Typography variant="h6" color="primary" gutterBottom>
                    🚀 Scraping en Progreso
                  </Typography>
                  
                  <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                    <Chip 
                      label={`📰 ${scrapingStatus?.articles_found || 0} artículos`}
                      color="primary"
                      variant="outlined"
                    />
                    <Chip 
                      label={`🖼️ ${scrapingStatus?.images_found || 0} imágenes`}
                      color="secondary"
                      variant="outlined"
                    />
                  </Box>
                  
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    URL: {scrapingStatus?.current_url}
                  </Typography>

                  <Box sx={{ mb: 3 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2">
                        Progreso: {scrapingStatus?.progress} / {scrapingStatus?.total}
                      </Typography>
                      <Typography variant="body2">
                        {scrapingStatus?.total ? Math.round((scrapingStatus.progress / scrapingStatus.total) * 100) : 0}%
                      </Typography>
                    </Box>
                    <LinearProgress 
                      variant="determinate" 
                      value={scrapingStatus?.total ? (scrapingStatus.progress / scrapingStatus.total) * 100 : 0}
                      sx={{ height: 8, borderRadius: 4 }}
                    />
                  </Box>

                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
                    <Chip 
                      label={`${scrapingStatus?.articles_found || 0} artículos`}
                      color="primary"
                      size="small"
                    />
                    <Chip 
                      label={`${scrapingStatus?.images_found || 0} imágenes`}
                      color="secondary"
                      size="small"
                    />
                  </Box>

                  {scrapingStatus?.start_time && (
                    <Typography variant="caption" color="text.secondary">
                      Iniciado: {new Date(scrapingStatus.start_time).toLocaleString()}
                    </Typography>
                  )}
                </Paper>
              ) : (
                <Paper sx={{ p: 3, backgroundColor: '#f5f5f5' }}>
                  <Typography variant="h6" color="text.secondary" gutterBottom>
                    ⏸️ Sin Scraping Activo
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Configura los parámetros y presiona "Iniciar Scraping" para comenzar.
                  </Typography>
                </Paper>
              )}

              {/* Mostrar análisis inteligente si está disponible */}
              {scrapingStatus?.analysis && (
                <Box sx={{ mt: 2 }}>
                  <Divider sx={{ my: 2 }} />
                  <Typography variant="subtitle2" gutterBottom>
                    🧠 Análisis Inteligente
                  </Typography>
                  <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                    <Typography variant="body2" color="text.secondary">
                      <strong>Método sugerido:</strong> 
                      <Chip 
                        label={scrapingStatus.suggested_method === 'improved' ? '📰 Mejorado' : 
                               scrapingStatus.suggested_method === 'hybrid' ? '🔄 Híbrido' :
                               scrapingStatus.suggested_method === 'optimized' ? '⚡ Optimizado' :
                               scrapingStatus.suggested_method === 'selenium' ? '🤖 Selenium' :
                               scrapingStatus.suggested_method === 'requests' ? '🚀 Requests' :
                               scrapingStatus.suggested_method}
                        color="primary"
                        size="small"
                        sx={{ ml: 1 }}
                      />
                      <br />
                      <strong>Confianza:</strong> {scrapingStatus.confidence}%
                      <br />
                      <strong>Dominio:</strong> {scrapingStatus.analysis.domain}
                      <br />
                      <strong>Tamaño de página:</strong> {Math.round(scrapingStatus.analysis.page_size / 1024)} KB
                      <br />
                      <strong>Artículos detectados:</strong> {scrapingStatus.analysis.analysis?.article_links || 0}
                      <br />
                      <strong>JavaScript:</strong> {scrapingStatus.analysis.analysis?.javascript_detected ? '✅' : '❌'}
                      <br />
                      <strong>Contenido dinámico:</strong> {scrapingStatus.analysis.analysis?.dynamic_content ? '✅' : '❌'}
                    </Typography>
                  </Paper>
                </Box>
              )}

              {scrapingStatus?.error && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  Error: {scrapingStatus.error}
                </Alert>
              )}

              {scrapingStatus?.end_time && !isRunning && (
                <Alert severity="success" sx={{ mt: 2 }}>
                  <Typography variant="body1" gutterBottom>
                    ✅ Scraping completado el {new Date(scrapingStatus.end_time).toLocaleString()}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    <Chip 
                      label={`📰 ${scrapingStatus?.articles_found || 0} artículos extraídos`}
                      color="primary"
                      size="small"
                    />
                    <Chip 
                      label={`🖼️ ${scrapingStatus?.images_found || 0} imágenes extraídas`}
                      color="secondary"
                      size="small"
                    />
                  </Box>
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Method Information */}
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Información sobre los Métodos
          </Typography>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, md: 4 }}>
              <Typography variant="subtitle2" color="primary">
                🧠 Análisis Inteligente
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Analiza automáticamente la página y decide el mejor método. Ideal para la mayoría de sitios.
              </Typography>
            </Grid>
            <Grid size={{ xs: 12, md: 4 }}>
              <Typography variant="subtitle2" color="primary">
                📰 Mejorado
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Método robusto sin Selenium, ideal para sitios de noticias y contenido estático.
              </Typography>
            </Grid>
            <Grid size={{ xs: 12, md: 4 }}>
              <Typography variant="subtitle2" color="primary">
                🔄 Híbrido
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Combina Selenium y Requests automáticamente para máxima compatibilidad.
              </Typography>
            </Grid>
            <Grid size={{ xs: 12, md: 4 }}>
              <Typography variant="subtitle2" color="primary">
                ⚡ Optimizado
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Usa cache y procesamiento paralelo para máximo rendimiento en sitios conocidos.
              </Typography>
            </Grid>
            <Grid size={{ xs: 12, md: 4 }}>
              <Typography variant="subtitle2" color="primary">
                🤖 Selenium
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Para sitios con mucho JavaScript, contenido dinámico o lazy loading.
              </Typography>
            </Grid>
            <Grid size={{ xs: 12, md: 4 }}>
              <Typography variant="subtitle2" color="primary">
                🚀 Requests
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Más rápido para sitios con contenido estático, sin JavaScript complejo.
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    </Box>
  );
};

export default ScrapingControl;
