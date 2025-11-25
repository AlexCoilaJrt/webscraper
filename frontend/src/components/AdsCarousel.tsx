import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardMedia,
  Typography,
  Button,
  Box,
  IconButton,
  Chip,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  NavigateBefore as NavigateBeforeIcon,
  NavigateNext as NavigateNextIcon,
  OpenInNew as OpenInNewIcon,
} from '@mui/icons-material';
import { api } from '../services/api';

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
  is_active?: boolean | number;
}

const AdsCarousel: React.FC = () => {
  const [ads, setAds] = useState<Ad[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [clickedAdId, setClickedAdId] = useState<number | null>(null);

  useEffect(() => {
    fetchAds();
  }, []);

  useEffect(() => {
    if (ads.length > 1) {
      const interval = setInterval(() => {
        setCurrentIndex((prevIndex) => (prevIndex + 1) % ads.length);
      }, 3000); // Cambiar cada 3 segundos

      return () => clearInterval(interval);
    }
  }, [ads.length]);

  const fetchAds = async () => {
    try {
      setLoading(true);
      const response = await api.get('/ads');
      const data = response.data as { ads?: Ad[] };
      // Filtrar solo anuncios activos (is_active puede ser boolean o 1/0)
      const activeAds = (data.ads || []).filter(ad => {
        // Si is_active es undefined, null, o true, está activo
        return ad.is_active !== false && ad.is_active !== 0;
      });
      setAds(activeAds);
    } catch (err: any) {
      console.error('Error cargando anuncios:', err);
      setError('Error cargando anuncios');
    } finally {
      setLoading(false);
    }
  };

  const handlePrevious = () => {
    setCurrentIndex((prevIndex) => (prevIndex - 1 + ads.length) % ads.length);
  };

  const handleNext = () => {
    setCurrentIndex((prevIndex) => (prevIndex + 1) % ads.length);
  };

  const handleAdClick = async (ad: Ad) => {
    try {
      // Registrar click
      await api.post('/ads/track', {
        ad_id: ad.id,
        event_type: 'click',
      });
      
      // Abrir URL en nueva pestaña
      window.open(ad.click_url, '_blank', 'noopener,noreferrer');
      setClickedAdId(ad.id);
      
      // Resetear después de 2 segundos
      setTimeout(() => setClickedAdId(null), 2000);
    } catch (err) {
      console.error('Error registrando click:', err);
      // Abrir URL de todas formas
      window.open(ad.click_url, '_blank', 'noopener,noreferrer');
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent>
          <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
            <CircularProgress />
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent>
          <Alert severity="error">{error}</Alert>
        </CardContent>
      </Card>
    );
  }

  if (ads.length === 0) {
    return null; // No mostrar nada si no hay anuncios
  }

  const currentAd = ads[currentIndex];
  
  // Obtener descripción (del anuncio o de la campaña, ya viene del backend)
  const description = currentAd?.description || currentAd?.display_text || '';

  return (
    <Card
      onClick={() => handleAdClick(currentAd)}
      sx={{
        position: 'relative',
        overflow: 'hidden',
        borderRadius: 3,
        boxShadow: 4,
        transition: 'all 0.3s ease',
        height: { xs: 400, md: 500 },
        maxWidth: { xs: '100%', md: 600 },
        mx: 'auto',
        cursor: 'pointer',
        '&:hover': {
          boxShadow: 8,
          transform: 'translateY(-4px)',
        },
      }}
    >
      {/* Imagen de fondo que cubre todo el card */}
      {currentAd.image_url ? (
        <CardMedia
          component="img"
          image={currentAd.image_url}
          alt={currentAd.title}
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            zIndex: 0,
          }}
        />
      ) : (
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            bgcolor: 'primary.main',
            background: 'linear-gradient(135deg, #0ea5e9 0%, #38bdf8 100%)',
            zIndex: 0,
          }}
        />
      )}

      {/* Overlay oscuro para mejor legibilidad del texto */}
      <Box
        sx={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          background: 'linear-gradient(to bottom, rgba(0,0,0,0.3) 0%, rgba(0,0,0,0.7) 100%)',
          zIndex: 1,
        }}
      />

      {/* Indicador de que es un anuncio */}
      <Box
        sx={{
          position: 'absolute',
          top: 12,
          right: 12,
          zIndex: 3,
        }}
      >
        <Chip
          label="Anuncio"
          size="small"
          sx={{
            bgcolor: 'rgba(0, 0, 0, 0.6)',
            color: 'white',
            fontSize: '0.7rem',
            fontWeight: 600,
            backdropFilter: 'blur(10px)',
          }}
        />
      </Box>

      {/* Contenido sobre la imagen */}
      <Box
        sx={{
          position: 'relative',
          zIndex: 2,
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          p: 3,
        }}
      >
        {/* Título y descripción */}
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'flex-end' }}>
          <Typography
            variant="h4"
            component="h3"
            sx={{
              fontWeight: 700,
              color: 'white',
              mb: 2,
              textShadow: '0 2px 8px rgba(0,0,0,0.5)',
              fontSize: { xs: '1.5rem', md: '2rem' },
            }}
          >
            {currentAd.title}
          </Typography>

          {/* Descripción - Muestra la descripción del anuncio o de la campaña */}
          {description && description.trim() && (
            <Typography
              variant="body1"
              sx={{
                color: 'rgba(255, 255, 255, 0.95)',
                mb: 2,
                textShadow: '0 1px 4px rgba(0,0,0,0.5)',
                fontSize: { xs: '1rem', md: '1.15rem' },
                lineHeight: 1.7,
                maxHeight: '120px',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                display: '-webkit-box',
                WebkitLineClamp: 4,
                WebkitBoxOrient: 'vertical',
                fontWeight: 400,
              }}
            >
              {description}
            </Typography>
          )}
        </Box>

        {/* Controles de navegación en la parte inferior */}
        {ads.length > 1 && (
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              mt: 3,
              pt: 2,
              borderTop: '1px solid rgba(255,255,255,0.2)',
            }}
          >
            {/* Botón anterior */}
            <IconButton
              onClick={(e) => {
                e.stopPropagation(); // Evitar que se active el click del card
                handlePrevious();
              }}
              sx={{
                bgcolor: 'rgba(255, 255, 255, 0.2)',
                color: 'white',
                backdropFilter: 'blur(10px)',
                '&:hover': {
                  bgcolor: 'rgba(255, 255, 255, 0.3)',
                },
                transition: 'all 0.3s ease',
              }}
            >
              <NavigateBeforeIcon />
            </IconButton>

            {/* Indicadores de posición y contador */}
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1 }}>
              <Box sx={{ display: 'flex', gap: 0.5 }}>
                {ads.map((_, index) => (
                  <Box
                    key={index}
                    sx={{
                      width: index === currentIndex ? 32 : 8,
                      height: 8,
                      borderRadius: 1,
                      bgcolor: index === currentIndex ? 'white' : 'rgba(255,255,255,0.5)',
                      transition: 'all 0.3s ease',
                      cursor: 'pointer',
                      boxShadow: index === currentIndex ? '0 2px 4px rgba(0,0,0,0.3)' : 'none',
                    }}
                    onClick={(e) => {
                      e.stopPropagation(); // Evitar que se active el click del card
                      setCurrentIndex(index);
                    }}
                  />
                ))}
              </Box>
              <Typography
                variant="caption"
                sx={{
                  color: 'rgba(255, 255, 255, 0.9)',
                  fontWeight: 600,
                  textShadow: '0 1px 2px rgba(0,0,0,0.5)',
                }}
              >
                {currentIndex + 1} de {ads.length}
              </Typography>
            </Box>

            {/* Botón siguiente */}
            <IconButton
              onClick={(e) => {
                e.stopPropagation(); // Evitar que se active el click del card
                handleNext();
              }}
              sx={{
                bgcolor: 'rgba(255, 255, 255, 0.2)',
                color: 'white',
                backdropFilter: 'blur(10px)',
                '&:hover': {
                  bgcolor: 'rgba(255, 255, 255, 0.3)',
                },
                transition: 'all 0.3s ease',
              }}
            >
              <NavigateNextIcon />
            </IconButton>
          </Box>
        )}
      </Box>
    </Card>
  );
};

export default AdsCarousel;

