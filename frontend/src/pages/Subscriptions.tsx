import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Avatar,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Star as StarIcon,
  Check as CheckIcon,
  Payment as PaymentIcon,
  Image as ImageIcon,
  Article as ArticleIcon,
  Receipt as ReceiptIcon,
  Refresh as RefreshIcon,
  ContentCopy as CopyIcon,
  WhatsApp as WhatsAppIcon,
  Email as EmailIcon,
} from '@mui/icons-material';
import { api } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

interface Plan {
  id: number;
  name: string;
  display_name: string;
  price: number;
  currency: string;
  max_articles_per_day: number;
  max_images_per_scraping: number;
  max_users: number;
  features: string[];
  is_active: boolean;
}

interface UserSubscription {
  id: number;
  plan_id: number;
  status: string;
  start_date: string;
  end_date: string;
  plan_name: string;
  plan_display_name: string;
  max_articles_per_day: number;
  max_images_per_scraping: number;
  max_users: number;
  features: string[];
}

interface PaymentCode {
  id: number;
  code: string;
  amount: number;
  currency: string;
  status: string;
  created_at: string;
  expires_at: string;
  plan_name: string;
}

interface UsageLimits {
  allowed: boolean;
  current_articles: number;
  current_images: number;
  max_articles: number;
  max_images: number;
  plan_name: string;
  reason?: string;
}

