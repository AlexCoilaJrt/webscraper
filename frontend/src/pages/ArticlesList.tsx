import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  CardMedia,
  Grid,
  Chip,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Pagination,
  Alert,
  CircularProgress,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  OpenInNew as OpenIcon,
  Image as ImageIcon,
  CalendarToday as DateIcon,
  CalendarToday as CalendarIcon,
  Person as AuthorIcon,
  Category as CategoryIcon,
  TableChart as ExcelIcon,
} from '@mui/icons-material';
import { apiService, Article } from '../services/api';
import * as XLSX from 'xlsx';

const ArticlesList: React.FC = () => {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedNewspaper, setSelectedNewspaper] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedRegion, setSelectedRegion] = useState('');
  const [newspapers, setNewspapers] = useState<string[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedArticle, setSelectedArticle] = useState<Article | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  // Clasificación de periódicos nacionales y extranjeros
  const nationalNewspapers = [
    'El Comercio', 'La República', 'Perú21', 'Trome', 'Ojo', 'Correo', 
    'La Primera', 'Expreso', 'El Peruano', 'Gestión', 'Andina', 'RPP',
    'América TV', 'Panamericana', 'ATV', 'Latina', 'Willax', 'TV Perú'
  ];

  const isNationalNewspaper = (newspaper: string) => {
    return nationalNewspapers.some(national => 
      newspaper.toLowerCase().includes(national.toLowerCase())
    );
  };

  const getFilteredNewspapers = () => {
    if (selectedRegion === 'nacional') {
      return newspapers.filter(newspaper => isNationalNewspaper(newspaper));
    } else if (selectedRegion === 'extranjero') {
      return newspapers.filter(newspaper => !isNationalNewspaper(newspaper));
    }
    return newspapers;
  };

  const loadArticles = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params: any = {
        page,
        limit: 12,
      };

      if (selectedNewspaper) params.newspaper = selectedNewspaper;
      if (selectedCategory) params.category = selectedCategory;
      if (selectedRegion) params.region = selectedRegion;
      if (searchTerm) params.search = searchTerm;

      console.log('🔍 Cargando artículos con parámetros:', params);

      const response = await apiService.getArticles(params) as any;
      
      let filteredArticles = response.articles;

      console.log('📰 Artículos cargados:', filteredArticles.length);
      setArticles(filteredArticles);
      setTotalPages(response.pagination.pages);
      
    } catch (err) {
      setError('Error cargando artículos');
      console.error('Error loading articles:', err);
    } finally {
      setLoading(false);
    }
  }, [page, selectedNewspaper, selectedCategory, selectedRegion, searchTerm]);

  const loadFilters = async () => {
    try {
      console.log('🔍 Cargando filtros...');
      const filters = await apiService.getArticleFilters() as any;
      console.log('📊 Filtros cargados:', filters);
      setNewspapers(filters.newspapers || []);
      setCategories(filters.categories || []);
      console.log('📰 Periódicos:', filters.newspapers);
      console.log('🏷️ Categorías:', filters.categories);
    } catch (err) {
      console.error('Error loading filters:', err);
    }
  };

  useEffect(() => {
    loadArticles();
  }, [loadArticles]);

  useEffect(() => {
    loadFilters();
  }, []);

  const handlePageChange = (event: React.ChangeEvent<unknown>, value: number) => {
    setPage(value);
  };

  const handleFilterChange = (filterType: string, value: string) => {
    console.log(`🔧 Cambiando filtro ${filterType}:`, value);
    setPage(1); // Reset to first page when filter changes
    
    switch (filterType) {
      case 'newspaper':
        setSelectedNewspaper(value);
        break;
      case 'category':
        setSelectedCategory(value);
        break;
      case 'region':
        setSelectedRegion(value);
        break;
    }
  };

  const handleArticleClick = (article: Article) => {
    setSelectedArticle(article);
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setSelectedArticle(null);
  };

  const exportToExcel = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Llamar al endpoint del backend para exportar a Excel
      const response = await fetch('http://localhost:5001/api/articles/export/excel');
      
      if (!response.ok) {
        throw new Error(`Error del servidor: ${response.status}`);
      }
      
      const result = await response.json();
      
      if (result.success) {
        // Convertir base64 a blob
        const byteCharacters = atob(result.data);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
        
        // Crear enlace de descarga
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = result.filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        
        // Mostrar mensaje de éxito
        alert(`✅ Archivo Excel exportado exitosamente: ${result.filename}\n📊 ${result.articles_count} artículos exportados`);
        
      } else {
        throw new Error(result.error || 'Error desconocido');
      }
      
    } catch (err) {
      setError('Error exportando a Excel');
      console.error('Error exporting to Excel:', err);
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido';
      alert(`❌ Error al exportar a Excel: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  const getImageUrl = (article: Article) => {
    if (article.images_data && article.images_data.length > 0) {
      const firstImage = article.images_data[0];
      if (firstImage.local_path) {
        return apiService.getImageUrl(firstImage.local_path.split('/').pop() || '');
      }
      return firstImage.url;
    }
    return null;
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

  if (loading && articles.length === 0) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <CircularProgress />
        <Typography variant="h6" sx={{ ml: 2 }}>
          Cargando artículos...
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom sx={{ mb: 2 }}>
        Artículos Extraídos
      </Typography>
      
      {/* Info sobre total de artículos y paginación */}
      {articles.length > 0 && (
        <Box sx={{ mb: 3, p: 2, bgcolor: 'primary.light', borderRadius: 1, color: 'white' }}>
          <Typography variant="body1">
            Mostrando {articles.length} artículos de la página {page} de {totalPages} páginas
            {totalPages > 1 && (
              <span> - Usa la paginación abajo para ver más artículos</span>
            )}
          </Typography>
        </Box>
      )}

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid size={{ xs: 12, md: 4 }}>
              <TextField
                fullWidth
                label="Buscar artículos"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                }}
                placeholder="Título, contenido o resumen..."
              />
            </Grid>
            <Grid size={{ xs: 12, md: 3 }}>
              <FormControl fullWidth>
                <InputLabel>Periódico</InputLabel>
                <Select
                  value={selectedNewspaper}
                  onChange={(e) => handleFilterChange('newspaper', e.target.value)}
                  label="Periódico"
                >
                  <MenuItem value="">Todos</MenuItem>
                  {getFilteredNewspapers().map((newspaper) => (
                    <MenuItem key={newspaper} value={newspaper}>
                      {newspaper} {isNationalNewspaper(newspaper) ? '🇵🇪' : '🌍'}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, md: 3 }}>
              <FormControl fullWidth>
                <InputLabel>Categoría</InputLabel>
                <Select
                  value={selectedCategory}
                  onChange={(e) => handleFilterChange('category', e.target.value)}
                  label="Categoría"
                >
                  <MenuItem value="">Todas</MenuItem>
                  {categories.map((category) => (
                    <MenuItem key={category} value={category}>
                      {category}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, md: 2 }}>
              <FormControl fullWidth>
                <InputLabel>Región</InputLabel>
                <Select
                  value={selectedRegion}
                  onChange={(e) => handleFilterChange('region', e.target.value)}
                  label="Región"
                >
                  <MenuItem value="">Todas</MenuItem>
                  <MenuItem value="nacional">🇵🇪 Nacional</MenuItem>
                  <MenuItem value="extranjero">🌍 Extranjero</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, md: 2 }}>
              <Button
                variant="outlined"
                startIcon={<FilterIcon />}
                onClick={() => {
                  console.log('🧹 Limpiando filtros...');
                  setSearchTerm('');
                  setSelectedNewspaper('');
                  setSelectedCategory('');
                  setSelectedRegion('');
                  setPage(1);
                }}
                fullWidth
              >
                Limpiar
              </Button>
            </Grid>
            <Grid size={{ xs: 12, md: 2 }}>
              <Button
                variant="contained"
                startIcon={<ExcelIcon />}
                onClick={exportToExcel}
                fullWidth
                sx={{
                  background: 'linear-gradient(135deg, #4caf50, #66bb6a)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #45a049, #5cb85c)',
                  },
                }}
              >
                Exportar Excel
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

      {/* Articles Grid */}
      {articles.length === 0 ? (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 6 }}>
            <Typography variant="h6" color="text.secondary">
              No se encontraron artículos
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Intenta ajustar los filtros o inicia un nuevo scraping
            </Typography>
          </CardContent>
        </Card>
      ) : (
        <>
          <Grid container spacing={3}>
            {articles.map((article) => {
              const imageUrl = getImageUrl(article);
              
              return (
                <Grid size={{ xs: 12, sm: 6, md: 4 }} key={article.id}>
                  <Card 
                    sx={{ 
                      height: '100%', 
                      display: 'flex', 
                      flexDirection: 'column',
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
                        background: 'linear-gradient(90deg, #667eea, #764ba2)',
                        zIndex: 1,
                      }
                    }}
                    onClick={() => handleArticleClick(article)}
                  >
                    {imageUrl && (
                      <Box sx={{ position: 'relative', overflow: 'hidden' }}>
                        <CardMedia
                          component="img"
                          height="200"
                          image={imageUrl}
                          alt={article.title}
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
                      </Box>
                    )}
                    
                    <CardContent sx={{ 
                      flexGrow: 1, 
                      display: 'flex', 
                      flexDirection: 'column',
                      p: 3,
                      background: 'linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%)',
                    }}>
                      <Typography variant="h6" component="h2" gutterBottom sx={{ 
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical',
                        overflow: 'hidden',
                        minHeight: '3em',
                        fontWeight: 700,
                        color: '#2c3e50',
                        mb: 2,
                        lineHeight: 1.3,
                      }}>
                        {article.title}
                      </Typography>
                      
                      <Typography 
                        variant="body2" 
                        color="text.secondary" 
                        sx={{ 
                          flexGrow: 1,
                          display: '-webkit-box',
                          WebkitLineClamp: 3,
                          WebkitBoxOrient: 'vertical',
                          overflow: 'hidden',
                          mb: 2
                        }}
                      >
                        {article.summary || article.content.substring(0, 200) + '...'}
                      </Typography>
                      
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 3 }}>
                        <Chip 
                          label={article.newspaper} 
                          size="small" 
                          sx={{
                            background: 'linear-gradient(135deg, #667eea, #764ba2)',
                            color: 'white',
                            fontWeight: 600,
                            '&:hover': {
                              background: 'linear-gradient(135deg, #5a6fd8, #6a4190)',
                            }
                          }}
                        />
                        {article.category && (
                          <Chip 
                            label={article.category} 
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
                        )}
                        {article.images_found > 0 && (
                          <Chip 
                            icon={<ImageIcon />}
                            label={article.images_found} 
                            size="small" 
                            sx={{
                              background: 'linear-gradient(135deg, #4facfe, #00f2fe)',
                              color: 'white',
                              fontWeight: 600,
                              '&:hover': {
                                background: 'linear-gradient(135deg, #3d8bfe, #00d4fe)',
                              }
                            }}
                          />
                        )}
                      </Box>
                      
                      <Box sx={{ 
                        display: 'flex', 
                        justifyContent: 'space-between', 
                        alignItems: 'center',
                        mt: 'auto',
                        pt: 2,
                        borderTop: '1px solid #e0e0e0',
                      }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <CalendarIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
                          <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500 }}>
                            {formatDate(article.scraped_at)}
                          </Typography>
                        </Box>
                        <Tooltip title="Ver artículo original">
                          <IconButton
                            size="small"
                            sx={{
                              background: 'linear-gradient(135deg, #667eea, #764ba2)',
                              color: 'white',
                              '&:hover': {
                                background: 'linear-gradient(135deg, #5a6fd8, #6a4190)',
                                transform: 'scale(1.1)',
                              },
                              transition: 'all 0.2s ease',
                            }}
                            onClick={(e) => {
                              e.stopPropagation();
                              window.open(article.url, '_blank');
                            }}
                          >
                            <OpenIcon sx={{ fontSize: 18 }} />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              );
            })}
          </Grid>

          {/* Pagination */}
          {totalPages > 1 && (
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mt: 4 }}>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Página {page} de {totalPages} - Navega para ver más artículos
              </Typography>
              <Pagination
                count={totalPages}
                page={page}
                onChange={handlePageChange}
                color="primary"
                size="large"
                showFirstButton
                showLastButton
              />
            </Box>
          )}
        </>
      )}

      {/* Article Detail Dialog */}
      <Dialog 
        open={dialogOpen} 
        onClose={handleCloseDialog}
        maxWidth="md"
        fullWidth
      >
        {selectedArticle && (
          <>
            <DialogTitle>
              <Typography variant="h5" component="div">
                {selectedArticle.title}
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                <Chip label={selectedArticle.newspaper} size="small" color="primary" />
                {selectedArticle.category && (
                  <Chip label={selectedArticle.category} size="small" color="secondary" />
                )}
              </Box>
            </DialogTitle>
            
            <DialogContent>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  <DateIcon sx={{ fontSize: 16, mr: 0.5, verticalAlign: 'middle' }} />
                  {formatDate(selectedArticle.scraped_at)}
                </Typography>
                {selectedArticle.author && (
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    <AuthorIcon sx={{ fontSize: 16, mr: 0.5, verticalAlign: 'middle' }} />
                    {selectedArticle.author}
                  </Typography>
                )}
                {selectedArticle.category && (
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    <CategoryIcon sx={{ fontSize: 16, mr: 0.5, verticalAlign: 'middle' }} />
                    {selectedArticle.category}
                  </Typography>
                )}
              </Box>
              
              {selectedArticle.summary && (
                <Typography variant="body1" paragraph sx={{ fontStyle: 'italic', backgroundColor: '#f5f5f5', p: 2, borderRadius: 1 }}>
                  {selectedArticle.summary}
                </Typography>
              )}
              
              <Typography variant="body1" paragraph>
                {selectedArticle.content}
              </Typography>
              
              {selectedArticle.images_data && selectedArticle.images_data.length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="h6" gutterBottom>
                    Imágenes ({selectedArticle.images_found})
                  </Typography>
                  <Grid container spacing={2}>
                    {selectedArticle.images_data.map((img, index) => (
                      <Grid size={{ xs: 12, sm: 6 }} key={index}>
                        <img
                          src={img.local_path ? apiService.getImageUrl(img.local_path.split('/').pop() || '') : img.url}
                          alt={img.alt_text || `Imagen ${index + 1}`}
                          style={{ width: '100%', height: 'auto', borderRadius: 8 }}
                        />
                      </Grid>
                    ))}
                  </Grid>
                </Box>
              )}
            </DialogContent>
            
            <DialogActions>
              <Button onClick={handleCloseDialog}>
                Cerrar
              </Button>
              <Button 
                variant="contained" 
                startIcon={<OpenIcon />}
                onClick={() => window.open(selectedArticle.url, '_blank')}
              >
                Ver Original
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Box>
  );
};

export default ArticlesList;
