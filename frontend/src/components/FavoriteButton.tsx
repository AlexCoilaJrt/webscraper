import React, { useState } from 'react';
import {
  IconButton,
  Tooltip,
  Snackbar,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Favorite as FavoriteIcon,
  FavoriteBorder as FavoriteBorderIcon,
} from '@mui/icons-material';
import { useFavorites } from '../contexts/FavoritesContext';

interface FavoriteButtonProps {
  article: {
    id: number;
    title: string;
    content: string;
    url: string;
    newspaper: string;
    category: string;
    published_date: string;
    image_url?: string;
    author?: string;
  };
  size?: 'small' | 'medium' | 'large';
  showTooltip?: boolean;
}

const FavoriteButton: React.FC<FavoriteButtonProps> = ({ 
  article, 
  size = 'medium',
  showTooltip = true 
}) => {
  const { isFavorite, addToFavorites, removeFromFavorites } = useFavorites();
  const [loading, setLoading] = useState(false);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'error'>('success');

  const isArticleFavorite = isFavorite(article.id);

  const handleToggleFavorite = async () => {
    setLoading(true);
    
    try {
      let success = false;
      let message = '';
      
      if (isArticleFavorite) {
        success = await removeFromFavorites(article.id);
        message = success ? 'Removido de favoritos' : 'Error removiendo de favoritos';
      } else {
        success = await addToFavorites(article);
        message = success ? 'Agregado a favoritos' : 'Error agregando a favoritos';
      }
      
      setSnackbarMessage(message);
      setSnackbarSeverity(success ? 'success' : 'error');
      setSnackbarOpen(true);
      
    } catch (error) {
      console.error('Error toggling favorite:', error);
      setSnackbarMessage('Error procesando favorito');
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
    } finally {
      setLoading(false);
    }
  };

  const button = (
    <IconButton
      onClick={handleToggleFavorite}
      disabled={loading}
      size={size}
      sx={{
        color: isArticleFavorite ? '#e91e63' : 'inherit',
        transition: 'all 0.3s ease',
        '&:hover': {
          color: isArticleFavorite ? '#c2185b' : '#e91e63',
          transform: 'scale(1.1)',
        },
        '&:disabled': {
          opacity: 0.6,
        },
      }}
    >
      {loading ? (
        <CircularProgress size={size === 'small' ? 16 : size === 'large' ? 24 : 20} />
      ) : isArticleFavorite ? (
        <FavoriteIcon />
      ) : (
        <FavoriteBorderIcon />
      )}
    </IconButton>
  );

  return (
    <>
      {showTooltip ? (
        <Tooltip 
          title={
            isArticleFavorite 
              ? 'Remover de favoritos' 
              : 'Agregar a favoritos'
          }
          arrow
        >
          {button}
        </Tooltip>
      ) : (
        button
      )}

      <Snackbar
        open={snackbarOpen}
        autoHideDuration={3000}
        onClose={() => setSnackbarOpen(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={() => setSnackbarOpen(false)}
          severity={snackbarSeverity}
          sx={{ width: '100%' }}
        >
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </>
  );
};

export default FavoriteButton;


















