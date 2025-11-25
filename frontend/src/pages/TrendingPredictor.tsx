import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Chip,
  Alert,
  CircularProgress,
  LinearProgress,
  Paper,
  Badge,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  Psychology as PsychologyIcon,
  Schedule as ScheduleIcon,
  Timeline as TimelineIcon,
  Category as CategoryIcon,
  Source as SourceIcon,
  AutoAwesome as AutoAwesomeIcon,
} from '@mui/icons-material';
import apiService from '../services/api';

interface Prediction {
  topic: string;
  confidence_score: number;
  viral_potential: number;
  time_to_trend_hours: number;
  keywords: string[];
  sources: string[];
  category: string;
  trending_probability: number;
  growth_rate: number;
  momentum: number;
  created_at?: string;
}

interface UsageInfo {
  used: number;
  limit: number;
  remaining: number;
  plan_type: string;
}

const TrendingPredictor: React.FC = () => {
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [usage, setUsage] = useState<UsageInfo>({ used: 0, limit: 5, remaining: 5, plan_type: 'creator' });
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      // Cargar predicciones existentes
      const predictionsResponse = await apiService.getUserPredictions() as any;
      if (predictionsResponse.success) {
        setPredictions(predictionsResponse.predictions);
      }

      // Cargar información de uso
      const usageResponse = await apiService.getDailyUsage() as any;
      if (usageResponse.success) {
        setUsage(usageResponse);
      }
    } catch (err) {
      console.error('Error loading data:', err);
      setError('Error cargando datos');
    } finally {
      setLoading(false);
    }
  };

  const generatePredictions = async () => {
    if (usage.remaining <= 0) {
      setError('Has alcanzado el límite diario de predicciones. ¡Actualiza tu plan!');
      return;
    }

    setGenerating(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await apiService.generateTrendingPredictions(10) as any;
      
      console.log('Response from API:', response);
      
      if (response && response.success) {
        setPredictions(response.predictions || []);
        setSuccess(`🔮 ¡${response.total_generated || 0} predicciones generadas exitosamente!`);
        setError(null);
        
        // Recargar información de uso
        try {
          const usageResponse = await apiService.getDailyUsage() as any;
          if (usageResponse && usageResponse.success) {
            setUsage(usageResponse);
          }
        } catch (usageErr) {
          console.warn('Error loading usage:', usageErr);
        }
      } else {
        const errorMsg = response?.error || response?.details || 'Error generando predicciones';
        if (response?.upgrade_required) {
          setError('Límite diario alcanzado. ¡Actualiza tu plan para más predicciones!');
        } else {
          setError(errorMsg);
        }
        setSuccess(null);
      }
    } catch (err: any) {
      console.error('Error generating predictions:', err);
      const errorMsg = err?.response?.data?.error || err?.response?.data?.details || err?.message || 'Error generando predicciones';
      setError(errorMsg);
      setSuccess(null);
    } finally {
      setGenerating(false);
    }
  };

  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return 'success';
    if (score >= 0.6) return 'warning';
    return 'error';
  };

  const getViralPotentialColor = (potential: number) => {
    if (potential >= 0.8) return '#ff6b6b';
    if (potential >= 0.6) return '#ffa726';
    if (potential >= 0.4) return '#66bb6a';
    return '#42a5f5';
  };

  const formatTimeToTrend = (hours: number) => {
    if (hours < 24) {
      return `${Math.round(hours)} horas`;
    } else {
      const days = Math.round(hours / 24);
      return `${days} día${days > 1 ? 's' : ''}`;
    }
  };

  const getPlanDisplayName = (planType: string) => {
    const plans = {
      'creator': 'Creator',
      'influencer': 'Influencer', 
      'media_company': 'Media Company'
    };
    return plans[planType as keyof typeof plans] || 'Creator';
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
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <PsychologyIcon sx={{ fontSize: 40, color: 'primary.main' }} />
          🔮 Trending Topics Predictor
        </Typography>
        <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 2 }}>
          Ve el futuro de las noticias - Predice qué temas serán virales en las próximas 24-48 horas
        </Typography>
        
        {/* Usage Info */}
        <Paper sx={{ p: 2, mb: 3, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box>
              <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Badge badgeContent={getPlanDisplayName(usage.plan_type)} color="secondary">
                  <TimelineIcon />
                </Badge>
                Límites del Plan
              </Typography>
              <Typography variant="body2" sx={{ opacity: 0.9 }}>
                {usage.used} de {usage.limit} predicciones utilizadas hoy
              </Typography>
            </Box>
            <Box sx={{ minWidth: 200 }}>
              <LinearProgress 
                variant="determinate" 
                value={(usage.used / usage.limit) * 100} 
                sx={{ 
                  height: 8, 
                  borderRadius: 4,
                  backgroundColor: 'rgba(255,255,255,0.3)',
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: usage.remaining > 0 ? '#4caf50' : '#f44336'
                  }
                }} 
              />
              <Typography variant="body2" sx={{ mt: 1, textAlign: 'center' }}>
                {usage.remaining} restantes
              </Typography>
            </Box>
          </Box>
        </Paper>
      </Box>

      {/* Error/Success Messages */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      {/* Generate Button */}
      <Box sx={{ mb: 4, textAlign: 'center' }}>
        <Button
          variant="contained"
          size="large"
          startIcon={generating ? <CircularProgress size={20} /> : <AutoAwesomeIcon />}
          onClick={generatePredictions}
          disabled={generating || usage.remaining <= 0}
          sx={{
            px: 4,
            py: 2,
            fontSize: '1.1rem',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            '&:hover': {
              background: 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)',
            }
          }}
        >
          {generating ? 'Generando Predicciones...' : '🔮 Generar Predicciones'}
        </Button>
        
        {usage.remaining <= 0 && (
          <Typography variant="body2" color="error" sx={{ mt: 2 }}>
            ¡Actualiza tu plan para más predicciones!
          </Typography>
        )}
      </Box>

      {/* Predictions Grid */}
      {predictions.length > 0 && (
        <Box>
          <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <TrendingUpIcon />
            Predicciones Generadas
          </Typography>
          
          <Box 
            sx={{ 
              display: 'grid',
              gridTemplateColumns: {
                xs: '1fr',
                md: 'repeat(2, 1fr)',
                lg: 'repeat(3, 1fr)'
              },
              gap: 3
            }}
          >
            {predictions.map((prediction, index) => (
                <Card 
                  sx={{ 
                    height: '100%',
                    background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
                    border: '1px solid #e0e0e0',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: '0 8px 25px rgba(0,0,0,0.15)',
                      transition: 'all 0.3s ease'
                    }
                  }}
                >
                  <CardContent>
                    {/* Topic Header */}
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="h6" component="h3" gutterBottom sx={{ fontWeight: 'bold' }}>
                        {prediction.topic}
                      </Typography>
                      <Chip 
                        label={prediction.category} 
                        size="small" 
                        color="primary" 
                        icon={<CategoryIcon />}
                        sx={{ mb: 1 }}
                      />
                    </Box>

                    {/* Confidence & Viral Potential */}
                    <Box sx={{ mb: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="body2" color="text.secondary">
                          Confianza:
                        </Typography>
                        <Typography variant="body2" fontWeight="bold" color={`${getConfidenceColor(prediction.confidence_score)}.main`}>
                          {Math.round(prediction.confidence_score * 100)}%
                        </Typography>
                      </Box>
                      <LinearProgress 
                        variant="determinate" 
                        value={prediction.confidence_score * 100}
                        color={getConfidenceColor(prediction.confidence_score)}
                        sx={{ height: 6, borderRadius: 3 }}
                      />
                    </Box>

                    {/* Viral Potential */}
                    <Box sx={{ mb: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="body2" color="text.secondary">
                          Potencial Viral:
                        </Typography>
                        <Typography variant="body2" fontWeight="bold" sx={{ color: getViralPotentialColor(prediction.viral_potential) }}>
                          {Math.round(prediction.viral_potential * 100)}%
                        </Typography>
                      </Box>
                      <LinearProgress 
                        variant="determinate" 
                        value={prediction.viral_potential * 100}
                        sx={{ 
                          height: 6, 
                          borderRadius: 3,
                          backgroundColor: 'rgba(0,0,0,0.1)',
                          '& .MuiLinearProgress-bar': {
                            backgroundColor: getViralPotentialColor(prediction.viral_potential)
                          }
                        }}
                      />
                    </Box>

                    {/* Time to Trend */}
                    <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                      <ScheduleIcon color="primary" />
                      <Typography variant="body2">
                        <strong>Tiempo estimado:</strong> {formatTimeToTrend(prediction.time_to_trend_hours)}
                      </Typography>
                    </Box>

                    {/* Keywords */}
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Palabras Clave:
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {prediction.keywords.slice(0, 4).map((keyword, idx) => (
                          <Chip 
                            key={idx} 
                            label={keyword} 
                            size="small" 
                            variant="outlined"
                            sx={{ fontSize: '0.75rem' }}
                          />
                        ))}
                        {prediction.keywords.length > 4 && (
                          <Chip 
                            label={`+${prediction.keywords.length - 4}`} 
                            size="small" 
                            variant="outlined"
                            sx={{ fontSize: '0.75rem' }}
                          />
                        )}
                      </Box>
                    </Box>

                    {/* Sources */}
                    <Box>
                      <Typography variant="body2" color="text.secondary" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <SourceIcon fontSize="small" />
                        Fuentes:
                      </Typography>
                      <Typography variant="body2" sx={{ fontSize: '0.85rem' }}>
                        {prediction.sources.join(', ')}
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
            ))}
          </Box>
        </Box>
      )}

      {/* Empty State */}
      {predictions.length === 0 && !generating && (
        <Paper sx={{ p: 6, textAlign: 'center', background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)' }}>
          <PsychologyIcon sx={{ fontSize: 80, color: 'primary.main', mb: 2 }} />
          <Typography variant="h5" gutterBottom>
            🔮 ¡Descubre el Futuro de las Noticias!
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            Genera predicciones inteligentes de trending topics y sé el primero en crear contenido viral
          </Typography>
          <Button
            variant="contained"
            size="large"
            startIcon={<AutoAwesomeIcon />}
            onClick={generatePredictions}
            disabled={usage.remaining <= 0}
            sx={{
              px: 4,
              py: 2,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              '&:hover': {
                background: 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)',
              }
            }}
          >
            Generar Primera Predicción
          </Button>
        </Paper>
      )}
    </Box>
  );
};

export default TrendingPredictor;
