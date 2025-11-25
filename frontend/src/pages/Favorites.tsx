import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  CardMedia,
  IconButton,
  Chip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Fade,
  Zoom,
  Tooltip,
  Divider,
} from '@mui/material';
import {
  Favorite as FavoriteIcon,
  Delete as DeleteIcon,
  OpenInNew as OpenInNewIcon,
  Clear as ClearIcon,
  Bookmark as BookmarkIcon,
  Newspaper as NewspaperIcon,
  Category as CategoryIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';
import { useFavorites } from '../contexts/FavoritesContext';
import FavoriteButton from '../components/FavoriteButton';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';

const Favorites: React.FC = () => {
  const { favorites, clearFavorites, loading, error } = useFavorites();
  const [clearDialogOpen, setClearDialogOpen] = useState(false);

  const handleClearFavorites = async () => {
    const success = await clearFavorites();
    setClearDialogOpen(false);
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive': return 'success';
      case 'negative': return 'error';
      case 'neutral': return 'info';
      default: return 'default';
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <Typography>Cargando favoritos...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box p={3}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Fade in timeout={800}>
        <Box sx={{ mb: 4, textAlign: 'center' }}>
          <Typography variant="h4" sx={{ 
            fontWeight: 'bold', 
            background: 'linear-gradient(135deg, #e91e63 0%, #f06292 100%)',
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            mb: 2,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 2
          }}>
            <FavoriteIcon sx={{ fontSize: '2.5rem' }} />
            Mis Favoritos
          </Typography>
          <Typography variant="h6" color="text.secondary">
            {favorites.length} artículos guardados
          </Typography>
        </Box>
      </Fade>

      {/* Actions */}
      {favorites.length > 0 && (
        <Fade in timeout={1000}>
          <Box sx={{ mb: 3, display: 'flex', justifyContent: 'center' }}>
            <Button
              variant="outlined"
              color="error"
              startIcon={<ClearIcon />}
              onClick={() => setClearDialogOpen(true)}
              sx={{ borderRadius: 2 }}
            >
              Limpiar Todos los Favoritos
            </Button>
          </Box>
        </Fade>
      )}

      {/* Favorites Grid */}
      {favorites.length === 0 ? (
        <Fade in timeout={1200}>
          <Box sx={{ textAlign: 'center', py: 8 }}>
            <BookmarkIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary" sx={{ mb: 1 }}>
              No tienes favoritos aún
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Marca artículos como favoritos para verlos aquí
            </Typography>
          </Box>
        </Fade>
      ) : (
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
          {favorites.map((favorite, index) => (
            <Box sx={{ flex: '1 1 300px', maxWidth: '400px' }} key={favorite.id}>
              <Zoom in timeout={800 + index * 100}>
                <Card sx={{ 
                  height: '100%', 
                  display: 'flex', 
                  flexDirection: 'column',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: 6,
                  }
                }}>
                  {favorite.image_url && (
                    <CardMedia
                      component="img"
                      height="200"
                      image={favorite.image_url}
                      alt={favorite.title}
                      sx={{ objectFit: 'cover' }}
                    />
                  )}
                  
                  <CardContent sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
                    <Typography variant="h6" sx={{ 
                      mb: 1, 
                      fontWeight: 'bold',
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical',
                      overflow: 'hidden',
                    }}>
                      {favorite.title}
                    </Typography>
                    
                    <Typography variant="body2" color="text.secondary" sx={{ 
                      mb: 2,
                      display: '-webkit-box',
                      WebkitLineClamp: 3,
                      WebkitBoxOrient: 'vertical',
                      overflow: 'hidden',
                      flexGrow: 1,
                    }}>
                      {favorite.content}
                    </Typography>
                    
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                      <Chip
                        label={favorite.newspaper}
                        size="small"
                        icon={<NewspaperIcon />}
                        color="primary"
                        variant="outlined"
                      />
                      <Chip
                        label={favorite.category}
                        size="small"
                        icon={<CategoryIcon />}
                        color="secondary"
                        variant="outlined"
                      />
                    </Box>
                    
                    <Divider sx={{ my: 1 }} />
                    
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <ScheduleIcon sx={{ fontSize: 14 }} />
                        {format(new Date(favorite.published_date), 'dd MMM yyyy', { locale: es })}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Guardado: {format(new Date(favorite.added_date), 'dd MMM', { locale: es })}
                      </Typography>
                    </Box>
                    
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Button
                        size="small"
                        href={favorite.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        startIcon={<OpenInNewIcon />}
                        sx={{ textTransform: 'none' }}
                      >
                        Leer más
                      </Button>
                      
                      <FavoriteButton 
                        article={favorite} 
                        size="small" 
                        showTooltip={false}
                      />
                    </Box>
                  </CardContent>
                </Card>
              </Zoom>
            </Box>
          ))}
        </Box>
      )}

      {/* Clear Dialog */}
      <Dialog
        open={clearDialogOpen}
        onClose={() => setClearDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <DeleteIcon color="error" />
          Confirmar Eliminación
        </DialogTitle>
        <DialogContent>
          <Typography>
            ¿Estás seguro de que quieres eliminar todos los favoritos? Esta acción no se puede deshacer.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setClearDialogOpen(false)}>
            Cancelar
          </Button>
          <Button 
            onClick={handleClearFavorites} 
            color="error" 
            variant="contained"
            startIcon={<DeleteIcon />}
          >
            Eliminar Todos
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Favorites;