const Subscriptions: React.FC = () => {
  // const { user: currentUser } = useAuth(); // Comentado temporalmente
  const [plans, setPlans] = useState<Plan[]>([]);
  const [userSubscription, setUserSubscription] = useState<UserSubscription | null>(null);
  const [paymentCodes, setPaymentCodes] = useState<PaymentCode[]>([]);
  const [usageLimits, setUsageLimits] = useState<UsageLimits | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [paymentDialogOpen, setPaymentDialogOpen] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<Plan | null>(null);
  const [creatingPayment, setCreatingPayment] = useState(false);
  const [paymentCreated, setPaymentCreated] = useState<any>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);

    try {
      const [plansResponse, subscriptionResponse, paymentCodesResponse, limitsResponse] = await Promise.all([
        api.get('/subscriptions/plans'),
        api.get('/subscriptions/user-subscription'),
        api.get('/subscriptions/payment-codes'),
        api.get('/subscriptions/usage-limits')
      ]);

      setPlans((plansResponse.data as any).plans);
      setUserSubscription((subscriptionResponse.data as any).subscription);
      setPaymentCodes((paymentCodesResponse.data as any).payment_codes);
      setUsageLimits((limitsResponse.data as any).limits);
    } catch (err) {
      setError('Error cargando datos de suscripciones');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreatePayment = async (plan: Plan) => {
    setSelectedPlan(plan);
    setCreatingPayment(true);
    setError(null);

    try {
      const response = await api.post('/subscriptions/create-payment', {
        plan_id: plan.id
      });

      setPaymentCreated((response.data as any).payment_code);
      setPaymentDialogOpen(true);
    } catch (err) {
      setError('Error creando código de pago');
      console.error('Error:', err);
    } finally {
      setCreatingPayment(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const formatCurrency = (amount: number, currency: string) => {
    return new Intl.NumberFormat('es-PE', {
      style: 'currency',
      currency: currency === 'USD' ? 'USD' : 'PEN'
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('es-PE');
  };

  const getTimeRemaining = (expiresAt: string) => {
    const now = new Date();
    const expires = new Date(expiresAt);
    const diff = expires.getTime() - now.getTime();
    
    if (diff <= 0) return 'Expirado';
    
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    
    if (days > 0) return `${days}d ${hours}h`;
    return `${hours}h`;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'paid': return 'success';
      case 'pending': return 'warning';
      case 'expired': return 'error';
      case 'cancelled': return 'default';
      default: return 'default';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'paid': return 'Pagado';
      case 'pending': return 'Pendiente';
      case 'expired': return 'Expirado';
      case 'cancelled': return 'Cancelado';
      default: return status;
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ fontWeight: 'bold', color: '#333' }}>
        Planes y Suscripciones
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Suscripción Actual */}
      {userSubscription && (
        <Card elevation={2} sx={{ mb: 4, border: '2px solid', borderColor: 'primary.main' }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                <StarIcon />
              </Avatar>
              <Box>
                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                  Plan Actual: {userSubscription.plan_display_name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Válido hasta: {formatDate(userSubscription.end_date)}
                </Typography>
              </Box>
            </Box>
            
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
              <Box sx={{ flex: '1 1 200px', textAlign: 'center' }}>
                <Typography variant="h4" color="primary" sx={{ fontWeight: 'bold' }}>
                  {userSubscription.max_articles_per_day === -1 ? '∞' : userSubscription.max_articles_per_day}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Artículos por día
                </Typography>
              </Box>
              <Box sx={{ flex: '1 1 200px', textAlign: 'center' }}>
                <Typography variant="h4" color="primary" sx={{ fontWeight: 'bold' }}>
                  {userSubscription.max_images_per_scraping === -1 ? '∞' : userSubscription.max_images_per_scraping}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Imágenes por scraping
                </Typography>
              </Box>
              <Box sx={{ flex: '1 1 200px', textAlign: 'center' }}>
                <Typography variant="h4" color="primary" sx={{ fontWeight: 'bold' }}>
                  {userSubscription.max_users === -1 ? '∞' : userSubscription.max_users}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Usuarios
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Límites de Uso Actuales */}
      {usageLimits && (
        <Card elevation={2} sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold' }}>
              Uso Actual del Día
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
              <Box sx={{ flex: '1 1 300px' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <ArticleIcon color="primary" sx={{ mr: 2 }} />
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="body1">
                      Artículos: {usageLimits.current_articles} / {usageLimits.max_articles === -1 ? '∞' : usageLimits.max_articles}
                    </Typography>
                    <Box sx={{ width: '100%', bgcolor: 'grey.200', borderRadius: 1, height: 8, mt: 1 }}>
                      <Box
                        sx={{
                          width: `${usageLimits.max_articles === -1 ? 0 : (usageLimits.current_articles / usageLimits.max_articles) * 100}%`,
                          bgcolor: 'primary.main',
                          height: '100%',
                          borderRadius: 1,
                        }}
                      />
                    </Box>
                  </Box>
                </Box>
              </Box>
              <Box sx={{ flex: '1 1 300px' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <ImageIcon color="primary" sx={{ mr: 2 }} />
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="body1">
                      Imágenes: {usageLimits.current_images} / {usageLimits.max_images === -1 ? '∞' : usageLimits.max_images}
                    </Typography>
                    <Box sx={{ width: '100%', bgcolor: 'grey.200', borderRadius: 1, height: 8, mt: 1 }}>
                      <Box
                        sx={{
                          width: `${usageLimits.max_images === -1 ? 0 : (usageLimits.current_images / usageLimits.max_images) * 100}%`,
                          bgcolor: 'secondary.main',
                          height: '100%',
                          borderRadius: 1,
                        }}
                      />
                    </Box>
                  </Box>
                </Box>
              </Box>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Planes Disponibles */}
      <Typography variant="h5" gutterBottom sx={{ fontWeight: 'bold', mb: 3 }}>
        Planes Disponibles
      </Typography>

      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3, mb: 4 }}>
        {plans.map((plan) => (
          <Box key={plan.id} sx={{ flex: '1 1 300px', minWidth: 300 }}>
            <Card 
              elevation={2} 
              sx={{ 
                height: '100%',
                position: 'relative',
                border: userSubscription?.plan_id === plan.id ? '2px solid' : '1px solid',
                borderColor: userSubscription?.plan_id === plan.id ? 'primary.main' : 'divider',
                '&:hover': {
                  elevation: 4,
                  transform: 'translateY(-4px)',
                  transition: 'all 0.3s ease-in-out'
                }
              }}
            >
              {userSubscription?.plan_id === plan.id && (
                <Chip
                  label="Plan Actual"
                  color="primary"
                  sx={{ position: 'absolute', top: 16, right: 16 }}
                />
              )}
              
              <CardContent sx={{ p: 3 }}>
                <Box sx={{ textAlign: 'center', mb: 3 }}>
                  <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 1 }}>
                    {plan.display_name}
                  </Typography>
                  <Typography variant="h3" color="primary" sx={{ fontWeight: 'bold' }}>
                    {plan.price === 0 ? 'Gratis' : formatCurrency(plan.price, plan.currency)}
                  </Typography>
                  {plan.price > 0 && (
                    <Typography variant="body2" color="text.secondary">
                      por mes
                    </Typography>
                  )}
                </Box>

                <List dense>
                  {(plan.name === 'freemium'
                    ? [
                        '50 artículos por día',
                        '10 imágenes por scraping',
                        'Chat básico (30 mensajes/día)',
                        'Búsqueda y resumen básicos',
                        'Estadísticas básicas (listas y KPIs simples)',
                        'Competitive Intelligence: 1 competidor',
                        'Trending Predictor: 0 predicciones/día',
                        '1 usuario por cuenta',
                        'Sin exportación ni auto‑update',
                        'Soporte por email'
                      ]
                    : plan.name === 'premium'
                    ? [
                        '500 artículos por día',
                        '100 imágenes por scraping',
                        'Chat avanzado (200 mensajes/día)',
                        'Resumen combinado y explicaciones guiadas',
                        'Estadísticas avanzadas (gráficos y comparativas)',
                        'Exportación Excel/CSV (UI y chat)',
                        'Consultas guardadas desde el chat',
                        'Competitive Intelligence: hasta 5 competidores',
                        'Trending Predictor: 5 predicciones/día',
                        'Hasta 5 usuarios por cuenta',
                        'Scraping programado (auto‑update desde UI)',
                        'Soporte prioritario'
                      ]
                    : [
                        'Artículos ilimitados',
                        'Imágenes ilimitadas',
                        'Chat sin límites y acciones completas',
                        'Exportación y auto‑update desde chat',
                        'Consultas guardadas + alertas por email',
                        'Competitive Intelligence: hasta 20 competidores',
                        'Trending Predictor: 20 predicciones/día',
                        'Usuarios ilimitados',
                        'API completa e integración con webhooks',
                        'Análisis de sentimientos avanzado',
                        'Soporte 24/7'
                      ]
                  ).map((feature, index) => (
                    <ListItem key={index} sx={{ px: 0 }}>
                      <ListItemIcon sx={{ minWidth: 32 }}>
                        <CheckIcon color="primary" sx={{ fontSize: 20 }} />
                      </ListItemIcon>
                      <ListItemText
                        primary={feature}
                        primaryTypographyProps={{ variant: 'body2' }}
                      />
                    </ListItem>
                  ))}
                </List>

                <Box sx={{ mt: 3 }}>
                  <Button
                    fullWidth
                    variant={userSubscription?.plan_id === plan.id ? "outlined" : "contained"}
                    color="primary"
                    size="large"
                    onClick={() => handleCreatePayment(plan)}
                    disabled={creatingPayment || userSubscription?.plan_id === plan.id}
                    startIcon={creatingPayment ? <CircularProgress size={20} /> : <PaymentIcon />}
                  >
                    {userSubscription?.plan_id === plan.id 
                      ? 'Plan Actual' 
                      : plan.price === 0 
                        ? 'Activar Gratis' 
                        : 'Suscribirse'
                    }
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Box>
        ))}
      </Box>

      {/* Historial de Pagos */}
      <Card elevation={2}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
              Historial de Pagos
            </Typography>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={fetchData}
              disabled={loading}
            >
              Actualizar
            </Button>
          </Box>

          {paymentCodes.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <ReceiptIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary">
                No hay pagos registrados
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Los códigos de pago aparecerán aquí una vez que los crees
              </Typography>
            </Box>
          ) : (
            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Código</TableCell>
                    <TableCell>Plan</TableCell>
                    <TableCell>Monto</TableCell>
                    <TableCell>Estado</TableCell>
                    <TableCell>Fecha</TableCell>
                    <TableCell>Expira</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {paymentCodes.map((payment) => (
                    <TableRow key={payment.id}>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 'bold', mr: 1 }}>
                            {payment.code}
                          </Typography>
                          <Tooltip title="Copiar código">
                            <IconButton
                              size="small"
                              onClick={() => copyToClipboard(payment.code)}
                            >
                              <CopyIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip label={payment.plan_name} color="primary" variant="outlined" size="small" />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                          {formatCurrency(payment.amount, payment.currency)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={getStatusText(payment.status)}
                          color={getStatusColor(payment.status) as any}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {formatDate(payment.created_at)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {getTimeRemaining(payment.expires_at)}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>

      {/* Dialog de Pago */}
      <Dialog open={paymentDialogOpen} onClose={() => setPaymentDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <PaymentIcon color="primary" sx={{ mr: 1 }} />
            Instrucciones de Pago
          </Box>
        </DialogTitle>
        <DialogContent>
          {paymentCreated && selectedPlan && (
            <Box>
              <Alert severity="info" sx={{ mb: 3 }}>
                <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                  Para activar tu suscripción, realiza el pago y envía el comprobante
                </Typography>
              </Alert>

              <Paper elevation={1} sx={{ p: 3, mb: 3, bgcolor: 'grey.50' }}>
                <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold' }}>
                  Detalles del Pago
                </Typography>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body1">Plan:</Typography>
                  <Typography variant="body1" sx={{ fontWeight: 'bold' }}>{selectedPlan.display_name}</Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body1">Monto:</Typography>
                  <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                    {formatCurrency(paymentCreated.amount, paymentCreated.currency)}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body1">Código:</Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Typography variant="body1" sx={{ fontFamily: 'monospace', fontWeight: 'bold', mr: 1 }}>
                      {paymentCreated.code}
                    </Typography>
                    <Tooltip title="Copiar código">
                      <IconButton size="small" onClick={() => copyToClipboard(paymentCreated.code)}>
                        <CopyIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body1">Expira:</Typography>
                  <Typography variant="body1" color="warning.main" sx={{ fontWeight: 'bold' }}>
                    {formatDate(paymentCreated.expires_at)}
                  </Typography>
                </Box>
              </Paper>

              <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold' }}>
                Instrucciones de Pago
              </Typography>
              <List>
                <ListItem>
                  <ListItemIcon>
                    <Typography variant="h6" color="primary">1</Typography>
                  </ListItemIcon>
                  <ListItemText 
                    primary="Realiza la transferencia por el monto exacto"
                    secondary="Usa el código de pago como referencia"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <Typography variant="h6" color="primary">2</Typography>
                  </ListItemIcon>
                  <ListItemText 
                    primary="Envía el comprobante de pago"
                    secondary="WhatsApp: +51 955 867 498 o Email: alexcjlegion@gmail.com"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <Typography variant="h6" color="primary">3</Typography>
                  </ListItemIcon>
                  <ListItemText 
                    primary="Espera la verificación"
                    secondary="Tu suscripción se activará en menos de 24 horas"
                  />
                </ListItem>
              </List>

              <Box sx={{ display: 'flex', gap: 2, mt: 3 }}>
                <Button
                  variant="outlined"
                  startIcon={<WhatsAppIcon />}
                  onClick={() => window.open('https://wa.me/51955867498?text=Hola, tengo un comprobante de pago para el código ' + paymentCreated.code)}
                >
                  Enviar por WhatsApp
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<EmailIcon />}
                  onClick={() => window.open('mailto:alexcjlegion@gmail.com?subject=Comprobante de Pago - ' + paymentCreated.code)}
                >
                  Enviar por Email
                </Button>
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPaymentDialogOpen(false)}>
            Cerrar
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Subscriptions;
