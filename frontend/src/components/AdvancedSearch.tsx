import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  TextField,
  Button,
  Chip,
  Autocomplete,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Paper,
  Typography,
  IconButton,
  Collapse,
  Card,
  CardContent,
  Tooltip,
  Fade,
  Zoom,
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Clear as ClearIcon,
  History as HistoryIcon,
  Category as CategoryIcon,
  Newspaper as NewspaperIcon,
  LocationOn as LocationIcon,
} from '@mui/icons-material';
import { apiService } from '../services/api';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';

interface SearchFilters {
  query: string;
  category: string;
  newspaper: string;
  region: string;
  dateFrom: string;
  dateTo: string;
  sentiment: string;
  sortBy: string;
  tags: string[];
}

interface SearchResult {
  id: number;
  title: string;
  content: string;
  url: string;
  newspaper: string;
  category: string;
  region: string;
  published_date: string;
  sentiment: string;
  image_url?: string;
  author?: string;
  tags: string[];
  relevance_score: number;
}

interface SearchSuggestions {
  queries: string[];
  categories: string[];
  newspapers: string[];
  regions: string[];
  tags: string[];
}

const AdvancedSearch: React.FC = () => {
  const [filters, setFilters] = useState<SearchFilters>({
    query: '',
    category: '',
    newspaper: '',
    region: '',
    dateFrom: '',
    dateTo: '',
    sentiment: '',
    sortBy: 'relevance',
    tags: [],
  });

  const [results, setResults] = useState<SearchResult[]>([]);
  const [suggestions, setSuggestions] = useState<SearchSuggestions>({
    queries: [],
    categories: [],
    newspapers: [],
    regions: [],
    tags: [],
  });
  const [loading, setLoading] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [searchHistory, setSearchHistory] = useState<string[]>([]);
  const [totalResults, setTotalResults] = useState(0);
  const [, setCurrentPage] = useState(1);
  const [resultsPerPage] = useState(12);

  // Cargar sugerencias y historial
  useEffect(() => {
    loadSuggestions();
    loadSearchHistory();
  }, []);

  const loadSuggestions = async () => {
    try {
      const response = await apiService.getSearchSuggestions();
      setSuggestions(response as SearchSuggestions);
    } catch (error) {
      console.error('Error loading suggestions:', error);
    }
  };

  const loadSearchHistory = () => {
    const history = JSON.parse(localStorage.getItem('searchHistory') || '[]');
    setSearchHistory(history.slice(0, 10)); // Últimas 10 búsquedas
  };

  const saveToHistory = (query: string) => {
    if (!query.trim()) return;
    
    const history = JSON.parse(localStorage.getItem('searchHistory') || '[]');
    const newHistory = [query, ...history.filter((q: string) => q !== query)].slice(0, 20);
    localStorage.setItem('searchHistory', JSON.stringify(newHistory));
    setSearchHistory(newHistory.slice(0, 10));
  };

  const performSearch = useCallback(async (page = 1) => {
    if (!filters.query.trim()) return;

    setLoading(true);
    try {
      const searchParams = {
        ...filters,
        page,
        limit: resultsPerPage,
      };

      const response = await apiService.advancedSearch(searchParams) as any;
      setResults(response.results);
      setTotalResults(response.total);
      setCurrentPage(page);
      
      // Guardar en historial
      saveToHistory(filters.query);
    } catch (error) {
      console.error('Error performing search:', error);
    } finally {
      setLoading(false);
    }
  }, [filters, resultsPerPage]);

  const handleSearch = () => {
    setCurrentPage(1);
    performSearch(1);
  };

  const handleFilterChange = (field: keyof SearchFilters, value: any) => {
    setFilters(prev => ({ ...prev, [field]: value }));
  };

  const clearFilters = () => {
    setFilters({
      query: '',
      category: '',
      newspaper: '',
      region: '',
      dateFrom: '',
      dateTo: '',
      sentiment: '',
      sortBy: 'relevance',
      tags: [],
    });
    setResults([]);
    setTotalResults(0);
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter') {
      handleSearch();
    }
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive': return 'success';
      case 'negative': return 'error';
      case 'neutral': return 'info';
      default: return 'default';
    }
  };

  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case 'positive': return '😊';
      case 'negative': return '😞';
      case 'neutral': return '😐';
      default: return '📰';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Fade in timeout={800}>
        <Box sx={{ mb: 4, textAlign: 'center' }}>
          <Typography variant="h4" sx={{ 
            fontWeight: 'bold', 
            background: 'linear-gradient(135deg, #0ea5e9 0%, #38bdf8 100%)',
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            mb: 2
          }}>
            🔍 Búsqueda Avanzada
          </Typography>
          <Typography variant="h6" color="text.secondary">
            Encuentra noticias específicas con filtros inteligentes
          </Typography>
        </Box>
      </Fade>

      {/* Barra de búsqueda principal */}
      <Fade in timeout={1000}>
        <Paper sx={{ p: 3, mb: 3, borderRadius: 3, boxShadow: 3 }}>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mb: 2 }}>
            <Autocomplete
              freeSolo
              options={suggestions.queries}
              value={filters.query}
              onChange={(_, newValue) => handleFilterChange('query', newValue || '')}
              onInputChange={(_, newValue) => handleFilterChange('query', newValue)}
              renderInput={(params) => (
                <TextField
                  {...params}
                  placeholder="Buscar noticias, temas, palabras clave..."
                  variant="outlined"
                  fullWidth
                  onKeyPress={handleKeyPress}
                  InputProps={{
                    ...params.InputProps,
                    startAdornment: <SearchIcon sx={{ mr: 1, color: 'primary.main' }} />,
                  }}
                />
              )}
              renderOption={(props, option) => (
                <Box component="li" {...props}>
                  <HistoryIcon sx={{ mr: 1, color: 'text.secondary' }} />
                  {option}
                </Box>
              )}
            />
            
            <Button
              variant="contained"
              onClick={handleSearch}
              disabled={loading || !filters.query.trim()}
              sx={{ 
                minWidth: 120,
                background: 'linear-gradient(135deg, #0ea5e9 0%, #38bdf8 100%)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #0284c7 0%, #0ea5e9 100%)',
                }
              }}
            >
              {loading ? 'Buscando...' : 'Buscar'}
            </Button>

            <Tooltip title="Filtros avanzados">
              <IconButton
                onClick={() => setShowFilters(!showFilters)}
                sx={{ 
                  bgcolor: showFilters ? 'primary.main' : 'grey.100',
                  color: showFilters ? 'white' : 'text.primary',
                  '&:hover': {
                    bgcolor: showFilters ? 'primary.dark' : 'grey.200',
                  }
                }}
              >
                <FilterIcon />
              </IconButton>
            </Tooltip>
          </Box>

          {/* Historial de búsquedas */}
          {searchHistory.length > 0 && (
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
              <Typography variant="body2" color="text.secondary" sx={{ mr: 1, alignSelf: 'center' }}>
                Recientes:
              </Typography>
              {searchHistory.map((query, index) => (
                <Chip
                  key={index}
                  label={query}
                  size="small"
                  icon={<HistoryIcon />}
                  onClick={() => {
                    handleFilterChange('query', query);
                    handleSearch();
                  }}
                  sx={{ cursor: 'pointer' }}
                />
              ))}
            </Box>
          )}
        </Paper>
      </Fade>

      {/* Filtros avanzados */}
      <Collapse in={showFilters}>
        <Fade in={showFilters} timeout={800}>
          <Paper sx={{ p: 3, mb: 3, borderRadius: 3, boxShadow: 2 }}>
            <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center' }}>
              <FilterIcon sx={{ mr: 1 }} />
              Filtros Avanzados
            </Typography>
            
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                <Box sx={{ flex: '1 1 200px', minWidth: 200 }}>
                  <FormControl fullWidth>
                    <InputLabel>Categoría</InputLabel>
                    <Select
                      value={filters.category}
                      onChange={(e) => handleFilterChange('category', e.target.value)}
                      label="Categoría"
                    >
                      <MenuItem value="">Todas</MenuItem>
                      {suggestions.categories.map((category) => (
                        <MenuItem key={category} value={category}>
                          <CategoryIcon sx={{ mr: 1, fontSize: 16 }} />
                          {category}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Box>

                <Box sx={{ flex: '1 1 200px', minWidth: 200 }}>
                  <FormControl fullWidth>
                    <InputLabel>Periódico</InputLabel>
                    <Select
                      value={filters.newspaper}
                      onChange={(e) => handleFilterChange('newspaper', e.target.value)}
                      label="Periódico"
                    >
                      <MenuItem value="">Todos</MenuItem>
                      {suggestions.newspapers.map((newspaper) => (
                        <MenuItem key={newspaper} value={newspaper}>
                          <NewspaperIcon sx={{ mr: 1, fontSize: 16 }} />
                          {newspaper}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Box>

                <Box sx={{ flex: '1 1 200px', minWidth: 200 }}>
                  <FormControl fullWidth>
                    <InputLabel>Región</InputLabel>
                    <Select
                      value={filters.region}
                      onChange={(e) => handleFilterChange('region', e.target.value)}
                      label="Región"
                    >
                      <MenuItem value="">Todas</MenuItem>
                      {suggestions.regions.map((region) => (
                        <MenuItem key={region} value={region}>
                          <LocationIcon sx={{ mr: 1, fontSize: 16 }} />
                          {region}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Box>

                <Box sx={{ flex: '1 1 200px', minWidth: 200 }}>
                  <FormControl fullWidth>
                    <InputLabel>Sentimiento</InputLabel>
                    <Select
                      value={filters.sentiment}
                      onChange={(e) => handleFilterChange('sentiment', e.target.value)}
                      label="Sentimiento"
                    >
                      <MenuItem value="">Todos</MenuItem>
                      <MenuItem value="positive">😊 Positivo</MenuItem>
                      <MenuItem value="negative">😞 Negativo</MenuItem>
                      <MenuItem value="neutral">😐 Neutral</MenuItem>
                    </Select>
                  </FormControl>
                </Box>
              </Box>

              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                <Box sx={{ flex: '1 1 200px', minWidth: 200 }}>
                  <TextField
                    fullWidth
                    type="date"
                    label="Fecha desde"
                    value={filters.dateFrom}
                    onChange={(e) => handleFilterChange('dateFrom', e.target.value)}
                    InputLabelProps={{ shrink: true }}
                  />
                </Box>

                <Box sx={{ flex: '1 1 200px', minWidth: 200 }}>
                  <TextField
                    fullWidth
                    type="date"
                    label="Fecha hasta"
                    value={filters.dateTo}
                    onChange={(e) => handleFilterChange('dateTo', e.target.value)}
                    InputLabelProps={{ shrink: true }}
                  />
                </Box>
              </Box>

              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                <Button
                  variant="outlined"
                  startIcon={<ClearIcon />}
                  onClick={clearFilters}
                >
                  Limpiar Filtros
                </Button>
                <Button
                  variant="contained"
                  startIcon={<SearchIcon />}
                  onClick={handleSearch}
                  disabled={loading}
                >
                  Aplicar Filtros
                </Button>
              </Box>
            </Box>
          </Paper>
        </Fade>
      </Collapse>

      {/* Resultados */}
      {results.length > 0 && (
        <Fade in timeout={1200}>
          <Box>
            <Typography variant="h6" sx={{ mb: 2 }}>
              {totalResults.toLocaleString()} resultados encontrados
            </Typography>
            
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
              {results.map((result, index) => (
                <Box sx={{ flex: '1 1 300px', maxWidth: '400px' }} key={result.id}>
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
                      {result.image_url && (
                        <Box
                          component="img"
                          src={result.image_url}
                          alt={result.title}
                          sx={{
                            width: '100%',
                            height: 200,
                            objectFit: 'cover',
                          }}
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
                          {result.title}
                        </Typography>
                        
                        <Typography variant="body2" color="text.secondary" sx={{ 
                          mb: 2,
                          display: '-webkit-box',
                          WebkitLineClamp: 3,
                          WebkitBoxOrient: 'vertical',
                          overflow: 'hidden',
                          flexGrow: 1,
                        }}>
                          {result.content}
                        </Typography>
                        
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                          <Chip
                            label={result.newspaper}
                            size="small"
                            icon={<NewspaperIcon />}
                            color="primary"
                            variant="outlined"
                          />
                          <Chip
                            label={result.category}
                            size="small"
                            icon={<CategoryIcon />}
                            color="secondary"
                            variant="outlined"
                          />
                          <Chip
                            label={getSentimentIcon(result.sentiment)}
                            size="small"
                            color={getSentimentColor(result.sentiment) as any}
                            variant="outlined"
                          />
                        </Box>
                        
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <Typography variant="caption" color="text.secondary">
                            {format(new Date(result.published_date), 'dd MMM yyyy', { locale: es })}
                          </Typography>
                          <Button
                            size="small"
                            href={result.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            sx={{ textTransform: 'none' }}
                          >
                            Leer más
                          </Button>
                        </Box>
                      </CardContent>
                    </Card>
                  </Zoom>
                </Box>
              ))}
            </Box>
          </Box>
        </Fade>
      )}

      {/* Sin resultados */}
      {!loading && filters.query && results.length === 0 && (
        <Fade in timeout={800}>
          <Box sx={{ textAlign: 'center', py: 8 }}>
            <SearchIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary" sx={{ mb: 1 }}>
              No se encontraron resultados
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Intenta con otros términos de búsqueda o ajusta los filtros
            </Typography>
          </Box>
        </Fade>
      )}
    </Box>
  );
};

export default AdvancedSearch;
