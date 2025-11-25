import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Tabs,
  Tab,
  Grid,
  Alert,
  IconButton,
  CircularProgress,
  Switch,
  FormControlLabel,
  LinearProgress,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Campaign as CampaignIcon,
  Analytics as AnalyticsIcon,
  TrendingUp as TrendingUpIcon,
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
} from '@mui/icons-material';
import { api } from '../services/api';
import ReactECharts from '../components/analytics/ReactEChartsLite';

interface Campaign {
  id: number;
  name: string;
  description?: string;
  advertiser_name?: string;
  budget: number;
  daily_budget: number;
  status: string;
  target_sentiments: string[];
  target_categories: string[];
  target_newspapers: string[];
  exclude_negative: boolean;
  min_sentiment_score: number;
  max_sentiment_score: number;
  start_date?: string;
  end_date?: string;
}

interface Ad {
  id: number;
  campaign_id: number;
  title: string;
  description?: string;
  image_url?: string;
  click_url: string;
  display_text?: string;
  ad_type: string;
  width: number;
  height: number;
  weight: number;
  is_active: boolean;
}

interface AdAnalytics {
  by_sentiment: Record<string, {
    impressions: number;
    clicks: number;
    conversions: number;
    ctr: number;
  }>;
  totals: {
    impressions: number;
    clicks: number;
    conversions: number;
    ctr: number;
  };
  period_days: number;
}

