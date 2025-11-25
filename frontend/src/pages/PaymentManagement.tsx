import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  CircularProgress,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Avatar,
  Tooltip,
} from '@mui/material';
import {
  Payment as PaymentIcon,
  CheckCircle as CheckIcon,
  Refresh as RefreshIcon,
  AttachMoney as MoneyIcon,
  People as PeopleIcon,
  TrendingUp as TrendingUpIcon,
  Receipt as ReceiptIcon,
  Warning as WarningIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';
import { api } from '../services/api';

interface PendingPayment {
  id: number;
  code: string;
  user_id: number;
  plan_id: number;
  amount: number;
  currency: string;
  created_at: string;
  expires_at: string;
  payment_proof: string;
  username: string;
  plan_name: string;
}

interface SubscriptionStats {
  subscription_stats: Array<{
    plan_name: string;
    active_subscriptions: number;
  }>;
  pending_payments: {
    count: number;
    total_amount: number;
  };
  daily_usage: {
    active_users: number;
    total_articles: number;
    total_images: number;
  };
}

const PaymentManagement: React.FC = () => {
  const [pendingPayments, setPendingPayments] = useState<PendingPayment[]>([]);
  const [subscriptionStats, setSubscriptionStats] = useState<SubscriptionStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [verifyDialogOpen, setVerifyDialogOpen] = useState(false);
  const [selectedPayment, setSelectedPayment] = useState<PendingPayment | null>(null);
  const [paymentProof, setPaymentProof] = useState('');
  const [verifying, setVerifying] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    setError(null);

    // Cargar pagos pendientes
    try {
      const paymentsResponse = await api.get('/admin/pending-payments');
      const paymentsData = paymentsResponse.data as any;
      if (paymentsData && paymentsData.success !== false) {
        setPendingPayments(paymentsData.pending_payments || []);
      } else {
        setPendingPayments([]);
      }
    } catch (err: any) {
      console.error('Error cargando pagos pendientes:', err);
      // Si falla, establecer lista vacía pero no mostrar error crítico
      setPendingPayments([]);
    }

    // Cargar estadísticas de suscripciones
    try {
      const statsResponse = await api.get('/admin/subscription-stats');
      const statsData = statsResponse.data as any;
      if (statsData && statsData.success !== false) {
        const subscriptionStatsData = statsData.stats || statsData;
        setSubscriptionStats(subscriptionStatsData);
      } else {
        setSubscriptionStats(null);
        // Si la respuesta no tiene éxito pero no es un error HTTP, no mostrar error
        if (statsData?.error) {
          setError('Error obteniendo estadísticas');
        }
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.error || err.message || 'Error obteniendo estadísticas';
      setError(errorMessage);
      console.error('Error cargando estadísticas:', err);
      setSubscriptionStats(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleVerifyPayment = async () => {
    if (!selectedPayment) return;

    setVerifying(true);
    try {
      await api.post('/admin/verify-payment', {
        payment_code: selectedPayment.code,
        payment_proof: paymentProof
      });

      setVerifyDialogOpen(false);
      setSelectedPayment(null);
      setPaymentProof('');
      await fetchData(); // Recargar datos
    } catch (err) {
      setError('Error verificando pago');
      console.error('Error:', err);
    } finally {
      setVerifying(false);
    }
  };

  const openVerifyDialog = (payment: PendingPayment) => {
    setSelectedPayment(payment);
    setPaymentProof(payment.payment_proof || '');
    setVerifyDialogOpen(true);
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

  const isExpired = (expiresAt: string) => {
    return new Date(expiresAt) < new Date();
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
      <Typography 
        variant="h4" 
        gutterBottom 
        sx={{ 
          fontWeight: 700, 
          background: 'linear-gradient(45deg, #1976d2, #42a5f5)',
          backgroundClip: 'text',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          mb: 3,
        }}
      >
        Gestión de Pagos y Suscripciones
      </Typography>

      {error && (
        <Alert 
          severity="error" 
          sx={{ 
            mb: 3, 
            borderRadius: 2,
            '& .MuiAlert-icon': {
              fontSize: 28,
            },
          }}
          onClose={() => setError(null)}
        >
          {error}
        </Alert>
      )}

      {/* Estadísticas Generales */}
      {subscriptionStats && (
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3, mb: 4 }}>
          <Box sx={{ flex: '1 1 200px', minWidth: 200 }}>
            <Card elevation={2}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                    <PeopleIcon />
                  </Avatar>
                  <Box>
                    <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                      {subscriptionStats.pending_payments.count}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Pagos Pendientes
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Box>

          <Box sx={{ flex: '1 1 200px', minWidth: 200 }}>
            <Card elevation={2}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Avatar sx={{ bgcolor: 'success.main', mr: 2 }}>
                    <MoneyIcon />
                  </Avatar>
                  <Box>
                    <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                      {formatCurrency(subscriptionStats.pending_payments.total_amount, 'USD')}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Monto Pendiente
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Box>

          <Box sx={{ flex: '1 1 200px', minWidth: 200 }}>
            <Card elevation={2}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Avatar sx={{ bgcolor: 'info.main', mr: 2 }}>
                    <TrendingUpIcon />
                  </Avatar>
                  <Box>
                    <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                      {subscriptionStats.daily_usage.active_users}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Usuarios Activos Hoy
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Box>

          <Box sx={{ flex: '1 1 200px', minWidth: 200 }}>
            <Card elevation={2}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Avatar sx={{ bgcolor: 'warning.main', mr: 2 }}>
                    <ReceiptIcon />
                  </Avatar>
                  <Box>
                    <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                      {subscriptionStats.daily_usage.total_articles}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Artículos Hoy
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Box>
        </Box>
      )}

      {/* Estadísticas de Planes */}
      {subscriptionStats && (
        <Card elevation={2} sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold' }}>
              Suscripciones Activas por Plan
            </Typography>
            <List>
              {subscriptionStats.subscription_stats.map((stat, index) => (
                <ListItem key={index} divider>
                  <ListItemIcon>
                    <PaymentIcon color="primary" />
                  </ListItemIcon>
                  <ListItemText
                    primary={stat.plan_name}
                    secondary={`${stat.active_subscriptions} suscripciones activas`}
                  />
                  <Chip 
                    label={stat.active_subscriptions} 
                    color="primary" 
                    variant="outlined"
                  />
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      {/* Pagos Pendientes */}
      <Card elevation={2}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
              Pagos Pendientes de Verificación
            </Typography>
            <Button
              variant="contained"
              startIcon={<RefreshIcon />}
              onClick={fetchData}
              disabled={loading}
              sx={{
                borderRadius: 2,
                px: 3,
                textTransform: 'none',
                background: 'linear-gradient(45deg, #1976d2, #42a5f5)',
                '&:hover': {
                  background: 'linear-gradient(45deg, #1565c0, #1976d2)',
                },
              }}
            >
              Actualizar
            </Button>
          </Box>

          {pendingPayments.length === 0 ? (
            <Box 
              sx={{ 
                textAlign: 'center', 
                py: 6,
                px: 3,
              }}
            >
              <Box
                sx={{
                  display: 'inline-flex',
                  p: 3,
                  borderRadius: '50%',
                  bgcolor: 'primary.light',
                  opacity: 0.1,
                  mb: 3,
                }}
              >
                <PaymentIcon sx={{ fontSize: 80, color: 'primary.main' }} />
              </Box>
              <Typography 
                variant="h6" 
                sx={{ 
                  color: 'text.primary',
                  fontWeight: 600,
                  mb: 1,
                }}
              >
                No hay pagos pendientes
              </Typography>
              <Typography 
                variant="body2" 
                sx={{ 
                  color: 'text.secondary',
                  maxWidth: 400,
                  mx: 'auto',
                }}
              >
                Todos los pagos han sido procesados correctamente
              </Typography>
            </Box>
          ) : (
            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Código</TableCell>
                    <TableCell>Usuario</TableCell>
                    <TableCell>Plan</TableCell>
                    <TableCell>Monto</TableCell>
                    <TableCell>Fecha</TableCell>
                    <TableCell>Expira</TableCell>
                    <TableCell>Estado</TableCell>
                    <TableCell>Acciones</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {pendingPayments.map((payment) => (
                    <TableRow key={payment.id}>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 'bold' }}>
                          {payment.code}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Avatar sx={{ width: 32, height: 32, mr: 1, bgcolor: 'primary.main' }}>
                            {payment.username.charAt(0).toUpperCase()}
                          </Avatar>
                          {payment.username}
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
                        <Typography variant="body2">
                          {formatDate(payment.created_at)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          {isExpired(payment.expires_at) ? (
                            <WarningIcon color="error" sx={{ mr: 1, fontSize: 16 }} />
                          ) : (
                            <ScheduleIcon color="warning" sx={{ mr: 1, fontSize: 16 }} />
                          )}
                          <Typography 
                            variant="body2" 
                            color={isExpired(payment.expires_at) ? 'error' : 'text.secondary'}
                          >
                            {getTimeRemaining(payment.expires_at)}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={isExpired(payment.expires_at) ? 'Expirado' : 'Pendiente'}
                          color={isExpired(payment.expires_at) ? 'error' : 'warning'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Tooltip title="Verificar Pago">
                          <IconButton
                            color="primary"
                            onClick={() => openVerifyDialog(payment)}
                            disabled={isExpired(payment.expires_at)}
                          >
                            <CheckIcon />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>

      {/* Dialog de Verificación */}
      <Dialog open={verifyDialogOpen} onClose={() => setVerifyDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <CheckIcon color="primary" sx={{ mr: 1 }} />
            Verificar Pago
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedPayment && (
            <Box>
              <Typography variant="body1" gutterBottom>
                <strong>Usuario:</strong> {selectedPayment.username}
              </Typography>
              <Typography variant="body1" gutterBottom>
                <strong>Plan:</strong> {selectedPayment.plan_name}
              </Typography>
              <Typography variant="body1" gutterBottom>
                <strong>Monto:</strong> {formatCurrency(selectedPayment.amount, selectedPayment.currency)}
              </Typography>
              <Typography variant="body1" gutterBottom>
                <strong>Código:</strong> {selectedPayment.code}
              </Typography>
              
              <Divider sx={{ my: 2 }} />
              
              <TextField
                fullWidth
                label="Comprobante de Pago (opcional)"
                multiline
                rows={3}
                value={paymentProof}
                onChange={(e) => setPaymentProof(e.target.value)}
                placeholder="Detalles del comprobante de pago, número de transacción, etc."
                sx={{ mt: 2 }}
              />
              
              <Alert severity="info" sx={{ mt: 2 }}>
                Al verificar este pago, se activará automáticamente la suscripción del usuario por 30 días.
              </Alert>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setVerifyDialogOpen(false)}>
            Cancelar
          </Button>
          <Button
            onClick={handleVerifyPayment}
            variant="contained"
            color="primary"
            disabled={verifying}
            startIcon={verifying ? <CircularProgress size={20} /> : <CheckIcon />}
          >
            {verifying ? 'Verificando...' : 'Verificar Pago'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default PaymentManagement;
