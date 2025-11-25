import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Chip,
  Alert,
  CircularProgress,
  IconButton,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Badge,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  RadioGroup,
  FormControlLabel,
  Radio,
  FormLabel,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  TrendingFlat as TrendingFlatIcon,
  Notifications as NotificationsIcon,
  Business as BusinessIcon,
  Close as CloseIcon,
  Refresh as RefreshIcon,
  AutoAwesome as AutoAwesomeIcon,
} from '@mui/icons-material';
import apiService from '../services/api';

interface Competitor {
  id: number;
  name: string;
  keywords: string[];
  domains: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface CompetitorAnalytics {
  total_mentions: number;
  avg_sentiment: number;
  positive_mentions: number;
  negative_mentions: number;
  neutral_mentions: number;
  sentiment_trend: Array<{
    date: string;
    sentiment: number;
    mentions: number;
  }>;
}

interface AlertItem {
  id: number;
  type: string;
  message: string;
  data: any;
  created_at: string;
  competitor_name: string;
}

interface Limits {
  current_competitors: number;
  max_competitors: number;
  remaining: number;
}

const CompetitiveIntelligence: React.FC = () => {
  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  const [analytics, setAnalytics] = useState<Record<string, CompetitorAnalytics>>({});
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [limits, setLimits] = useState<Limits>({ current_competitors: 0, max_competitors: 1, remaining: 1 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [autoDetecting, setAutoDetecting] = useState(false);
  
  // Dialog states
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [newCompetitor, setNewCompetitor] = useState({
    name: '',
    keywords: '',
    domains: ''
  });
  const [availableNewspapers, setAvailableNewspapers] = useState<string[]>([]);
  const [competitorType, setCompetitorType] = useState<'newspaper' | 'external'>('newspaper');
  
  // AI Suggestions states
  const [aiSuggestions, setAiSuggestions] = useState<any[]>([]);
  const [aiLoading, setAiLoading] = useState(false);
  const [showAISuggestions, setShowAISuggestions] = useState(false);
  const [selectedSuggestions, setSelectedSuggestions] = useState<string[]>([]);
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [competitorsRes, analyticsRes, alertsRes, limitsRes, newspapersRes] = await Promise.all([
        apiService.getCompetitors(),
        apiService.getCompetitiveAnalytics(30),
        apiService.getCompetitiveAlerts(true),
        apiService.getCompetitiveLimits(),
        apiService.getAvailableNewspapers()
      ]) as [any, any, any, any, any];

      if (competitorsRes.success) {
        setCompetitors(competitorsRes.competitors);
      }

      if (analyticsRes.success) {
        setAnalytics(analyticsRes.analytics);
      }

      if (alertsRes.success) {
        setAlerts(alertsRes.alerts);
      }

      if (limitsRes.success) {
        setLimits(limitsRes as Limits);
      }

      if (newspapersRes.success) {
        setAvailableNewspapers(newspapersRes.newspapers);
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Error cargando datos');
    } finally {
      setLoading(false);
    }
  };

  const handleAddCompetitor = async () => {
    try {
      if (!newCompetitor.name.trim() || !newCompetitor.keywords.trim()) {
        setError('Nombre y palabras clave son requeridos');
        return;
      }

      const keywords = newCompetitor.keywords.split(',').map(k => k.trim()).filter(k => k);
      const domains = newCompetitor.domains.split(',').map(d => d.trim()).filter(d => d);

      const response = await apiService.addCompetitor({
        name: newCompetitor.name.trim(),
        keywords,
        domains
      }) as any;

      if (response.success) {
        setAddDialogOpen(false);
        resetForm();
        loadData();
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Error agregando competidor');
    }
  };

  const resetForm = () => {
    setNewCompetitor({ name: '', keywords: '', domains: '' });
    setCompetitorType('newspaper');
    setAiSuggestions([]);
    setSelectedSuggestions([]);
    setShowAISuggestions(false);
    setError(null);
    setSuccess(null);
    setAutoDetecting(false);
  };

  // AI Suggestions functions
  const getAISuggestions = async () => {
    if (!newCompetitor.name.trim()) {
      setError('Ingresa el nombre del competidor primero');
      return;
    }

    setAiLoading(true);
    try {
      const response = await apiService.getAISuggestions(
        newCompetitor.name,
        newCompetitor.keywords.split(',').map(k => k.trim()).filter(k => k)
      ) as any;

      if (response.success) {
        setAiSuggestions(response.suggestions || []);
        setShowAISuggestions(true);
        setError(null);
      } else {
        setError('Error obteniendo sugerencias de IA');
      }
    } catch (err) {
      console.error('Error getting AI suggestions:', err);
      setError('Error obteniendo sugerencias de IA');
    } finally {
      setAiLoading(false);
    }
  };

  const toggleSuggestion = (keyword: string) => {
    setSelectedSuggestions(prev => 
      prev.includes(keyword) 
        ? prev.filter(k => k !== keyword)
        : [...prev, keyword]
    );
  };

  const applySelectedSuggestions = () => {
    const currentKeywords = newCompetitor.keywords.split(',').map(k => k.trim()).filter(k => k);
    const newKeywords = [...currentKeywords, ...selectedSuggestions];
    setNewCompetitor(prev => ({
      ...prev,
      keywords: newKeywords.join(', ')
    }));
    setShowAISuggestions(false);
    setSelectedSuggestions([]);
  };

  const analyzeArticles = async () => {
    setAnalyzing(true);
    try {
      const response = await apiService.analyzeExistingArticles() as any;
      if (response.success) {
        setSuccess(`✅ ${response.message}`);
        loadData(); // Recargar datos para mostrar los resultados
      } else {
        setError('Error analizando artículos');
      }
    } catch (err) {
      console.error('Error analyzing articles:', err);
      setError('Error analizando artículos');
    } finally {
      setAnalyzing(false);
    }
  };

  const autoDetectCompetitor = async () => {
    if (!newCompetitor.name.trim()) {
      setError('Por favor ingresa el nombre del competidor');
      return;
    }

    setAutoDetecting(true);
    try {
      const response = await apiService.autoDetectCompetitor(newCompetitor.name) as any;
      if (response.success) {
        // Auto-llenar los campos con los datos detectados
        setNewCompetitor(prev => ({
          ...prev,
          domains: response.domain,
          keywords: response.keywords.join(', ')
        }));
        
        setSuccess(`🎯 Auto-detección exitosa: ${response.source} (${response.confidence})`);
        
        if (response.newspaper_found) {
          setSuccess(prev => `${prev} - Periódico encontrado: ${response.newspaper_found}`);
        }
      } else {
        setError('Error en la auto-detección');
      }
    } catch (err) {
      console.error('Error auto-detecting competitor:', err);
      setError('Error en la auto-detección');
    } finally {
      setAutoDetecting(false);
    }
  };

  const handleDeleteCompetitor = async (competitorId: number) => {
    try {
      const response = await apiService.deleteCompetitor(competitorId) as any;
      if (response.success) {
        loadData();
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Error eliminando competidor');
    }
  };

  const handleMarkAlertRead = async (alertId: number) => {
    try {
      await apiService.markAlertRead(alertId);
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.error || 'Error marcando alerta');
    }
  };

  const getSentimentIcon = (sentiment: number) => {
    if (sentiment > 0.1) return <TrendingUpIcon color="success" />;
    if (sentiment < -0.1) return <TrendingDownIcon color="error" />;
    return <TrendingFlatIcon color="action" />;
  };

  const getSentimentColor = (sentiment: number) => {
    if (sentiment > 0.1) return 'success';
    if (sentiment < -0.1) return 'error';
    return 'default';
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
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            🕵️ Competitive Intelligence
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Monitorea a tus competidores y descubre oportunidades de mercado
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={loadData}
          >
            Actualizar
          </Button>
          <Button
            variant="outlined"
            startIcon={analyzing ? <CircularProgress size={16} /> : <RefreshIcon />}
            onClick={analyzeArticles}
            disabled={analyzing || competitors.length === 0}
            color="secondary"
          >
            {analyzing ? 'Analizando...' : '🔍 Analizar'}
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setAddDialogOpen(true)}
            disabled={limits.remaining <= 0}
          >
            Agregar Competidor
          </Button>
        </Box>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Success Alert */}
      {success && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      {/* Limits Info */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <BusinessIcon color="primary" />
            <Box>
              <Typography variant="h6">
                Límites del Plan
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {limits.current_competitors} de {limits.max_competitors} competidores utilizados
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={(limits.current_competitors / limits.max_competitors) * 100}
                sx={{ mt: 1, width: 200 }}
              />
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Alerts Section */}
      {alerts.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <Badge badgeContent={alerts.length} color="error">
                <NotificationsIcon color="primary" />
              </Badge>
              <Typography variant="h6">
                Alertas Recientes
              </Typography>
            </Box>
            <List>
              {alerts.slice(0, 5).map((alert) => (
                <ListItem key={alert.id} divider>
                  <ListItemIcon>
                    <NotificationsIcon color="warning" />
                  </ListItemIcon>
                  <ListItemText
                    primary={alert.message}
                    secondary={`${alert.competitor_name} • ${new Date(alert.created_at).toLocaleString()}`}
                  />
                  <IconButton
                    size="small"
                    onClick={() => handleMarkAlertRead(alert.id)}
                  >
                    <CloseIcon />
                  </IconButton>
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      {/* Competitors Grid */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)', lg: 'repeat(3, 1fr)' }, gap: 3 }}>
        {competitors.map((competitor) => {
          const competitorAnalytics = analytics[competitor.name];
          
          return (
            <Box key={competitor.id}>
              <Card sx={{ height: '100%' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Typography variant="h6" component="h3">
                      {competitor.name}
                    </Typography>
                    <IconButton
                      size="small"
                      color="error"
                      onClick={() => handleDeleteCompetitor(competitor.id)}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Box>

                  {/* Keywords */}
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Palabras Clave:
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {competitor.keywords.map((keyword, index) => (
                        <Chip
                          key={index}
                          label={keyword}
                          size="small"
                          variant="outlined"
                        />
                      ))}
                    </Box>
                  </Box>

                  {/* Analytics */}
                  {competitorAnalytics && (
                    <Box>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Analytics (30 días):
                      </Typography>
                      
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Paper sx={{ p: 1, textAlign: 'center', flex: 1 }}>
                          <Typography variant="h6" color="primary">
                            {competitorAnalytics.total_mentions}
                          </Typography>
                          <Typography variant="caption">
                            Menciones
                          </Typography>
                        </Paper>
                        <Paper sx={{ p: 1, textAlign: 'center', flex: 1 }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5 }}>
                            {getSentimentIcon(competitorAnalytics.avg_sentiment)}
                            <Typography variant="h6" color={`${getSentimentColor(competitorAnalytics.avg_sentiment)}.main`}>
                              {competitorAnalytics.avg_sentiment.toFixed(2)}
                            </Typography>
                          </Box>
                          <Typography variant="caption">
                            Sentimiento
                          </Typography>
                        </Paper>
                      </Box>

                      <Box sx={{ mt: 1 }}>
                        <Typography variant="caption" color="text.secondary">
                          Positivas: {competitorAnalytics.positive_mentions} | 
                          Negativas: {competitorAnalytics.negative_mentions} | 
                          Neutrales: {competitorAnalytics.neutral_mentions}
                        </Typography>
                      </Box>
                    </Box>
                  )}

                  {!competitorAnalytics && (
                    <Typography variant="body2" color="text.secondary">
                      Sin datos de analytics aún
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Box>
          );
        })}
      </Box>

      {/* Empty State */}
      {competitors.length === 0 && (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 6 }}>
            <BusinessIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              No tienes competidores configurados
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Agrega competidores para comenzar a monitorear sus menciones en las noticias
            </Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setAddDialogOpen(true)}
              disabled={limits.remaining <= 0}
            >
              Agregar Primer Competidor
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Add Competitor Dialog */}
      <Dialog open={addDialogOpen} onClose={() => { setAddDialogOpen(false); resetForm(); }} maxWidth="sm" fullWidth>
        <DialogTitle>
          Agregar Nuevo Competidor
        </DialogTitle>
        <DialogContent>
          <FormControl component="fieldset" sx={{ mb: 3 }}>
            <FormLabel component="legend">Tipo de Competidor</FormLabel>
            <RadioGroup
              value={competitorType}
              onChange={(e) => setCompetitorType(e.target.value as 'newspaper' | 'external')}
              row
            >
              <FormControlLabel value="newspaper" control={<Radio />} label="Diario Existente" />
              <FormControlLabel value="external" control={<Radio />} label="Competidor Externo" />
            </RadioGroup>
          </FormControl>

          {competitorType === 'newspaper' ? (
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Seleccionar Diario</InputLabel>
              <Select
                value={newCompetitor.name}
                onChange={(e) => setNewCompetitor({ ...newCompetitor, name: e.target.value })}
                label="Seleccionar Diario"
              >
                {availableNewspapers.map((newspaper) => (
                  <MenuItem key={newspaper} value={newspaper}>
                    {newspaper}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          ) : (
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mb: 2 }}>
              <TextField
                autoFocus
                margin="dense"
                label="Nombre del Competidor"
                fullWidth
                variant="outlined"
                value={newCompetitor.name}
                onChange={(e) => setNewCompetitor({ ...newCompetitor, name: e.target.value })}
              />
              <Button
                variant="outlined"
                startIcon={autoDetecting ? <CircularProgress size={16} /> : <AutoAwesomeIcon />}
                onClick={autoDetectCompetitor}
                disabled={autoDetecting || !newCompetitor.name.trim()}
                sx={{ minWidth: 120 }}
                color="primary"
              >
                {autoDetecting ? 'Detectando...' : '🎯 Auto-detect'}
              </Button>
            </Box>
          )}
           <Box sx={{ mb: 2 }}>
             <TextField
               margin="dense"
               label="Palabras Clave (separadas por comas)"
               fullWidth
               variant="outlined"
               value={newCompetitor.keywords}
               onChange={(e) => setNewCompetitor({ ...newCompetitor, keywords: e.target.value })}
               placeholder="ej: coca cola, coca-cola, coca"
               sx={{ mb: 1 }}
             />
             <Button
               variant="outlined"
               startIcon={aiLoading ? <CircularProgress size={16} /> : <RefreshIcon />}
               onClick={getAISuggestions}
               disabled={aiLoading || !newCompetitor.name.trim()}
               sx={{ mb: 1 }}
             >
               🤖 Obtener Sugerencias de IA
             </Button>
           </Box>
          <TextField
            margin="dense"
            label="Dominios a Monitorear (opcional, separados por comas)"
            fullWidth
            variant="outlined"
            value={newCompetitor.domains}
            onChange={(e) => setNewCompetitor({ ...newCompetitor, domains: e.target.value })}
            placeholder="ej: cocacola.com, coca-cola.com"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => { setAddDialogOpen(false); resetForm(); }}>
            Cancelar
          </Button>
          <Button onClick={handleAddCompetitor} variant="contained">
            Agregar
          </Button>
         </DialogActions>
       </Dialog>

       {/* AI Suggestions Dialog */}
       <Dialog 
         open={showAISuggestions} 
         onClose={() => setShowAISuggestions(false)} 
         maxWidth="md" 
         fullWidth
       >
         <DialogTitle>
           🤖 Sugerencias de IA para "{newCompetitor.name}"
         </DialogTitle>
         <DialogContent>
           <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
             La IA ha analizado {aiSuggestions.length > 0 ? 'artículos existentes' : 'patrones generales'} 
             para sugerir palabras clave relevantes. Selecciona las que consideres útiles:
           </Typography>
           
           <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
             {aiSuggestions.map((suggestion, index) => (
               <Chip
                 key={index}
                 label={`${suggestion.keyword} (${Math.round(suggestion.final_relevance * 100)}%)`}
                 onClick={() => toggleSuggestion(suggestion.keyword)}
                 color={selectedSuggestions.includes(suggestion.keyword) ? 'primary' : 'default'}
                 variant={selectedSuggestions.includes(suggestion.keyword) ? 'filled' : 'outlined'}
                 sx={{ 
                   cursor: 'pointer',
                   '&:hover': { 
                     backgroundColor: selectedSuggestions.includes(suggestion.keyword) 
                       ? 'primary.dark' 
                       : 'action.hover' 
                   }
                 }}
               />
             ))}
           </Box>
           
           {selectedSuggestions.length > 0 && (
             <Alert severity="info" sx={{ mb: 2 }}>
               Has seleccionado {selectedSuggestions.length} sugerencias: {selectedSuggestions.join(', ')}
             </Alert>
           )}
         </DialogContent>
         <DialogActions>
           <Button onClick={() => setShowAISuggestions(false)}>
             Cancelar
           </Button>
           <Button 
             onClick={applySelectedSuggestions} 
             variant="contained"
             disabled={selectedSuggestions.length === 0}
           >
             Aplicar Seleccionadas ({selectedSuggestions.length})
           </Button>
         </DialogActions>
       </Dialog>
    </Box>
  );
};

export default CompetitiveIntelligence;