const AdsManagement: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  
  // Campañas
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [campaignDialogOpen, setCampaignDialogOpen] = useState(false);
  const [editingCampaign, setEditingCampaign] = useState<Campaign | null>(null);
  const [campaignForm, setCampaignForm] = useState<Partial<Campaign>>({
    name: '',
    description: '',
    advertiser_name: '',
    budget: 0,
    daily_budget: 0,
    status: 'active',
    target_sentiments: ['all'],
    target_categories: [],
    target_newspapers: [],
    exclude_negative: true,
    min_sentiment_score: -1.0,
    max_sentiment_score: 1.0,
  });
  
  // Anuncios
  const [ads, setAds] = useState<Ad[]>([]);
  const [adDialogOpen, setAdDialogOpen] = useState(false);
  const [editingAd, setEditingAd] = useState<Ad | null>(null);
  const [adForm, setAdForm] = useState<Partial<Ad>>({
    campaign_id: 0,
    title: '',
    description: '',
    image_url: '',
    click_url: '',
    display_text: '',
    ad_type: 'banner',
    width: 300,
    height: 250,
    weight: 1,
    is_active: true,
  });
  
  // Analytics
  const [analytics, setAnalytics] = useState<AdAnalytics | null>(null);
  const [selectedCampaignForAnalytics, setSelectedCampaignForAnalytics] = useState<number | null>(null);
  const [recommendations, setRecommendations] = useState<any>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      await Promise.all([
        fetchCampaigns(),
        fetchRecommendations(),
      ]);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Error cargando datos');
    } finally {
      setLoading(false);
    }
  };

  const fetchCampaigns = async () => {
    try {
      const response = await api.get('/ads/campaigns');
      const data = response.data as { campaigns?: Campaign[] };
      setCampaigns(data.campaigns || []);
      
      // Si hay campañas, cargar anuncios de la primera
      if (data.campaigns && data.campaigns.length > 0) {
        fetchAds(data.campaigns[0].id);
      }
    } catch (err: any) {
      console.error('Error cargando campañas:', err);
    }
  };

  const fetchAds = async (campaignId: number) => {
    try {
      const response = await api.get(`/ads?campaign_id=${campaignId}`);
      const data = response.data as { ads?: Ad[] };
      setAds(data.ads || []);
    } catch (err: any) {
      console.error('Error cargando anuncios:', err);
      setAds([]);
    }
  };

  const fetchRecommendations = async () => {
    try {
      const response = await api.get('/ads/recommendations?days=7');
      setRecommendations(response.data as any);
    } catch (err: any) {
      console.error('Error cargando recomendaciones:', err);
    }
  };

  const fetchAnalytics = async (campaignId?: number) => {
    try {
      const params = campaignId ? `?campaign_id=${campaignId}&days=30` : '?days=30';
      const response = await api.get(`/ads/analytics${params}`);
      setAnalytics(response.data as AdAnalytics);
    } catch (err: any) {
      console.error('Error cargando analytics:', err);
    }
  };

  const handleCreateCampaign = async () => {
    try {
      await api.post('/ads/campaigns', campaignForm);
      setCampaignDialogOpen(false);
      resetCampaignForm();
      fetchCampaigns();
    } catch (err: any) {
      setError(err.response?.data?.error || 'Error creando campaña');
    }
  };

  const handleCreateAd = async () => {
    try {
      await api.post('/ads', adForm);
      setAdDialogOpen(false);
      resetAdForm();
      if (adForm.campaign_id) {
        fetchAds(adForm.campaign_id);
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Error creando anuncio');
    }
  };

  const resetCampaignForm = () => {
    setCampaignForm({
      name: '',
      description: '',
      advertiser_name: '',
      budget: 0,
      daily_budget: 0,
      status: 'active',
      target_sentiments: ['all'],
      target_categories: [],
      target_newspapers: [],
      exclude_negative: true,
      min_sentiment_score: -1.0,
      max_sentiment_score: 1.0,
    });
    setEditingCampaign(null);
  };

  const resetAdForm = () => {
    setAdForm({
      campaign_id: campaigns[0]?.id || 0,
      title: '',
      description: '',
      image_url: '',
      click_url: '',
      display_text: '',
      ad_type: 'banner',
      width: 300,
      height: 250,
      weight: 1,
      is_active: true,
    });
    setEditingAd(null);
  };

  const buildAnalyticsChart = () => {
    if (!analytics || !analytics.by_sentiment) return {};
    
    const sentiments = Object.keys(analytics.by_sentiment);
    const impressions = sentiments.map(s => analytics.by_sentiment[s].impressions);
    const clicks = sentiments.map(s => analytics.by_sentiment[s].clicks);
    
    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        }
      },
      legend: {
        data: ['Impresiones', 'Clicks']
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: sentiments.map(s => s === 'positive' ? 'Positivo' : s === 'negative' ? 'Negativo' : 'Neutral')
      },
      yAxis: {
        type: 'value'
      },
      series: [
        {
          name: 'Impresiones',
          type: 'bar',
          data: impressions,
          itemStyle: { color: '#3b82f6' }
        },
        {
          name: 'Clicks',
          type: 'bar',
          data: clicks,
          itemStyle: { color: '#10b981' }
        }
      ]
    };
  };

  const buildCTRChart = () => {
    if (!analytics || !analytics.by_sentiment) return {};
    
    const sentiments = Object.keys(analytics.by_sentiment);
    const ctrs = sentiments.map(s => analytics.by_sentiment[s].ctr);
    
    return {
      tooltip: {
        trigger: 'item'
      },
      series: [
        {
          type: 'pie',
          radius: '60%',
          data: sentiments.map((s, i) => ({
            value: ctrs[i],
            name: s === 'positive' ? 'Positivo' : s === 'negative' ? 'Negativo' : 'Neutral',
            itemStyle: {
              color: s === 'positive' ? '#10b981' : s === 'negative' ? '#ef4444' : '#f59e0b'
            }
          }))
        }
      ]
    };
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
        <Typography variant="h4" component="h1">
          Gestión de Anuncios
        </Typography>
        <IconButton onClick={fetchData} color="primary">
          <RefreshIcon />
        </IconButton>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Recomendaciones */}
      {recommendations && (
        <Card sx={{ mb: 3, bgcolor: 'info.light' }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              📊 Recomendaciones de Colocación
            </Typography>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, md: 4 }}>
                <Typography variant="body2" color="text.secondary">
                  Contenido Positivo
                </Typography>
                <Typography variant="h5">
                  {recommendations.summary?.positive_pct || 0}%
                </Typography>
              </Grid>
              <Grid size={{ xs: 12, md: 4 }}>
                <Typography variant="body2" color="text.secondary">
                  Contenido Negativo
                </Typography>
                <Typography variant="h5">
                  {recommendations.summary?.negative_pct || 0}%
                </Typography>
              </Grid>
              <Grid size={{ xs: 12, md: 4 }}>
                <Typography variant="body2" color="text.secondary">
                  Contenido Neutral
                </Typography>
                <Typography variant="h5">
                  {recommendations.summary?.neutral_pct || 0}%
                </Typography>
              </Grid>
            </Grid>
            {recommendations.best_categories && recommendations.best_categories.length > 0 && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Mejores Categorías:
                </Typography>
                {recommendations.best_categories.slice(0, 3).map(([cat, count, pct]: any) => (
                  <Chip
                    key={cat}
                    label={`${cat}: ${pct.toFixed(1)}% positivo`}
                    sx={{ mr: 1, mb: 1 }}
                    color="success"
                    size="small"
                  />
                ))}
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
          <Tab icon={<CampaignIcon />} label="Campañas" />
          <Tab icon={<AddIcon />} label="Anuncios" />
          <Tab icon={<AnalyticsIcon />} label="Analytics" />
        </Tabs>
      </Paper>

      {/* Tab: Campañas */}
      {tabValue === 0 && (
        <Box>
          <Box sx={{ mb: 2, display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => {
                resetCampaignForm();
                setCampaignDialogOpen(true);
              }}
            >
              Nueva Campaña
            </Button>
          </Box>

          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Nombre</TableCell>
                  <TableCell>Anunciante</TableCell>
                  <TableCell>Presupuesto</TableCell>
                  <TableCell>Sentimientos</TableCell>
                  <TableCell>Estado</TableCell>
                  <TableCell>Acciones</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {campaigns.map((campaign) => (
                  <TableRow key={campaign.id}>
                    <TableCell>{campaign.name}</TableCell>
                    <TableCell>{campaign.advertiser_name || '-'}</TableCell>
                    <TableCell>${campaign.budget.toFixed(2)}</TableCell>
                    <TableCell>
                      {campaign.target_sentiments.includes('all') ? (
                        <Chip label="Todos" size="small" />
                      ) : (
                        campaign.target_sentiments.map(s => (
                          <Chip
                            key={s}
                            label={s === 'positive' ? 'Positivo' : s === 'negative' ? 'Negativo' : 'Neutral'}
                            size="small"
                            sx={{ mr: 0.5 }}
                            color={s === 'positive' ? 'success' : s === 'negative' ? 'error' : 'warning'}
                          />
                        ))
                      )}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={campaign.status}
                        size="small"
                        color={campaign.status === 'active' ? 'success' : 'default'}
                      />
                    </TableCell>
                    <TableCell>
                      <IconButton
                        size="small"
                        onClick={() => {
                          setSelectedCampaignForAnalytics(campaign.id);
                          fetchAnalytics(campaign.id);
                          setTabValue(2);
                        }}
                      >
                        <AnalyticsIcon fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
                {campaigns.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={6} align="center">
                      No hay campañas. Crea una nueva para comenzar.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )}

      {/* Tab: Anuncios */}
      {tabValue === 1 && (
        <Box>
          <Box sx={{ mb: 2, display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => {
                resetAdForm();
                setAdDialogOpen(true);
              }}
            >
              Nuevo Anuncio
            </Button>
          </Box>

          <Alert severity="info" sx={{ mb: 2 }}>
            Selecciona una campaña para ver sus anuncios. Los anuncios se mostrarán automáticamente
            en artículos que coincidan con los criterios de sentimiento de la campaña.
          </Alert>

          <Box sx={{ mb: 2 }}>
            <FormControl sx={{ minWidth: 200 }}>
              <InputLabel>Filtrar por Campaña</InputLabel>
              <Select
                value={adForm.campaign_id || ''}
                onChange={(e) => {
                  const campaignId = e.target.value as number;
                  setAdForm({ ...adForm, campaign_id: campaignId });
                  if (campaignId) {
                    fetchAds(campaignId);
                  } else {
                    setAds([]);
                  }
                }}
                label="Filtrar por Campaña"
              >
                <MenuItem value="">Todas las campañas</MenuItem>
                {campaigns.map(c => (
                  <MenuItem key={c.id} value={c.id}>{c.name}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>

          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Título</TableCell>
                  <TableCell>Tipo</TableCell>
                  <TableCell>Tamaño</TableCell>
                  <TableCell>Peso</TableCell>
                  <TableCell>Estado</TableCell>
                  <TableCell>Acciones</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {ads.map((ad) => (
                  <TableRow key={ad.id}>
                    <TableCell>{ad.title}</TableCell>
                    <TableCell>
                      <Chip label={ad.ad_type} size="small" />
                    </TableCell>
                    <TableCell>{ad.width}x{ad.height}px</TableCell>
                    <TableCell>{ad.weight}</TableCell>
                    <TableCell>
                      <Chip
                        label={ad.is_active ? 'Activo' : 'Inactivo'}
                        size="small"
                        color={ad.is_active ? 'success' : 'default'}
                      />
                    </TableCell>
                    <TableCell>
                      <IconButton
                        size="small"
                        onClick={() => {
                          setEditingAd(ad);
                          setAdForm(ad);
                          setAdDialogOpen(true);
                        }}
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
                {ads.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={6} align="center">
                      {adForm.campaign_id ? 
                        'No hay anuncios en esta campaña. Crea uno nuevo.' :
                        'Selecciona una campaña para ver sus anuncios o crea uno nuevo.'}
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )}

      {/* Tab: Analytics */}
      {tabValue === 2 && (
        <Box>
          <Box sx={{ mb: 2 }}>
            <FormControl sx={{ minWidth: 200 }}>
              <InputLabel>Campaña</InputLabel>
              <Select
                value={selectedCampaignForAnalytics || ''}
                onChange={(e) => {
                  const campaignId = e.target.value as number;
                  setSelectedCampaignForAnalytics(campaignId || null);
                  fetchAnalytics(campaignId || undefined);
                }}
                label="Campaña"
              >
                <MenuItem value="">Todas las campañas</MenuItem>
                {campaigns.map(c => (
                  <MenuItem key={c.id} value={c.id}>{c.name}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>

          {analytics && (
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 4 }}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Total Impresiones
                    </Typography>
                    <Typography variant="h4">
                      {analytics.totals.impressions.toLocaleString()}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid size={{ xs: 12, md: 4 }}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Total Clicks
                    </Typography>
                    <Typography variant="h4">
                      {analytics.totals.clicks.toLocaleString()}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid size={{ xs: 12, md: 4 }}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      CTR Promedio
                    </Typography>
                    <Typography variant="h4">
                      {analytics.totals.ctr.toFixed(2)}%
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Impresiones y Clicks por Sentimiento
                    </Typography>
                    <ReactECharts option={buildAnalyticsChart()} style={{ height: '300px' }} />
                  </CardContent>
                </Card>
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      CTR por Sentimiento
                    </Typography>
                    <ReactECharts option={buildCTRChart()} style={{ height: '300px' }} />
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}
        </Box>
      )}

      {/* Dialog: Crear/Editar Campaña */}
      <Dialog open={campaignDialogOpen} onClose={() => setCampaignDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingCampaign ? 'Editar Campaña' : 'Nueva Campaña'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                label="Nombre de la Campaña"
                value={campaignForm.name}
                onChange={(e) => setCampaignForm({ ...campaignForm, name: e.target.value })}
                required
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                label="Descripción"
                value={campaignForm.description}
                onChange={(e) => setCampaignForm({ ...campaignForm, description: e.target.value })}
                multiline
                rows={3}
              />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                label="Anunciante"
                value={campaignForm.advertiser_name}
                onChange={(e) => setCampaignForm({ ...campaignForm, advertiser_name: e.target.value })}
              />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                label="Presupuesto Total"
                type="number"
                value={campaignForm.budget}
                onChange={(e) => setCampaignForm({ ...campaignForm, budget: parseFloat(e.target.value) || 0 })}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormControl fullWidth>
                <InputLabel>Sentimientos Objetivo</InputLabel>
                <Select
                  multiple
                  value={campaignForm.target_sentiments || []}
                  onChange={(e) => setCampaignForm({ ...campaignForm, target_sentiments: e.target.value as string[] })}
                  label="Sentimientos Objetivo"
                >
                  <MenuItem value="all">Todos</MenuItem>
                  <MenuItem value="positive">Positivo</MenuItem>
                  <MenuItem value="neutral">Neutral</MenuItem>
                  <MenuItem value="negative">Negativo</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={campaignForm.exclude_negative || false}
                    onChange={(e) => setCampaignForm({ ...campaignForm, exclude_negative: e.target.checked })}
                  />
                }
                label="Excluir contenido muy negativo"
              />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                label="Score Mínimo"
                type="number"
                inputProps={{ step: 0.1, min: -1, max: 1 }}
                value={campaignForm.min_sentiment_score}
                onChange={(e) => setCampaignForm({ ...campaignForm, min_sentiment_score: parseFloat(e.target.value) || -1 })}
              />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                label="Score Máximo"
                type="number"
                inputProps={{ step: 0.1, min: -1, max: 1 }}
                value={campaignForm.max_sentiment_score}
                onChange={(e) => setCampaignForm({ ...campaignForm, max_sentiment_score: parseFloat(e.target.value) || 1 })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCampaignDialogOpen(false)}>Cancelar</Button>
          <Button onClick={handleCreateCampaign} variant="contained">
            {editingCampaign ? 'Guardar' : 'Crear'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog: Crear/Editar Anuncio */}
      <Dialog open={adDialogOpen} onClose={() => setAdDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingAd ? 'Editar Anuncio' : 'Nuevo Anuncio'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid size={{ xs: 12 }}>
              <FormControl fullWidth>
                <InputLabel>Campaña</InputLabel>
                <Select
                  value={adForm.campaign_id || ''}
                  onChange={(e) => setAdForm({ ...adForm, campaign_id: e.target.value as number })}
                  label="Campaña"
                  required
                >
                  {campaigns.map(c => (
                    <MenuItem key={c.id} value={c.id}>{c.name}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                label="Título"
                value={adForm.title}
                onChange={(e) => setAdForm({ ...adForm, title: e.target.value })}
                required
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                label="URL de Click"
                value={adForm.click_url}
                onChange={(e) => setAdForm({ ...adForm, click_url: e.target.value })}
                required
                placeholder="https://..."
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                label="URL de Imagen"
                value={adForm.image_url}
                onChange={(e) => setAdForm({ ...adForm, image_url: e.target.value })}
                placeholder="https://..."
              />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                label="Ancho (px)"
                type="number"
                value={adForm.width}
                onChange={(e) => setAdForm({ ...adForm, width: parseInt(e.target.value) || 300 })}
              />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                label="Alto (px)"
                type="number"
                value={adForm.height}
                onChange={(e) => setAdForm({ ...adForm, height: parseInt(e.target.value) || 250 })}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormControl fullWidth>
                <InputLabel>Tipo de Anuncio</InputLabel>
                <Select
                  value={adForm.ad_type}
                  onChange={(e) => setAdForm({ ...adForm, ad_type: e.target.value })}
                  label="Tipo de Anuncio"
                >
                  <MenuItem value="banner">Banner</MenuItem>
                  <MenuItem value="sidebar">Sidebar</MenuItem>
                  <MenuItem value="inline">Inline</MenuItem>
                  <MenuItem value="popup">Popup</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={adForm.is_active || false}
                    onChange={(e) => setAdForm({ ...adForm, is_active: e.target.checked })}
                  />
                }
                label="Activo"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAdDialogOpen(false)}>Cancelar</Button>
          <Button onClick={handleCreateAd} variant="contained">
            {editingAd ? 'Guardar' : 'Crear'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AdsManagement;

