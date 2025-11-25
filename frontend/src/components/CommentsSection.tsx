import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  Card,
  CardContent,
  Divider,
  Avatar,
  CircularProgress,
  Alert,
  IconButton,
} from '@mui/material';
import {
  Send as SendIcon,
  Delete as DeleteIcon,
  Person as PersonIcon,
} from '@mui/icons-material';
import { apiService } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

interface Comment {
  id: number;
  article_id: number;
  user_name: string;
  comment_text: string;
  created_at: string;
  updated_at?: string;
  is_edited?: boolean;
}

interface CommentsSectionProps {
  articleId: number;
}

const CommentsSection: React.FC<CommentsSectionProps> = ({ articleId }) => {
  const { isAdmin } = useAuth();
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [userName, setUserName] = useState('');
  const [commentText, setCommentText] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchComments();
  }, [articleId]);

  const fetchComments = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiService.getComments(articleId) as { comments?: Comment[] };
      setComments(response.comments || []);
    } catch (err: any) {
      console.error('Error cargando comentarios:', err);
      setError('Error cargando comentarios');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!userName.trim() || !commentText.trim()) {
      setError('Por favor completa todos los campos');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      const response = await apiService.createComment({
        article_id: articleId,
        user_name: userName.trim(),
        comment_text: commentText.trim(),
      }) as { success?: boolean; comment?: Comment };

      if (response.success && response.comment) {
        setComments([response.comment, ...comments]);
        setCommentText('');
        setError(null);
      }
    } catch (err: any) {
      console.error('Error creando comentario:', err);
      setError(err.response?.data?.error || 'Error al publicar comentario');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (commentId: number) => {
    if (!window.confirm('¿Estás seguro de eliminar este comentario?')) {
      return;
    }

    try {
      await apiService.deleteComment(commentId);
      setComments(comments.filter(c => c.id !== commentId));
    } catch (err: any) {
      console.error('Error eliminando comentario:', err);
      setError('Error al eliminar comentario');
    }
  };

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('es-ES', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateString;
    }
  };

  return (
    <Box sx={{ mt: 3 }}>
      <Typography variant="h6" gutterBottom sx={{ mb: 2, fontWeight: 600 }}>
        💬 Comentarios y Opiniones ({comments.length})
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Formulario para nuevo comentario */}
      <Card sx={{ mb: 3, bgcolor: 'background.paper' }}>
        <CardContent>
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
            <TextField
              fullWidth
              label="Tu comentario"
              value={commentText}
              onChange={(e) => setCommentText(e.target.value)}
              margin="normal"
              required
              multiline
              rows={3}
              placeholder="Escribe tu opinión sobre esta noticia..."
              inputProps={{ maxLength: 2000 }}
              helperText={`${commentText.length}/2000 caracteres`}
            />
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
              <Button
                type="submit"
                variant="contained"
                startIcon={<SendIcon />}
                disabled={submitting || !userName.trim() || !commentText.trim()}
              >
                {submitting ? 'Publicando...' : 'Publicar Comentario'}
              </Button>
            </Box>
          </form>
        </CardContent>
      </Card>

      {/* Lista de comentarios */}
      {loading ? (
        <Box display="flex" justifyContent="center" py={4}>
          <CircularProgress />
        </Box>
      ) : comments.length === 0 ? (
        <Card>
          <CardContent>
            <Typography variant="body2" color="text.secondary" align="center" py={2}>
              No hay comentarios aún. ¡Sé el primero en opinar!
            </Typography>
          </CardContent>
        </Card>
      ) : (
        <Box>
          {comments.map((comment, index) => (
            <React.Fragment key={comment.id}>
              <Card sx={{ mb: 2, bgcolor: 'background.paper' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                    <Avatar sx={{ bgcolor: 'primary.main' }}>
                      <PersonIcon />
                    </Avatar>
                    <Box sx={{ flex: 1 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                        <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                          {comment.user_name}
                        </Typography>
                        {isAdmin && (
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => handleDelete(comment.id)}
                            sx={{ ml: 1 }}
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        )}
                      </Box>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1, fontSize: '0.75rem' }}>
                        {formatDate(comment.created_at)}
                        {comment.is_edited && ' • Editado'}
                      </Typography>
                      <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                        {comment.comment_text}
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
              {index < comments.length - 1 && <Divider sx={{ my: 1 }} />}
            </React.Fragment>
          ))}
        </Box>
      )}
    </Box>
  );
};

export default CommentsSection;

