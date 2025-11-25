import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Chip,
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Avatar,
  Button,
} from '@mui/material';
import {
  Payment as PaymentIcon,
  CheckCircle as CheckIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Close as CloseIcon,
  Notifications as NotificationsIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';
// import { api } from '../services/api'; // Comentado temporalmente
import { useAuth } from '../contexts/AuthContext';

interface PaymentNotification {
  id: number;
  type: 'payment_created' | 'payment_verified' | 'payment_expired' | 'subscription_activated';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  data?: any;
}

interface PaymentNotificationsProps {
  onPaymentVerified?: () => void;
}

export const PaymentNotifications: React.FC<PaymentNotificationsProps> = ({ onPaymentVerified }) => {
  const { user, isAdmin } = useAuth();
  const [notifications, setNotifications] = useState<PaymentNotification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showNotifications, setShowNotifications] = useState(false);
  // const [snackbarOpen, setSnackbarOpen] = useState(false);
  // const [snackbarMessage, setSnackbarMessage] = useState('');
  // const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'error' | 'warning' | 'info'>('info');

  // Simular notificaciones (en producción vendrían del backend)
  useEffect(() => {
    const mockNotifications: PaymentNotification[] = [
      {
        id: 1,
        type: 'payment_created',
        title: 'Código de Pago Creado',
        message: 'Se ha creado un nuevo código de pago para el Plan Premium',
        timestamp: new Date().toISOString(),
        read: false,
        data: { plan: 'Premium', amount: 29 }
      },
      {
        id: 2,
        type: 'payment_verified',
        title: 'Pago Verificado',
        message: 'Tu pago ha sido verificado y tu suscripción está activa',
        timestamp: new Date(Date.now() - 3600000).toISOString(),
        read: false,
        data: { plan: 'Premium', duration: '30 días' }
      }
    ];

    setNotifications(mockNotifications);
    setUnreadCount(mockNotifications.filter(n => !n.read).length);
  }, []);

  // Polling para notificaciones en tiempo real (cada 30 segundos)
  useEffect(() => {
    const interval = setInterval(() => {
      fetchNotifications();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const fetchNotifications = async () => {
    try {
      // En producción, esto sería una llamada real al backend
      // const response = await api.get('/notifications/payments');
      // setNotifications(response.data.notifications);
    } catch (error) {
      console.error('Error fetching notifications:', error);
    }
  };

  const markAsRead = async (notificationId: number) => {
    try {
      // En producción: await api.put(`/notifications/${notificationId}/read`);
      setNotifications(prev => 
        prev.map(n => n.id === notificationId ? { ...n, read: true } : n)
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  const markAllAsRead = async () => {
    try {
      // En producción: await api.put('/notifications/mark-all-read');
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
      setUnreadCount(0);
    } catch (error) {
      console.error('Error marking all notifications as read:', error);
    }
  };

  // const showSnackbar = (message: string, severity: 'success' | 'error' | 'warning' | 'info') => {
  //   setSnackbarMessage(message);
  //   setSnackbarSeverity(severity);
  //   setSnackbarOpen(true);
  // };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'payment_created':
        return <PaymentIcon color="primary" />;
      case 'payment_verified':
        return <CheckIcon color="success" />;
      case 'payment_expired':
        return <WarningIcon color="warning" />;
      case 'subscription_activated':
        return <TrendingUpIcon color="success" />;
      default:
        return <InfoIcon color="info" />;
    }
  };

  const getNotificationColor = (type: string) => {
    switch (type) {
      case 'payment_created':
        return 'primary';
      case 'payment_verified':
        return 'success';
      case 'payment_expired':
        return 'warning';
      case 'subscription_activated':
        return 'success';
      default:
        return 'info';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    if (diff < 60000) return 'Hace un momento';
    if (diff < 3600000) return `Hace ${Math.floor(diff / 60000)} min`;
    if (diff < 86400000) return `Hace ${Math.floor(diff / 3600000)} h`;
    return date.toLocaleDateString('es-PE');
  };

  // Solo mostrar notificaciones de pagos para usuarios con suscripciones o admins
  if (!user || (!isAdmin && !user.subscription)) {
    return null;
  }

  return (
    <>
      {/* Botón de notificaciones */}
      <Box sx={{ position: 'fixed', bottom: 20, right: 20, zIndex: 1000 }}>
        <IconButton
          onClick={() => setShowNotifications(!showNotifications)}
          sx={{
            background: 'rgba(255, 255, 255, 0.9)',
            border: '1px solid rgba(0, 0, 0, 0.1)',
            boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
            '&:hover': {
              background: 'rgba(255, 255, 255, 1)',
              transform: 'scale(1.05)',
            },
            transition: 'all 0.2s ease-in-out',
          }}
        >
          <NotificationsIcon sx={{ color: '#1976d2' }} />
          {unreadCount > 0 && (
            <Chip
              label={unreadCount}
              size="small"
              color="error"
              sx={{
                position: 'absolute',
                top: -8,
                right: -8,
                minWidth: 20,
                height: 20,
                fontSize: '0.75rem',
              }}
            />
          )}
        </IconButton>
      </Box>

      {/* Panel de notificaciones */}
      {showNotifications && (
        <Box
          sx={{
            position: 'fixed',
            bottom: 80,
            right: 20,
            width: 400,
            maxHeight: 500,
            zIndex: 999,
            background: 'white',
            borderRadius: 2,
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
            border: '1px solid rgba(0, 0, 0, 0.1)',
            overflow: 'hidden',
          }}
        >
          <Box sx={{ p: 2, borderBottom: '1px solid rgba(0, 0, 0, 0.1)' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                Notificaciones de Pagos
              </Typography>
              <Box>
                {unreadCount > 0 && (
                  <Button size="small" onClick={markAllAsRead}>
                    Marcar todo como leído
                  </Button>
                )}
                <IconButton size="small" onClick={() => setShowNotifications(false)}>
                  <CloseIcon />
                </IconButton>
              </Box>
            </Box>
          </Box>

          <Box sx={{ maxHeight: 400, overflowY: 'auto' }}>
            {notifications.length === 0 ? (
              <Box sx={{ p: 3, textAlign: 'center' }}>
                <NotificationsIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  No hay notificaciones
                </Typography>
              </Box>
            ) : (
              <List dense>
                {notifications.map((notification) => (
                  <ListItem
                    key={notification.id}
                    sx={{
                      bgcolor: notification.read ? 'transparent' : 'rgba(25, 118, 210, 0.04)',
                      borderLeft: notification.read ? 'none' : '3px solid #1976d2',
                      cursor: 'pointer',
                      '&:hover': {
                        bgcolor: 'rgba(0, 0, 0, 0.04)',
                      },
                    }}
                    onClick={() => markAsRead(notification.id)}
                  >
                    <ListItemIcon>
                      <Avatar
                        sx={{
                          bgcolor: `${getNotificationColor(notification.type)}.light`,
                          width: 32,
                          height: 32,
                        }}
                      >
                        {getNotificationIcon(notification.type)}
                      </Avatar>
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Typography variant="body2" sx={{ fontWeight: notification.read ? 'normal' : 'bold' }}>
                          {notification.title}
                        </Typography>
                      }
                      secondary={
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            {notification.message}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {formatTimestamp(notification.timestamp)}
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            )}
          </Box>
        </Box>
      )}

      {/* Snackbar para mensajes temporales - Comentado temporalmente */}
      {/* <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
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
      </Snackbar> */}
    </>
  );
};

export default PaymentNotifications;
