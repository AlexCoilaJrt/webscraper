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
  FormControlLabel,
  Checkbox,
  Collapse,
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
  Description as CsvIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';
import { apiService, Article } from '../services/api';
import * as XLSX from 'xlsx';
import ChatbotWidget from '../components/ChatbotWidget';
import CommentsSection from '../components/CommentsSection';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../services/api';

const ArticlesList: React.FC = () => {
  const { isAdmin } = useAuth();
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [userSubscription, setUserSubscription] = useState<any>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedNewspaper, setSelectedNewspaper] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedRegion, setSelectedRegion] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [timeFilter, setTimeFilter] = useState<string>('');
  const [showCustomDateRange, setShowCustomDateRange] = useState(false);
  const [showTimeFilters, setShowTimeFilters] = useState(false);
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
      if (dateFrom) {
        params.dateFrom = dateFrom;
        console.log(`📅 Filtro fecha desde: ${dateFrom}`);
      }
      if (dateTo) {
        params.dateTo = dateTo;
        console.log(`📅 Filtro fecha hasta: ${dateTo}`);
      }

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
  }, [page, selectedNewspaper, selectedCategory, selectedRegion, searchTerm, dateFrom, dateTo]);

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
    loadUserSubscription();
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

  const hasExportAccess = () => {
    // Admin siempre tiene acceso
    if (isAdmin) return true;
    // Usuarios con plan Premium o Enterprise tienen acceso
    if (userSubscription) {
      const planName = userSubscription.plan_name?.toLowerCase() || '';
      return planName === 'premium' || planName === 'enterprise';
    }
    return false;
  };

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

  const calculateDateRange = (filter: string): { from: string; to: string } => {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const todayStr = today.toISOString().split('T')[0];
    
    switch (filter) {
      case 'last_hour':
        // Para última hora, usamos desde ayer hasta hoy (por si la hora cruza medianoche)
        // El backend filtrará por fecha, así que esto capturará artículos de hoy y ayer
        const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);
        const oneHourAgoDate = new Date(oneHourAgo.getFullYear(), oneHourAgo.getMonth(), oneHourAgo.getDate());
        return {
          from: oneHourAgoDate.toISOString().split('T')[0],
          to: todayStr
        };
      case 'last_24h':
        // Últimas 24 horas: desde ayer hasta hoy
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);
        return {
          from: yesterday.toISOString().split('T')[0],
          to: todayStr
        };
      case 'last_7d':
        // Últimos 7 días: desde hace 7 días hasta hoy
        const sevenDaysAgo = new Date(today);
        sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
        return {
          from: sevenDaysAgo.toISOString().split('T')[0],
          to: todayStr
        };
      case 'last_month':
        // Último mes: desde el primer día del mes anterior hasta hoy
        const lastMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1);
        return {
          from: lastMonth.toISOString().split('T')[0],
          to: todayStr
        };
      case 'last_year':
        // Último año: desde el 1 de enero del año pasado hasta hoy
        const lastYear = new Date(now.getFullYear() - 1, 0, 1);
        return {
          from: lastYear.toISOString().split('T')[0],
          to: todayStr
        };
      default:
        return { from: '', to: '' };
    }
  };

  const handleTimeFilterChange = (filter: string) => {
    setPage(1);
    
    // Si se hace clic en el mismo filtro, deseleccionarlo
    if (timeFilter === filter) {
      console.log('🔄 Deseleccionando filtro de tiempo');
      setTimeFilter('');
      setDateFrom('');
      setDateTo('');
      setShowCustomDateRange(false);
      return;
    }
    
    console.log(`⏰ Aplicando filtro de tiempo: ${filter}`);
    setTimeFilter(filter);
    
    if (filter === 'custom') {
      setShowCustomDateRange(true);
      // No cambiar las fechas si ya están establecidas
      console.log('📅 Modo rango personalizado activado');
    } else {
      setShowCustomDateRange(false);
      const range = calculateDateRange(filter);
      console.log(`📅 Rango calculado: ${range.from} a ${range.to}`);
      setDateFrom(range.from);
      setDateTo(range.to);
    }
  };

  const handleDateChange = (field: 'dateFrom' | 'dateTo', value: string) => {
    setPage(1); // Reset to first page when filter changes
    if (field === 'dateFrom') {
      setDateFrom(value);
    } else {
      setDateTo(value);
    }
    // Si se cambia manualmente, activar rango personalizado
    if (!showCustomDateRange) {
      setTimeFilter('custom');
      setShowCustomDateRange(true);
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
    // Verificar acceso
    if (!hasExportAccess()) {
      setError('La exportación a Excel está disponible solo para planes Premium y Enterprise. Actualiza tu plan para acceder a esta función.');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      // Llamar al endpoint del backend para exportar a Excel
      const response = await fetch('http://localhost:5001/api/articles/export/excel', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
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

  const exportToCSV = async () => {
    // Verificar acceso
    if (!hasExportAccess()) {
      setError('La exportación a CSV está disponible solo para planes Premium y Enterprise. Actualiza tu plan para acceder a esta función.');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await fetch('http://localhost:5001/api/articles/export/csv', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error(`Error del servidor: ${response.status}`);
      }

      const result = await response.json();

      if (result.success) {
        const byteCharacters = atob(result.data);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: 'text/csv;charset=utf-8;' });

        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = result.filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);

        alert(`✅ Archivo CSV exportado: ${result.filename}\n📊 ${result.articles_count} artículos incluidos`);
      } else {
        throw new Error(result.error || 'Error desconocido');
      }
    } catch (err) {
      setError('Error exportando a CSV');
      console.error('Error exporting to CSV:', err);
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido';
      alert(`❌ Error al exportar a CSV: ${errorMessage}`);
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
      <ChatbotWidget />
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
            <Grid size={{ xs: 12, md: 2.5 }}>
              <TextField
                fullWidth
                label="Buscar artículos"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                }}
                placeholder="Título, contenido o resumen..."
                size="small"
              />
            </Grid>
            <Grid size={{ xs: 12, md: 1.8 }}>
              <FormControl fullWidth size="small">
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
            <Grid size={{ xs: 12, md: 1.6 }}>
              <FormControl fullWidth size="small">
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
            <Grid size={{ xs: 12, md: 1.3 }}>
              <FormControl fullWidth size="small">
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
            <Grid size={{ xs: 12, md: 1.2 }}>
              <Button
                variant="outlined"
                onClick={() => setShowTimeFilters(!showTimeFilters)}
                size="small"
                fullWidth
                sx={{
                  justifyContent: 'space-between',
                  textTransform: 'none',
                  py: 0.8,
                  borderColor: 'primary.main',
                  '&:hover': {
                    borderColor: 'primary.dark',
                    backgroundColor: 'action.hover',
                  },
                }}
                endIcon={showTimeFilters ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <Typography variant="body2" sx={{ fontWeight: 500 }}>
                    ⏰ Tiempo
                  </Typography>
                  {timeFilter && (
                    <Chip
                      label={
                        timeFilter === 'last_hour' ? '1h' :
                        timeFilter === 'last_24h' ? '24h' :
                        timeFilter === 'last_7d' ? '7d' :
                        timeFilter === 'last_month' ? 'Mes' :
                        timeFilter === 'last_year' ? 'Año' :
                        'Custom'
                      }
                      size="small"
                      color="primary"
                      sx={{ height: 20, fontSize: '0.65rem', ml: 0.5 }}
                    />
                  )}
                </Box>
              </Button>
            </Grid>
            <Grid size={{ xs: 12, md: 1 }}>
              <Button
                variant="outlined"
                startIcon={<FilterIcon />}
                onClick={() => {
                  console.log('🧹 Limpiando filtros...');
                  setSearchTerm('');
                  setSelectedNewspaper('');
                  setSelectedCategory('');
                  setSelectedRegion('');
                  setDateFrom('');
                  setDateTo('');
                  setTimeFilter('');
                  setShowCustomDateRange(false);
                  setPage(1);
                }}
                fullWidth
                size="small"
                sx={{ minWidth: 'auto' }}
              >
                Limpiar
              </Button>
            </Grid>
            {hasExportAccess() && (
              <>
            <Grid size={{ xs: 6, md: 1 }}>
              <Button
                variant="contained"
                startIcon={<ExcelIcon />}
                onClick={exportToExcel}
                size="small"
                sx={{
                  background: 'linear-gradient(135deg, #4caf50, #66bb6a)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #45a049, #5cb85c)',
                  },
                  minWidth: 'auto',
                  padding: '4px 8px',
                  fontSize: '0.75rem',
                }}
              >
                Exportar Excel
              </Button>
            </Grid>
            <Grid size={{ xs: 6, md: 1 }}>
              <Button
                variant="outlined"
                startIcon={<CsvIcon />}
                onClick={exportToCSV}
                size="small"
                sx={{
                  borderColor: 'primary.main',
                  color: 'primary.main',
                  '&:hover': {
                    borderColor: 'primary.dark',
                    backgroundColor: 'rgba(25, 118, 210, 0.04)',
                  },
                  minWidth: 'auto',
                  padding: '4px 8px',
                  fontSize: '0.75rem',
                }}
              >
                Exportar CSV
              </Button>
            </Grid>
              </>
            )}
          </Grid>

          {/* Panel expandible de Filtros de Tiempo */}
          <Collapse in={showTimeFilters}>
            <Box sx={{ mt: 2, p: 2, bgcolor: 'background.paper', borderRadius: 1, border: 1, borderColor: 'divider' }}>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5, mb: 2 }}>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={timeFilter === 'last_hour'}
                      onChange={() => handleTimeFilterChange('last_hour')}
                      size="small"
                    />
                  }
                  label="Última hora"
                />
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={timeFilter === 'last_24h'}
                      onChange={() => handleTimeFilterChange('last_24h')}
                      size="small"
                    />
                  }
                  label="Últimas 24 horas"
                />
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={timeFilter === 'last_7d'}
                      onChange={() => handleTimeFilterChange('last_7d')}
                      size="small"
                    />
                  }
                  label="Últimos 7 días"
                />
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={timeFilter === 'last_month'}
                      onChange={() => handleTimeFilterChange('last_month')}
                      size="small"
                    />
                  }
                  label="Último mes"
                />
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={timeFilter === 'last_year'}
                      onChange={() => handleTimeFilterChange('last_year')}
                      size="small"
                    />
                  }
                  label="Último año"
                />
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={timeFilter === 'custom' || showCustomDateRange}
                      onChange={() => handleTimeFilterChange('custom')}
                      size="small"
                    />
                  }
                  label="Rango personalizado"
                />
              </Box>
              <Collapse in={showCustomDateRange || timeFilter === 'custom'}>
                <Grid container spacing={2} sx={{ mt: 1 }}>
                  <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                    <TextField
                      fullWidth
                      label="Fecha desde"
                      type="date"
                      value={dateFrom}
                      onChange={(e) => handleDateChange('dateFrom', e.target.value)}
                      InputLabelProps={{
                        shrink: true,
                      }}
                      size="small"
                      InputProps={{
                        startAdornment: <CalendarIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                      }}
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                    <TextField
                      fullWidth
                      label="Fecha hasta"
                      type="date"
                      value={dateTo}
                      onChange={(e) => handleDateChange('dateTo', e.target.value)}
                      InputLabelProps={{
                        shrink: true,
                      }}
                      size="small"
                      InputProps={{
                        startAdornment: <CalendarIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                      }}
                    />
                  </Grid>
                </Grid>
              </Collapse>
            </Box>
          </Collapse>
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
                        {article.user_category || article.category ? (
                          <Chip 
                            label={article.user_category || article.category} 
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
                        ) : null}
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

              {/* Sección de Comentarios */}
              <CommentsSection articleId={selectedArticle.id} />
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
