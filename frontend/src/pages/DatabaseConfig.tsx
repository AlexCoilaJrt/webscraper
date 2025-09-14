import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  TextField,
  Button,
  Alert,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Divider,
  Container,
  Avatar,
  Fade,
  Zoom,
  Paper,
  Chip,
} from '@mui/material';
import {
  Storage as StorageIcon,
  Storage as DatabaseIcon,
  CloudDownload as DownloadIcon,
  Settings as SettingsIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { apiService } from '../services/api';

interface DatabaseConfig {
  type: 'sqlite' | 'mysql' | 'postgresql';
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
  ssl: boolean;
}

interface ConnectionStatus {
  connected: boolean;
  message: string;
  tables?: string[];
  recordCounts?: { [key: string]: number };
}

const DatabaseConfig: React.FC = () => {
  const [config, setConfig] = useState<DatabaseConfig>({
    type: 'sqlite',
    host: 'localhost',
    port: 3306,
    database: 'news_database',
    username: '',
    password: '',
    ssl: false,
  });

  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleConfigChange = (field: keyof DatabaseConfig, value: any) => {
    setConfig(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  const testConnection = async () => {
    try {
      setLoading(true);
      setError(null);
      setConnectionStatus(null);

      // Simular prueba de conexión (en una implementación real, esto llamaría al backend)
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Simular respuesta exitosa
      setConnectionStatus({
        connected: true,
        message: 'Conexión exitosa a la base de datos',
        tables: ['articles', 'images', 'scraping_stats'],
        recordCounts: {
          articles: 1250,
          images: 3400,
          scraping_stats: 45,
        },
      });

      setSuccess('✅ Conexión establecida correctamente');
    } catch (err) {
      setError('❌ Error al conectar con la base de datos');
      setConnectionStatus({
        connected: false,
        message: 'Error de conexión',
      });
    } finally {
      setLoading(false);
    }
  };

  const saveConfig = async () => {
    try {
      setLoading(true);
      setError(null);

      // Simular guardado de configuración
      await new Promise(resolve => setTimeout(resolve, 1000));

      setSuccess('✅ Configuración guardada exitosamente');
    } catch (err) {
      setError('❌ Error al guardar la configuración');
    } finally {
      setLoading(false);
    }
  };

  const downloadData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Simular descarga de datos
      await new Promise(resolve => setTimeout(resolve, 2000));

      setSuccess('✅ Datos descargados exitosamente');
    } catch (err) {
      setError('❌ Error al descargar los datos');
    } finally {
      setLoading(false);
    }
  };

  const getDatabaseIcon = (type: string) => {
    switch (type) {
      case 'sqlite':
        return <DatabaseIcon sx={{ color: '#003B57' }} />;
      case 'mysql':
        return <DatabaseIcon sx={{ color: '#00758F' }} />;
      case 'postgresql':
        return <DatabaseIcon sx={{ color: '#336791' }} />;
      default:
        return <DatabaseIcon />;
    }
  };

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
              bgcolor: 'info.main',
              boxShadow: 3,
            }}
          >
            <SettingsIcon sx={{ fontSize: 40 }} />
          </Avatar>
          <Typography
            variant="h3"
            component="h1"
            gutterBottom
            sx={{
              fontWeight: 700,
              background: 'linear-gradient(45deg, #2196f3, #21cbf3)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            Configuración de Base de Datos
          </Typography>
          <Typography variant="h6" color="text.secondary" sx={{ maxWidth: 600, mx: 'auto' }}>
            Configura la conexión a tu base de datos local y descarga tus datos
          </Typography>
        </Box>
      </Fade>

      {error && (
        <Fade in timeout={600}>
          <Alert severity="error" sx={{ mb: 4, borderRadius: 2 }}>
            {error}
          </Alert>
        </Fade>
      )}

      {success && (
        <Fade in timeout={600}>
          <Alert severity="success" sx={{ mb: 4, borderRadius: 2 }}>
            {success}
          </Alert>
        </Fade>
      )}

      <Grid container spacing={4}>
        {/* Configuración de Base de Datos */}
        <Grid size={{ xs: 12, md: 8 }}>
          <Zoom in timeout={1000}>
            <Card
              sx={{
                borderRadius: 3,
                boxShadow: 4,
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                color: 'white',
              }}
            >
              <CardContent sx={{ p: 4 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                  <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)', mr: 2 }}>
                    <StorageIcon />
                  </Avatar>
                  <Typography variant="h5" sx={{ fontWeight: 600 }}>
                    Configuración de Conexión
                  </Typography>
                </Box>

                <Grid container spacing={3}>
                  <Grid size={{ xs: 12, md: 6 }}>
                    <FormControl fullWidth>
                      <InputLabel sx={{ color: 'white' }}>Tipo de Base de Datos</InputLabel>
                      <Select
                        value={config.type}
                        onChange={(e) => handleConfigChange('type', e.target.value)}
                        label="Tipo de Base de Datos"
                        sx={{
                          color: 'white',
                          '& .MuiOutlinedInput-notchedOutline': {
                            borderColor: 'rgba(255,255,255,0.3)',
                          },
                          '&:hover .MuiOutlinedInput-notchedOutline': {
                            borderColor: 'rgba(255,255,255,0.5)',
                          },
                          '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                            borderColor: 'white',
                          },
                        }}
                      >
                        <MenuItem value="sqlite">
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            {getDatabaseIcon('sqlite')}
                            SQLite
                          </Box>
                        </MenuItem>
                        <MenuItem value="mysql">
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            {getDatabaseIcon('mysql')}
                            MySQL
                          </Box>
                        </MenuItem>
                        <MenuItem value="postgresql">
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            {getDatabaseIcon('postgresql')}
                            PostgreSQL
                          </Box>
                        </MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>

                  <Grid size={{ xs: 12, md: 6 }}>
                    <TextField
                      fullWidth
                      label="Host"
                      value={config.host}
                      onChange={(e) => handleConfigChange('host', e.target.value)}
                      sx={{
                        '& .MuiOutlinedInput-root': {
                          color: 'white',
                          '& fieldset': {
                            borderColor: 'rgba(255,255,255,0.3)',
                          },
                          '&:hover fieldset': {
                            borderColor: 'rgba(255,255,255,0.5)',
                          },
                          '&.Mui-focused fieldset': {
                            borderColor: 'white',
                          },
                        },
                        '& .MuiInputLabel-root': {
                          color: 'rgba(255,255,255,0.7)',
                        },
                        '& .MuiInputLabel-root.Mui-focused': {
                          color: 'white',
                        },
                      }}
                    />
                  </Grid>

                  <Grid size={{ xs: 12, md: 6 }}>
                    <TextField
                      fullWidth
                      label="Puerto"
                      type="number"
                      value={config.port}
                      onChange={(e) => handleConfigChange('port', parseInt(e.target.value))}
                      sx={{
                        '& .MuiOutlinedInput-root': {
                          color: 'white',
                          '& fieldset': {
                            borderColor: 'rgba(255,255,255,0.3)',
                          },
                          '&:hover fieldset': {
                            borderColor: 'rgba(255,255,255,0.5)',
                          },
                          '&.Mui-focused fieldset': {
                            borderColor: 'white',
                          },
                        },
                        '& .MuiInputLabel-root': {
                          color: 'rgba(255,255,255,0.7)',
                        },
                        '& .MuiInputLabel-root.Mui-focused': {
                          color: 'white',
                        },
                      }}
                    />
                  </Grid>

                  <Grid size={{ xs: 12, md: 6 }}>
                    <TextField
                      fullWidth
                      label="Nombre de Base de Datos"
                      value={config.database}
                      onChange={(e) => handleConfigChange('database', e.target.value)}
                      sx={{
                        '& .MuiOutlinedInput-root': {
                          color: 'white',
                          '& fieldset': {
                            borderColor: 'rgba(255,255,255,0.3)',
                          },
                          '&:hover fieldset': {
                            borderColor: 'rgba(255,255,255,0.5)',
                          },
                          '&.Mui-focused fieldset': {
                            borderColor: 'white',
                          },
                        },
                        '& .MuiInputLabel-root': {
                          color: 'rgba(255,255,255,0.7)',
                        },
                        '& .MuiInputLabel-root.Mui-focused': {
                          color: 'white',
                        },
                      }}
                    />
                  </Grid>

                  <Grid size={{ xs: 12, md: 6 }}>
                    <TextField
                      fullWidth
                      label="Usuario"
                      value={config.username}
                      onChange={(e) => handleConfigChange('username', e.target.value)}
                      sx={{
                        '& .MuiOutlinedInput-root': {
                          color: 'white',
                          '& fieldset': {
                            borderColor: 'rgba(255,255,255,0.3)',
                          },
                          '&:hover fieldset': {
                            borderColor: 'rgba(255,255,255,0.5)',
                          },
                          '&.Mui-focused fieldset': {
                            borderColor: 'white',
                          },
                        },
                        '& .MuiInputLabel-root': {
                          color: 'rgba(255,255,255,0.7)',
                        },
                        '& .MuiInputLabel-root.Mui-focused': {
                          color: 'white',
                        },
                      }}
                    />
                  </Grid>

                  <Grid size={{ xs: 12, md: 6 }}>
                    <TextField
                      fullWidth
                      label="Contraseña"
                      type="password"
                      value={config.password}
                      onChange={(e) => handleConfigChange('password', e.target.value)}
                      sx={{
                        '& .MuiOutlinedInput-root': {
                          color: 'white',
                          '& fieldset': {
                            borderColor: 'rgba(255,255,255,0.3)',
                          },
                          '&:hover fieldset': {
                            borderColor: 'rgba(255,255,255,0.5)',
                          },
                          '&.Mui-focused fieldset': {
                            borderColor: 'white',
                          },
                        },
                        '& .MuiInputLabel-root': {
                          color: 'rgba(255,255,255,0.7)',
                        },
                        '& .MuiInputLabel-root.Mui-focused': {
                          color: 'white',
                        },
                      }}
                    />
                  </Grid>

                  <Grid size={{ xs: 12 }}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={config.ssl}
                          onChange={(e) => handleConfigChange('ssl', e.target.checked)}
                          sx={{
                            '& .MuiSwitch-switchBase.Mui-checked': {
                              color: 'white',
                            },
                            '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
                              backgroundColor: 'rgba(255,255,255,0.3)',
                            },
                          }}
                        />
                      }
                      label="Usar SSL"
                      sx={{ color: 'white' }}
                    />
                  </Grid>
                </Grid>

                <Box sx={{ display: 'flex', gap: 2, mt: 4 }}>
                  <Button
                    variant="contained"
                    startIcon={<CheckIcon />}
                    onClick={testConnection}
                    disabled={loading}
                    sx={{
                      bgcolor: 'rgba(255,255,255,0.2)',
                      '&:hover': { bgcolor: 'rgba(255,255,255,0.3)' },
                      borderRadius: 2,
                    }}
                  >
                    {loading ? <CircularProgress size={20} /> : 'Probar Conexión'}
                  </Button>
                  <Button
                    variant="contained"
                    startIcon={<SettingsIcon />}
                    onClick={saveConfig}
                    disabled={loading}
                    sx={{
                      bgcolor: 'rgba(255,255,255,0.2)',
                      '&:hover': { bgcolor: 'rgba(255,255,255,0.3)' },
                      borderRadius: 2,
                    }}
                  >
                    Guardar Configuración
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Zoom>
        </Grid>

        {/* Estado de Conexión y Acciones */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Zoom in timeout={1200}>
            <Card
              sx={{
                borderRadius: 3,
                boxShadow: 4,
                background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                color: 'white',
                mb: 3,
              }}
            >
              <CardContent sx={{ p: 4 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                  <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)', mr: 2 }}>
                    {connectionStatus?.connected ? <CheckIcon /> : <ErrorIcon />}
                  </Avatar>
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    Estado de Conexión
                  </Typography>
                </Box>

                {connectionStatus ? (
                  <Box>
                    <Typography variant="body2" sx={{ mb: 2, opacity: 0.9 }}>
                      {connectionStatus.message}
                    </Typography>
                    
                    {connectionStatus.connected && connectionStatus.tables && (
                      <Box>
                        <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                          Tablas encontradas:
                        </Typography>
                        {connectionStatus.tables.map((table) => (
                          <Chip
                            key={table}
                            label={`${table} (${connectionStatus.recordCounts?.[table] || 0})`}
                            size="small"
                            sx={{
                              bgcolor: 'rgba(255,255,255,0.2)',
                              color: 'white',
                              mr: 1,
                              mb: 1,
                            }}
                          />
                        ))}
                      </Box>
                    )}
                  </Box>
                ) : (
                  <Typography variant="body2" sx={{ opacity: 0.7 }}>
                    No se ha probado la conexión aún
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Zoom>

          <Zoom in timeout={1400}>
            <Card
              sx={{
                borderRadius: 3,
                boxShadow: 4,
                background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
                color: 'white',
              }}
            >
              <CardContent sx={{ p: 4 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                  <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)', mr: 2 }}>
                    <DownloadIcon />
                  </Avatar>
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    Descargar Datos
                  </Typography>
                </Box>

                <Typography variant="body2" sx={{ mb: 3, opacity: 0.9 }}>
                  Descarga todos los datos de tu base de datos configurada
                </Typography>

                <Button
                  variant="contained"
                  fullWidth
                  startIcon={<DownloadIcon />}
                  onClick={downloadData}
                  disabled={loading || !connectionStatus?.connected}
                  sx={{
                    bgcolor: 'rgba(255,255,255,0.2)',
                    '&:hover': { bgcolor: 'rgba(255,255,255,0.3)' },
                    borderRadius: 2,
                    py: 1.5,
                  }}
                >
                  {loading ? <CircularProgress size={20} /> : 'Descargar Datos'}
                </Button>
              </CardContent>
            </Card>
          </Zoom>
        </Grid>
      </Grid>
    </Container>
  );
};

export default DatabaseConfig;
