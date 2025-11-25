import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Avatar,
  Chip,
  Divider,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  IconButton,
} from '@mui/material';
import {
  TrendingUp as TrendingIcon,
  ThumbUp as ThumbUpIcon,
  Comment as CommentIcon,
  Person as PersonIcon,
  Send as SendIcon,
} from '@mui/icons-material';
import { apiService } from '../services/api';

interface ViralComment {
  id: number;
  user_name: string;
  comment_text: string;
  topic: string;
  likes: number;
  created_at: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  sentiment_score?: number;
  emotions?: Record<string, number>;
}

const ViralComments: React.FC = () => {
  const [comments, setComments] = useState<ViralComment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [userName, setUserName] = useState('');
  const [commentText, setCommentText] = useState('');
  const [selectedTopic, setSelectedTopic] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const topics = [
    'Medio Ambiente',
    'Política',
    'Tecnología',
    'Economía',
    'Salud',
    'Educación',
    'Deportes',
    'Cultura',
  ];

  useEffect(() => {
    fetchViralComments();
  }, []);

  const fetchViralComments = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiService.getViralComments(undefined, 10) as { comments?: ViralComment[] };
      
      // Si no hay comentarios en la BD, usar los mock iniciales
      if (response.comments && response.comments.length > 0) {
        setComments(response.comments);
      } else {
        // Cargar comentarios mock iniciales
        const mockComments: ViralComment[] = [
      {
        id: 1,
        user_name: 'María González',
        comment_text: '¡Excelente noticia! Es importante que se tomen medidas para proteger el medio ambiente. Todos debemos contribuir.',
        topic: 'Medio Ambiente',
        likes: 234,
        created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        sentiment: 'positive' as const,
      },
      {
        id: 2,
        user_name: 'Carlos Ramírez',
        comment_text: 'Me parece genial que se estén implementando estas políticas. El futuro se ve prometedor con estos cambios.',
        topic: 'Política',
        likes: 189,
        created_at: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
        sentiment: 'positive' as const,
      },
      {
        id: 3,
        user_name: 'Ana Martínez',
        comment_text: 'Finalmente una solución real a este problema. Llevábamos años esperando algo así. ¡Bravo!',
        topic: 'Tecnología',
        likes: 312,
        created_at: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
        sentiment: 'positive' as const,
      },
      {
        id: 4,
        user_name: 'Luis Fernández',
        comment_text: 'Esto es exactamente lo que necesitábamos. Un paso adelante hacia un futuro mejor para todos.',
        topic: 'Economía',
        likes: 156,
        created_at: new Date(Date.now() - 8 * 60 * 60 * 1000).toISOString(),
        sentiment: 'positive' as const,
      },
      {
        id: 5,
        user_name: 'Sofía López',
        comment_text: 'Me encanta ver este tipo de iniciativas. Demuestra que sí se puede hacer la diferencia cuando hay voluntad.',
        topic: 'Salud',
        likes: 278,
        created_at: new Date(Date.now() - 10 * 60 * 60 * 1000).toISOString(),
        sentiment: 'positive' as const,
      },
      {
        id: 6,
        user_name: 'Diego Torres',
        comment_text: 'Increíble avance. Esto va a cambiar muchas vidas para mejor. Estoy muy optimista al respecto.',
        topic: 'Educación',
        likes: 201,
        created_at: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString(),
        sentiment: 'positive' as const,
      },
    ];
        setComments(mockComments);
      }
    } catch (err: any) {
      console.error('Error cargando comentarios virales:', err);
      // Si hay error, usar comentarios mock
      const mockComments: ViralComment[] = [
        {
          id: 1,
          user_name: 'María González',
          comment_text: '¡Excelente noticia! Es importante que se tomen medidas para proteger el medio ambiente. Todos debemos contribuir.',
          topic: 'Medio Ambiente',
          likes: 234,
          created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
          sentiment: 'positive' as const,
        },
        {
          id: 2,
          user_name: 'Carlos Ramírez',
          comment_text: 'Me parece genial que se estén implementando estas políticas. El futuro se ve prometedor con estos cambios.',
          topic: 'Política',
          likes: 189,
          created_at: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
          sentiment: 'positive' as const,
        },
      ];
      setComments(mockComments);
      setError('Error cargando comentarios. Mostrando comentarios de ejemplo.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!userName.trim() || !commentText.trim() || !selectedTopic) {
      setError('Por favor completa todos los campos');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      const response = await apiService.createViralComment({
        user_name: userName.trim(),
        comment_text: commentText.trim(),
        topic: selectedTopic,
      }) as { success?: boolean; comment?: ViralComment };

      if (response.success && response.comment) {
        setComments([response.comment, ...comments]);
        setCommentText('');
        setUserName('');
        setSelectedTopic('');
        setShowForm(false);
        setError(null);
      }
    } catch (err: any) {
      console.error('Error creando comentario viral:', err);
      setError(err.response?.data?.error || 'Error al publicar comentario');
    } finally {
      setSubmitting(false);
    }
  };

  const handleLike = async (commentId: number) => {
    try {
      await apiService.likeViralComment(commentId);
      // Actualizar el comentario en la lista
      setComments(comments.map(c => 
        c.id === commentId ? { ...c, likes: c.likes + 1 } : c
      ));
    } catch (err) {
      console.error('Error dando like:', err);
    }
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
    
    if (diffInHours < 1) {
      return 'Hace menos de 1 hora';
    } else if (diffInHours < 24) {
      return `Hace ${diffInHours} hora${diffInHours > 1 ? 's' : ''}`;
    } else {
      const diffInDays = Math.floor(diffInHours / 24);
      return `Hace ${diffInDays} día${diffInDays > 1 ? 's' : ''}`;
    }
  };

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const getSentimentConfig = (sentiment: string) => {
    switch (sentiment) {
      case 'positive':
        return {
          label: 'Positivo',
          color: 'success' as const,
          bgColor: 'success.light',
          textColor: 'success.contrastText',
        };
      case 'negative':
        return {
          label: 'Negativo',
          color: 'error' as const,
          bgColor: 'error.light',
          textColor: 'error.contrastText',
        };
      case 'neutral':
      default:
        return {
          label: 'Neutral',
          color: 'default' as const,
          bgColor: 'grey.300',
          textColor: 'grey.800',
        };
    }
  };

  return (
    <Card
      sx={{
        height: { xs: 'auto', md: 500 },
        maxWidth: { xs: '100%', md: 600 },
        mx: 'auto',
        borderRadius: 3,
        boxShadow: 4,
        display: 'flex',
        flexDirection: 'column',
        background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
        border: '1px solid rgba(0,0,0,0.08)',
      }}
    >
      <CardContent sx={{ p: 3, flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {/* Header */}
        <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
          <TrendingIcon sx={{ color: 'primary.main', fontSize: 28 }} />
          <Typography variant="h5" sx={{ fontWeight: 700, flex: 1 }}>
            💬 Comentarios Virales
          </Typography>
          <Chip
            label="En Vivo"
            color="success"
            size="small"
            sx={{ fontWeight: 600 }}
          />
        </Box>

        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Opiniones destacadas sobre temas de actualidad
        </Typography>

        {/* Botón para agregar comentario */}
        {!showForm && (
          <Button
            variant="contained"
            fullWidth
            startIcon={<CommentIcon />}
            onClick={() => setShowForm(true)}
            sx={{ mb: 2 }}
          >
            Agregar tu Comentario
          </Button>
        )}

        {/* Formulario para nuevo comentario */}
        {showForm && (
          <Card sx={{ mb: 2, bgcolor: 'background.paper', border: '1px solid', borderColor: 'primary.main' }}>
            <CardContent>
              {error && (
                <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
                  {error}
                </Alert>
              )}
              <form onSubmit={handleSubmit}>
                <TextField
                  fullWidth
                  label="Tu nombre"
                  value={userName}
                  onChange={(e) => setUserName(e.target.value)}
                  margin="normal"
                  required
                  size="small"
                  placeholder="Ej: Juan Pérez"
                />
                <FormControl fullWidth margin="normal" size="small" required>
                  <InputLabel>Tema</InputLabel>
                  <Select
                    value={selectedTopic}
                    onChange={(e) => setSelectedTopic(e.target.value)}
                    label="Tema"
                  >
                    {topics.map((topic) => (
                      <MenuItem key={topic} value={topic}>
                        {topic}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <TextField
                  fullWidth
                  label="Tu comentario"
                  value={commentText}
                  onChange={(e) => setCommentText(e.target.value)}
                  margin="normal"
                  required
                  multiline
                  rows={3}
                  placeholder="Escribe tu opinión sobre este tema..."
                  inputProps={{ maxLength: 2000 }}
                  helperText={`${commentText.length}/2000 caracteres`}
                />
                <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
                  <Button
                    type="submit"
                    variant="contained"
                    startIcon={<SendIcon />}
                    disabled={submitting || !userName.trim() || !commentText.trim() || !selectedTopic}
                    sx={{ flex: 1 }}
                  >
                    {submitting ? 'Publicando...' : 'Publicar'}
                  </Button>
                  <Button
                    variant="outlined"
                    onClick={() => {
                      setShowForm(false);
                      setError(null);
                      setCommentText('');
                      setUserName('');
                      setSelectedTopic('');
                    }}
                  >
                    Cancelar
                  </Button>
                </Box>
              </form>
            </CardContent>
          </Card>
        )}

        {/* Lista de comentarios */}
        <Box
          sx={{
            flex: 1,
            overflowY: 'auto',
            pr: 1,
            '&::-webkit-scrollbar': {
              width: '6px',
            },
            '&::-webkit-scrollbar-track': {
              background: '#f1f1f1',
              borderRadius: '10px',
            },
            '&::-webkit-scrollbar-thumb': {
              background: '#888',
              borderRadius: '10px',
              '&:hover': {
                background: '#555',
              },
            },
          }}
        >
          {comments.map((comment, index) => (
            <React.Fragment key={comment.id}>
              <Box
                sx={{
                  mb: 2,
                  p: 2,
                  borderRadius: 2,
                  bgcolor: 'background.paper',
                  border: '1px solid rgba(0,0,0,0.05)',
                  transition: 'all 0.2s ease',
                  '&:hover': {
                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                    transform: 'translateY(-2px)',
                  },
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2, mb: 1.5 }}>
                  <Avatar
                    sx={{
                      bgcolor: 'primary.main',
                      width: 40,
                      height: 40,
                      fontSize: '0.9rem',
                      fontWeight: 600,
                    }}
                  >
                    {getInitials(comment.user_name)}
                  </Avatar>
                  <Box sx={{ flex: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                      <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                        {comment.user_name}
                      </Typography>
                      <Chip
                        label={comment.topic}
                        size="small"
                        sx={{
                          height: 20,
                          fontSize: '0.7rem',
                          bgcolor: 'primary.light',
                          color: 'primary.contrastText',
                        }}
                      />
                    </Box>
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{ fontSize: '0.75rem', mb: 1 }}
                    >
                      {formatTimeAgo(comment.created_at)}
                    </Typography>
                    <Typography
                      variant="body2"
                      sx={{
                        lineHeight: 1.6,
                        color: 'text.primary',
                        mb: 1,
                      }}
                    >
                      {comment.comment_text}
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                      <IconButton
                        size="small"
                        onClick={() => handleLike(comment.id)}
                        sx={{
                          color: 'success.main',
                          '&:hover': {
                            bgcolor: 'success.light',
                            color: 'success.contrastText',
                          },
                        }}
                      >
                        <ThumbUpIcon sx={{ fontSize: 16 }} />
                      </IconButton>
                      <Typography variant="caption" sx={{ fontWeight: 600, color: 'success.main' }}>
                        {comment.likes}
                      </Typography>
                      {(() => {
                        const sentimentConfig = getSentimentConfig(comment.sentiment || 'neutral');
                        return (
                          <Chip
                            icon={<CommentIcon sx={{ fontSize: 14 }} />}
                            label={sentimentConfig.label}
                            size="small"
                            sx={{
                              height: 22,
                              fontSize: '0.7rem',
                              bgcolor: sentimentConfig.bgColor,
                              color: sentimentConfig.textColor,
                              '& .MuiChip-icon': {
                                color: sentimentConfig.textColor,
                              },
                            }}
                          />
                        );
                      })()}
                    </Box>
                  </Box>
                </Box>
              </Box>
              {index < comments.length - 1 && (
                <Divider sx={{ my: 1, opacity: 0.3 }} />
              )}
            </React.Fragment>
          ))}
        </Box>
      </CardContent>
    </Card>
  );
};

export default ViralComments;

