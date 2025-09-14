import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardMedia,
  CardContent,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Pagination,
  Alert,
  CircularProgress,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  IconButton,
  Tooltip,
  ImageList,
  ImageListItem,
  Container,
  Avatar,
  Fade,
  Zoom,
  Paper,
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Download as DownloadIcon,
  OpenInNew as OpenIcon,
  Image as ImageIcon,
  ZoomIn as ZoomIcon,
  PhotoLibrary as PhotoLibraryIcon,
  Storage as StorageIcon,
} from '@mui/icons-material';
import { apiService, Image } from '../services/api';

const ImagesGallery: React.FC = () => {
  const [images, setImages] = useState<Image[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedArticleId, setSelectedArticleId] = useState('');
  const [articleIds, setArticleIds] = useState<string[]>([]);
  const [selectedImage, setSelectedImage] = useState<Image | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'masonry'>('grid');

  useEffect(() => {
    loadImages();
  }, [page, selectedArticleId]);

  const loadImages = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params: any = {
        page,
        limit: 20,
      };

      if (selectedArticleId) params.article_id = selectedArticleId;

      const response = await apiService.getImages(params) as any;
      
      let filteredImages = response.images;
      
      // Client-side search
      if (searchTerm) {
        filteredImages = filteredImages.filter((image: any) =>
          image.alt_text.toLowerCase().includes(searchTerm.toLowerCase()) ||
          image.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
          image.article_id.toLowerCase().includes(searchTerm.toLowerCase())
        );
      }

      setImages(filteredImages);
      
      // Extract unique article IDs
      const uniqueArticleIds = Array.from(new Set(response.images.map((img: any) => img.article_id))) as string[];
      setArticleIds(uniqueArticleIds);
      
    } catch (err) {
      setError('Error cargando imágenes');
      console.error('Error loading images:', err);
    } finally {
      setLoading(false);
    }
  };

  const handlePageChange = (event: React.ChangeEvent<unknown>, value: number) => {
    setPage(value);
  };

  const handleImageClick = (image: Image) => {
    setSelectedImage(image);
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setSelectedImage(null);
  };

  const getImageUrl = (image: Image) => {
    if (image.local_path) {
      return apiService.getImageUrl(image.local_path.split('/').pop() || '');
    }
    return image.url;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('es-ES', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateString;
    }
  };

  if (loading && images.length === 0) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <CircularProgress />
        <Typography variant="h6" sx={{ ml: 2 }}>
          Cargando imágenes...
        </Typography>
      </Box>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Fade in timeout={800}>
        <Box sx={{ mb: 6, textAlign: 'center' }}>
          <Avatar
            sx={{
              width: 80,
              height: 80,
              mx: 'auto',
              mb: 2,
              bgcolor: 'secondary.main',
              boxShadow: 3,
            }}
          >
            <PhotoLibraryIcon sx={{ fontSize: 40 }} />
          </Avatar>
          <Typography
            variant="h3"
            component="h1"
            gutterBottom
            sx={{
              fontWeight: 700,
              background: 'linear-gradient(45deg, #f093fb, #f5576c)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            Galería de Imágenes
          </Typography>
          <Typography variant="h6" color="text.secondary" sx={{ maxWidth: 600, mx: 'auto' }}>
            Explora todas las imágenes extraídas durante el scraping
          </Typography>
        </Box>
      </Fade>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid size={{ xs: 12, md: 4 }}>
              <TextField
                fullWidth
                label="Buscar imágenes"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                }}
                placeholder="Texto alternativo, título o ID de artículo..."
              />
            </Grid>
            <Grid size={{ xs: 12, md: 3 }}>
              <FormControl fullWidth>
                <InputLabel>Artículo</InputLabel>
                <Select
                  value={selectedArticleId}
                  onChange={(e) => setSelectedArticleId(e.target.value)}
                  label="Artículo"
                >
                  <MenuItem value="">Todos</MenuItem>
                  {articleIds.map((articleId) => (
                    <MenuItem key={articleId} value={articleId}>
                      {articleId}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, md: 3 }}>
              <FormControl fullWidth>
                <InputLabel>Vista</InputLabel>
                <Select
                  value={viewMode}
                  onChange={(e) => setViewMode(e.target.value as 'grid' | 'masonry')}
                  label="Vista"
                >
                  <MenuItem value="grid">Cuadrícula</MenuItem>
                  <MenuItem value="masonry">Mosaico</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, md: 2 }}>
              <Button
                variant="outlined"
                startIcon={<FilterIcon />}
                onClick={() => {
                  setSearchTerm('');
                  setSelectedArticleId('');
                }}
                fullWidth
              >
                Limpiar
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Images Display */}
      {images.length === 0 ? (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 6 }}>
            <ImageIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary">
              No se encontraron imágenes
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Intenta ajustar los filtros o inicia un nuevo scraping con descarga de imágenes
            </Typography>
          </CardContent>
        </Card>
      ) : (
        <>
          {viewMode === 'grid' ? (
            <Grid container spacing={2}>
              {images.map((image) => (
                <Grid size={{ xs: 12, sm: 6, md: 4, lg: 3 }} key={image.id}>
                  <Card 
                    sx={{ 
                      cursor: 'pointer',
                      borderRadius: 3,
                      boxShadow: 2,
                      transition: 'all 0.3s ease',
                      '&:hover': {
                        transform: 'translateY(-8px)',
                        boxShadow: 8,
                      },
                      overflow: 'hidden',
                      position: 'relative',
                      '&::before': {
                        content: '""',
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        right: 0,
                        height: 4,
                        background: 'linear-gradient(90deg, #f093fb, #f5576c)',
                        zIndex: 1,
                      }
                    }}
                    onClick={() => handleImageClick(image)}
                  >
                    <Box sx={{ position: 'relative', overflow: 'hidden' }}>
                      <CardMedia
                        component="img"
                        height="200"
                        image={getImageUrl(image)}
                        alt={image.alt_text || 'Imagen'}
                        sx={{ 
                          objectFit: 'cover',
                          transition: 'transform 0.3s ease',
                          '&:hover': {
                            transform: 'scale(1.05)',
                          }
                        }}
                      />
                      <Box
                        sx={{
                          position: 'absolute',
                          top: 0,
                          left: 0,
                          right: 0,
                          bottom: 0,
                          background: 'linear-gradient(to bottom, transparent 0%, rgba(0,0,0,0.1) 100%)',
                        }}
                      />
                      <Box
                        sx={{
                          position: 'absolute',
                          top: 8,
                          right: 8,
                          background: 'rgba(0,0,0,0.7)',
                          borderRadius: 1,
                          p: 0.5,
                        }}
                      >
                        <ZoomIcon sx={{ color: 'white', fontSize: 20 }} />
                      </Box>
                    </Box>
                    <CardContent sx={{ 
                      p: 2,
                      background: 'linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%)',
                    }}>
                      <Typography 
                        variant="body2" 
                        color="text.secondary" 
                        gutterBottom
                        sx={{
                          display: '-webkit-box',
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: 'vertical',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          fontWeight: 500,
                          mb: 2,
                        }}
                      >
                        {image.alt_text || 'Sin descripción'}
                      </Typography>
                      <Box sx={{ 
                        display: 'flex', 
                        justifyContent: 'space-between', 
                        alignItems: 'center',
                        pt: 1,
                        borderTop: '1px solid #e0e0e0',
                      }}>
                        <Chip 
                          label={image.article_id} 
                          size="small" 
                          sx={{
                            background: 'linear-gradient(135deg, #f093fb, #f5576c)',
                            color: 'white',
                            fontWeight: 600,
                            '&:hover': {
                              background: 'linear-gradient(135deg, #e881f7, #f3455a)',
                            }
                          }}
                        />
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <StorageIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
                          <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500 }}>
                            {image.width} × {image.height}
                          </Typography>
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          ) : (
            <ImageList variant="masonry" cols={4} gap={8}>
              {images.map((image) => (
                <ImageListItem key={image.id}>
                  <img
                    src={getImageUrl(image)}
                    alt={image.alt_text || 'Imagen'}
                    loading="lazy"
                    style={{ cursor: 'pointer' }}
                    onClick={() => handleImageClick(image)}
                  />
                </ImageListItem>
              ))}
            </ImageList>
          )}

          {/* Pagination */}
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
            <Pagination
              count={10} // You might want to get this from the API
              page={page}
              onChange={handlePageChange}
              color="primary"
              size="large"
            />
          </Box>
        </>
      )}

      {/* Image Detail Dialog */}
      <Dialog 
        open={dialogOpen} 
        onClose={handleCloseDialog}
        maxWidth="lg"
        fullWidth
      >
        {selectedImage && (
          <>
            <DialogTitle>
              <Typography variant="h6" component="div">
                Detalles de la Imagen
              </Typography>
            </DialogTitle>
            
            <DialogContent>
              <Grid container spacing={3}>
                <Grid size={{ xs: 12, md: 8 }}>
                  <img
                    src={getImageUrl(selectedImage)}
                    alt={selectedImage.alt_text || 'Imagen'}
                    style={{ 
                      width: '100%', 
                      height: 'auto', 
                      borderRadius: 8,
                      maxHeight: '60vh',
                      objectFit: 'contain'
                    }}
                  />
                </Grid>
                
                <Grid size={{ xs: 12, md: 4 }}>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <Box>
                      <Typography variant="subtitle2" color="text.secondary">
                        Texto Alternativo
                      </Typography>
                      <Typography variant="body2">
                        {selectedImage.alt_text || 'Sin descripción'}
                      </Typography>
                    </Box>
                    
                    <Box>
                      <Typography variant="subtitle2" color="text.secondary">
                        Título
                      </Typography>
                      <Typography variant="body2">
                        {selectedImage.title || 'Sin título'}
                      </Typography>
                    </Box>
                    
                    <Box>
                      <Typography variant="subtitle2" color="text.secondary">
                        Artículo ID
                      </Typography>
                      <Chip 
                        label={selectedImage.article_id} 
                        size="small" 
                        color="primary" 
                        variant="outlined"
                      />
                    </Box>
                    
                    <Box>
                      <Typography variant="subtitle2" color="text.secondary">
                        Dimensiones
                      </Typography>
                      <Typography variant="body2">
                        {selectedImage.width} × {selectedImage.height} px
                      </Typography>
                    </Box>
                    
                    <Box>
                      <Typography variant="subtitle2" color="text.secondary">
                        Formato
                      </Typography>
                      <Typography variant="body2">
                        {selectedImage.format?.toUpperCase() || 'Desconocido'}
                      </Typography>
                    </Box>
                    
                    <Box>
                      <Typography variant="subtitle2" color="text.secondary">
                        Tamaño
                      </Typography>
                      <Typography variant="body2">
                        {formatFileSize(selectedImage.size_bytes)}
                      </Typography>
                    </Box>
                    
                    <Box>
                      <Typography variant="subtitle2" color="text.secondary">
                        Puntuación de Relevancia
                      </Typography>
                      <Typography variant="body2">
                        {selectedImage.relevance_score}/100
                      </Typography>
                    </Box>
                    
                    <Box>
                      <Typography variant="subtitle2" color="text.secondary">
                        Descargada
                      </Typography>
                      <Typography variant="body2">
                        {formatDate(selectedImage.downloaded_at)}
                      </Typography>
                    </Box>
                  </Box>
                </Grid>
              </Grid>
            </DialogContent>
            
            <DialogActions>
              <Button onClick={handleCloseDialog}>
                Cerrar
              </Button>
              <Button 
                variant="outlined"
                startIcon={<DownloadIcon />}
                onClick={() => {
                  const link = document.createElement('a');
                  link.href = getImageUrl(selectedImage);
                  link.download = `image_${selectedImage.id}.${selectedImage.format || 'jpg'}`;
                  link.click();
                }}
              >
                Descargar
              </Button>
              <Button 
                variant="contained" 
                startIcon={<OpenIcon />}
                onClick={() => window.open(getImageUrl(selectedImage), '_blank')}
              >
                Abrir Original
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Container>
  );
};

export default ImagesGallery;
