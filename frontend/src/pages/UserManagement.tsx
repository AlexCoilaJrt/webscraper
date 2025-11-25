import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Chip,
  Menu,
  ListItemIcon,
  ListItemText,
  Divider,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Tooltip,
  Stack,
  Avatar,
  Container,
  Fade,
  alpha,
  FormGroup,
  FormControlLabel,
  Checkbox,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Block as BlockIcon,
  CheckCircle as CheckCircleIcon,
  MoreVert as MoreVertIcon,
  Visibility as VisibilityIcon,
  VpnKey as VpnKeyIcon,
  CardMembership as CardMembershipIcon,
  BarChart as BarChartIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  People as PeopleIcon,
  Person as PersonIcon,
  Email as EmailIcon,
  CalendarToday as CalendarIcon,
  AccessTime as AccessTimeIcon,
  Star as StarIcon,
  TrendingUp as TrendingUpIcon,
  Image as ImageIcon,
  Article as ArticleIcon,
  Security as SecurityIcon,
  CheckBox,
  CheckBoxOutlineBlank,
} from '@mui/icons-material';
import { DataGrid, GridColDef, GridActionsCellItem } from '@mui/x-data-grid';
import { api } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

interface User {
  id: number;
  username: string;
  email: string;
  role: 'admin' | 'user';
  is_active: boolean;
  created_at: string;
  last_login: string | null;
}

interface Plan {
  id: number;
  name: string;
  display_name: string;
  price: number;
  currency: string;
}

interface UserDetails {
  user: User;
  subscription?: {
    id: number | null;
    plan_id: number | null;
    plan_name: string;
    plan_display_name: string;
    status: string;
    start_date: string;
    end_date: string | null;
    features?: string[];
  };
  statistics?: {
    total_articles: number;
    total_images: number;
    articles_today: number;
    images_today: number;
  };
}

const UserManagement: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [detailsDialogOpen, setDetailsDialogOpen] = useState(false);
  const [planDialogOpen, setPlanDialogOpen] = useState(false);
  const [passwordDialogOpen, setPasswordDialogOpen] = useState(false);
  const [permissionsDialogOpen, setPermissionsDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [userDetails, setUserDetails] = useState<UserDetails | null>(null);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [allPermissions, setAllPermissions] = useState<any[]>([]);
  const [userPermissions, setUserPermissions] = useState<string[]>([]);
  const [selectedPermissionIds, setSelectedPermissionIds] = useState<number[]>([]);
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
  const [menuUserId, setMenuUserId] = useState<number | null>(null);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    role: 'user' as 'admin' | 'user',
  });
  const [newPassword, setNewPassword] = useState('');
  const [selectedPlanId, setSelectedPlanId] = useState<number | null>(null);
  const { token } = useAuth();

  useEffect(() => {
    fetchUsers();
    fetchPlans();
  }, [token]);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const response = await api.get('/auth/users', {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if ((response.data as any).success) {
        setUsers((response.data as any).users);
      }
    } catch (error) {
      setError('Error cargando usuarios');
    } finally {
      setLoading(false);
    }
  };

  const fetchPlans = async () => {
    try {
      const response = await api.get('/subscriptions/plans', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if ((response.data as any).success) {
        setPlans((response.data as any).plans);
      }
    } catch (error) {
      console.error('Error cargando planes:', error);
    }
  };

  const fetchAllPermissions = async () => {
    try {
      const response = await api.get('/auth/permissions', {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if ((response.data as any).success) {
        setAllPermissions((response.data as any).permissions);
      }
    } catch (error) {
      console.error('Error cargando permisos:', error);
    }
  };

  const fetchUserPermissions = async (userId: number) => {
    try {
      const response = await api.get(`/auth/users/${userId}/permissions`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if ((response.data as any).success) {
        const permCodes = (response.data as any).permissions;
        setUserPermissions(permCodes);
        // Mapear códigos de permisos a IDs para el selector
        const permIds = allPermissions
          .filter(p => permCodes.includes(p.code))
          .map(p => p.id);
        setSelectedPermissionIds(permIds);
      }
    } catch (error) {
      console.error('Error cargando permisos de usuario:', error);
    }
  };

  const handleOpenPermissionsDialog = async (user: User) => {
    setSelectedUser(user);
    await fetchAllPermissions();
    // Esperar a que allPermissions se actualice antes de cargar permisos del usuario
    setTimeout(async () => {
      await fetchUserPermissions(user.id);
    }, 100);
    setPermissionsDialogOpen(true);
  };

  const handleSavePermissions = async () => {
    if (!selectedUser) return;
    
    try {
      const response = await api.put(
        `/auth/users/${selectedUser.id}/permissions`,
        { permission_ids: selectedPermissionIds },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      if ((response.data as any).success) {
        setSuccess('Permisos actualizados exitosamente');
        setPermissionsDialogOpen(false);
        fetchUsers();
        setTimeout(() => setSuccess(''), 3000);
      }
    } catch (error: any) {
      setError(error.response?.data?.error || 'Error actualizando permisos');
      setTimeout(() => setError(''), 5000);
    }
  };

  const fetchUserDetails = async (userId: number) => {
    try {
      const response = await api.get(`/auth/users/${userId}/details`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if ((response.data as any).success) {
        // El backend devuelve { success: true, user: {...} }
        const userData = (response.data as any).user;
        // Transformar a la estructura esperada por UserDetails
        setUserDetails({
          user: {
            id: userData.id,
            username: userData.username,
            email: userData.email,
            role: userData.role,
            is_active: userData.is_active,
            created_at: userData.created_at,
            last_login: userData.last_login,
          },
          subscription: userData.subscription || undefined,
          statistics: userData.statistics || undefined,
        });
      }
    } catch (error: any) {
      console.error('Error cargando detalles:', error);
      setError(error.response?.data?.error || 'Error cargando detalles del usuario');
    }
  };

  const handleCreateUser = async () => {
    try {
      const response = await api.post('/auth/users', formData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if ((response.data as any).success) {
        setSuccess('Usuario creado exitosamente');
        setCreateDialogOpen(false);
        setFormData({ username: '', email: '', password: '', role: 'user' });
        fetchUsers();
      }
    } catch (error: any) {
      setError(error.response?.data?.error || 'Error creando usuario');
    }
  };

  const handleUpdateRole = async (userId: number, newRole: 'admin' | 'user') => {
    try {
      const response = await api.put(`/auth/users/${userId}/role`, 
        { role: newRole },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      if ((response.data as any).success) {
        setSuccess('Rol actualizado exitosamente');
        fetchUsers();
      }
    } catch (error: any) {
      setError(error.response?.data?.error || 'Error actualizando rol');
    }
  };

  const handleDeactivateUser = async (userId: number) => {
    try {
      const response = await api.put(`/auth/users/${userId}/deactivate`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if ((response.data as any).success) {
        setSuccess('Usuario desactivado exitosamente');
        fetchUsers();
      }
    } catch (error: any) {
      setError(error.response?.data?.error || 'Error desactivando usuario');
    }
  };

  const handleViewDetails = async (user: User) => {
    setSelectedUser(user);
    setDetailsDialogOpen(true);
    await fetchUserDetails(user.id);
  };

  const handleChangePlan = async (userId: number) => {
    if (!selectedPlanId) {
      setError('Por favor selecciona un plan');
      return;
    }
    try {
      const response = await api.put(`/auth/users/${userId}/plan`, 
        { plan_id: selectedPlanId },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      if ((response.data as any).success) {
        setSuccess('Plan actualizado exitosamente');
        setPlanDialogOpen(false);
        setSelectedPlanId(null);
        fetchUsers();
        if (selectedUser) {
          await fetchUserDetails(selectedUser.id);
        }
      }
    } catch (error: any) {
      setError(error.response?.data?.error || 'Error actualizando plan');
    }
  };

  const handleChangePassword = async (userId: number) => {
    if (!newPassword || newPassword.length < 6) {
      setError('La contraseña debe tener al menos 6 caracteres');
      return;
    }
    try {
      const response = await api.put(`/auth/users/${userId}/password`, 
        { password: newPassword },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      if ((response.data as any).success) {
        setSuccess('Contraseña actualizada exitosamente');
        setPasswordDialogOpen(false);
        setNewPassword('');
      }
    } catch (error: any) {
      setError(error.response?.data?.error || 'Error actualizando contraseña');
    }
  };

  const handleDeleteUser = async (userId: number) => {
    if (!window.confirm('¿Estás seguro de que deseas eliminar este usuario? Esta acción no se puede deshacer.')) {
      return;
    }
    try {
      const response = await api.delete(`/auth/users/${userId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if ((response.data as any).success) {
        setSuccess('Usuario eliminado exitosamente');
        fetchUsers();
      }
    } catch (error: any) {
      setError(error.response?.data?.error || 'Error eliminando usuario');
    }
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, userId: number) => {
    setMenuAnchor(event.currentTarget);
    setMenuUserId(userId);
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
    setMenuUserId(null);
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Nunca';
    try {
      return new Date(dateString).toLocaleString('es-ES', {
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

  const columns: GridColDef[] = [
    { 
      field: 'id', 
      headerName: 'ID', 
      width: 80,
      headerAlign: 'center',
      align: 'center',
    },
    { 
      field: 'username', 
      headerName: 'Usuario', 
      width: 180,
      renderCell: (params) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Avatar 
            sx={{ 
              width: 32, 
              height: 32, 
              bgcolor: params.row.role === 'admin' 
                ? 'primary.main' 
                : 'grey.400',
              fontSize: '0.875rem'
            }}
          >
            {params.value.charAt(0).toUpperCase()}
          </Avatar>
          <Typography variant="body2" fontWeight={500}>
            {params.value}
          </Typography>
        </Box>
      ),
    },
    { 
      field: 'email', 
      headerName: 'Email', 
      width: 220,
      renderCell: (params) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <EmailIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
          <Typography variant="body2" color="text.secondary">
            {params.value}
          </Typography>
        </Box>
      ),
    },
    {
      field: 'role',
      headerName: 'Rol',
      width: 130,
      headerAlign: 'center',
      align: 'center',
      renderCell: (params) => (
        <Chip
          label={params.value === 'admin' ? 'Administrador' : 'Usuario'}
          color={params.value === 'admin' ? 'primary' : 'default'}
          size="small"
          sx={{ 
            fontWeight: 600,
            minWidth: 100
          }}
        />
      ),
    },
    {
      field: 'is_active',
      headerName: 'Estado',
      width: 130,
      headerAlign: 'center',
      align: 'center',
      renderCell: (params) => (
        <Chip
          icon={params.value ? <CheckCircleIcon /> : <BlockIcon />}
          label={params.value ? 'Activo' : 'Inactivo'}
          color={params.value ? 'success' : 'error'}
          size="small"
          sx={{ 
            fontWeight: 600,
            minWidth: 100
          }}
        />
      ),
    },
    { 
      field: 'created_at', 
      headerName: 'Creado', 
      width: 180,
      renderCell: (params) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <CalendarIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
          <Typography variant="body2" color="text.secondary">
            {formatDate(params.value)}
          </Typography>
        </Box>
      ),
    },
    { 
      field: 'last_login', 
      headerName: 'Último Login', 
      width: 180,
      renderCell: (params) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <AccessTimeIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
          <Typography variant="body2" color="text.secondary">
            {formatDate(params.value)}
          </Typography>
        </Box>
      ),
    },
    {
      field: 'actions',
      type: 'actions',
      headerName: 'Acciones',
      width: 100,
      headerAlign: 'center',
      align: 'center',
      getActions: (params) => [
        <GridActionsCellItem
          icon={
            <Tooltip title="Más opciones">
              <IconButton
                size="small"
                sx={{
                  '&:hover': {
                    bgcolor: alpha('#1976d2', 0.1),
                  }
                }}
              >
                <MoreVertIcon />
              </IconButton>
            </Tooltip>
          }
          label="Más opciones"
          onClick={(e) => {
            e.stopPropagation();
            handleMenuOpen(e as any, params.row.id);
          }}
        />,
      ],
    },
  ];

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Box display="flex" flexDirection="column" justifyContent="center" alignItems="center" minHeight="50vh">
          <CircularProgress size={60} />
          <Typography variant="h6" color="text.secondary" sx={{ mt: 2 }}>
            Cargando usuarios...
          </Typography>
      </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header Mejorado */}
      <Fade in timeout={800}>
        <Box sx={{ mb: 4 }}>
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            mb: 3
          }}>
    <Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                <Avatar
                  sx={{
                    width: 56,
                    height: 56,
                    background: 'linear-gradient(45deg, #1976d2, #42a5f5)',
                    boxShadow: '0 8px 16px rgba(25, 118, 210, 0.2)',
                  }}
                >
                  <PeopleIcon sx={{ fontSize: 32 }} />
                </Avatar>
                <Box>
                  <Typography
                    variant="h3"
                    component="h1"
                    sx={{
                      fontWeight: 700,
                      background: 'linear-gradient(45deg, #1976d2, #42a5f5)',
                      backgroundClip: 'text',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                      mb: 0.5,
                    }}
                  >
          Gestión de Usuarios
        </Typography>
                  <Typography variant="body1" color="text.secondary">
                    Administra usuarios, planes y permisos del sistema
                  </Typography>
                </Box>
              </Box>
            </Box>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={fetchUsers}
                sx={{
                  borderRadius: 2,
                  px: 3,
                  py: 1.5,
                  textTransform: 'none',
                  fontWeight: 600,
                }}
              >
                Actualizar
              </Button>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateDialogOpen(true)}
                sx={{
                  borderRadius: 2,
                  px: 3,
                  py: 1.5,
                  textTransform: 'none',
                  fontWeight: 600,
                  background: 'linear-gradient(45deg, #1976d2, #42a5f5)',
                  boxShadow: '0 4px 12px rgba(25, 118, 210, 0.3)',
                  '&:hover': {
                    background: 'linear-gradient(45deg, #1565c0, #1976d2)',
                    boxShadow: '0 6px 16px rgba(25, 118, 210, 0.4)',
                  }
                }}
        >
          Crear Usuario
        </Button>
            </Box>
      </Box>

          {/* Estadísticas rápidas */}
          <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
            <Card sx={{ flex: 1, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography variant="h4" fontWeight={700}>
                      {users.length}
                    </Typography>
                    <Typography variant="body2" sx={{ opacity: 0.9 }}>
                      Total Usuarios
                    </Typography>
                  </Box>
                  <PeopleIcon sx={{ fontSize: 48, opacity: 0.3 }} />
                </Box>
              </CardContent>
            </Card>
            <Card sx={{ flex: 1, background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', color: 'white' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography variant="h4" fontWeight={700}>
                      {users.filter(u => u.is_active).length}
                    </Typography>
                    <Typography variant="body2" sx={{ opacity: 0.9 }}>
                      Usuarios Activos
                    </Typography>
                  </Box>
                  <CheckCircleIcon sx={{ fontSize: 48, opacity: 0.3 }} />
                </Box>
              </CardContent>
            </Card>
            <Card sx={{ flex: 1, background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', color: 'white' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography variant="h4" fontWeight={700}>
                      {users.filter(u => u.role === 'admin').length}
                    </Typography>
                    <Typography variant="body2" sx={{ opacity: 0.9 }}>
                      Administradores
                    </Typography>
                  </Box>
                  <StarIcon sx={{ fontSize: 48, opacity: 0.3 }} />
                </Box>
              </CardContent>
            </Card>
          </Box>
        </Box>
      </Fade>

      {error && (
        <Alert 
          severity="error" 
          sx={{ mb: 3, borderRadius: 2 }} 
          onClose={() => setError('')}
        >
          {error}
        </Alert>
      )}

      {success && (
        <Alert 
          severity="success" 
          sx={{ mb: 3, borderRadius: 2 }} 
          onClose={() => setSuccess('')}
        >
          {success}
        </Alert>
      )}

      {/* Tabla de Usuarios Mejorada */}
      <Card
        sx={{
          borderRadius: 3,
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
          overflow: 'hidden',
        }}
      >
        <CardContent sx={{ p: 0 }}>
          <DataGrid
            rows={users}
            columns={columns}
            initialState={{
              pagination: {
                paginationModel: { page: 0, pageSize: 10 },
              },
            }}
            pageSizeOptions={[10, 25, 50]}
            disableRowSelectionOnClick
            autoHeight
            sx={{
              border: 'none',
              '& .MuiDataGrid-columnHeaders': {
                backgroundColor: alpha('#1976d2', 0.08),
                borderBottom: '2px solid',
                borderBottomColor: alpha('#1976d2', 0.2),
                fontWeight: 700,
                fontSize: '0.875rem',
              },
              '& .MuiDataGrid-cell': {
                borderBottom: `1px solid ${alpha('#000', 0.06)}`,
              },
              '& .MuiDataGrid-row:hover': {
                backgroundColor: alpha('#1976d2', 0.04),
              },
              '& .MuiDataGrid-footerContainer': {
                borderTop: `1px solid ${alpha('#000', 0.08)}`,
              },
            }}
          />
        </CardContent>
      </Card>

      {/* Menú de acciones mejorado */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={handleMenuClose}
        PaperProps={{
          sx: {
            borderRadius: 2,
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.12)',
            minWidth: 220,
            mt: 1,
          }
        }}
      >
        {menuUserId && (
          <>
            <MenuItem
              onClick={() => {
                const user = users.find(u => u.id === menuUserId);
                if (user) {
                  handleViewDetails(user);
                }
                handleMenuClose();
              }}
              sx={{
                py: 1.5,
                '&:hover': {
                  bgcolor: alpha('#1976d2', 0.08),
                }
              }}
            >
              <ListItemIcon>
                <VisibilityIcon fontSize="small" color="primary" />
              </ListItemIcon>
              <ListItemText 
                primary="Ver Detalles"
                primaryTypographyProps={{ fontWeight: 500 }}
              />
            </MenuItem>
            <MenuItem
              onClick={() => {
                const user = users.find(u => u.id === menuUserId);
                if (user) {
                  setSelectedUser(user);
                  setPlanDialogOpen(true);
                }
                handleMenuClose();
              }}
              sx={{
                py: 1.5,
                '&:hover': {
                  bgcolor: alpha('#1976d2', 0.08),
                }
              }}
            >
              <ListItemIcon>
                <CardMembershipIcon fontSize="small" color="primary" />
              </ListItemIcon>
              <ListItemText 
                primary="Cambiar Plan"
                primaryTypographyProps={{ fontWeight: 500 }}
              />
            </MenuItem>
            <MenuItem
              onClick={() => {
                const user = users.find(u => u.id === menuUserId);
                if (user) {
                  setSelectedUser(user);
                  setPasswordDialogOpen(true);
                }
                handleMenuClose();
              }}
              sx={{
                py: 1.5,
                '&:hover': {
                  bgcolor: alpha('#1976d2', 0.08),
                }
              }}
            >
              <ListItemIcon>
                <VpnKeyIcon fontSize="small" color="primary" />
              </ListItemIcon>
              <ListItemText 
                primary="Cambiar Contraseña"
                primaryTypographyProps={{ fontWeight: 500 }}
              />
            </MenuItem>
            <MenuItem
              onClick={() => {
                const user = users.find(u => u.id === menuUserId);
                if (user) {
                  handleOpenPermissionsDialog(user);
                }
                handleMenuClose();
              }}
              sx={{
                py: 1.5,
                '&:hover': {
                  bgcolor: alpha('#9c27b0', 0.08),
                }
              }}
            >
              <ListItemIcon>
                <VpnKeyIcon fontSize="small" sx={{ color: '#9c27b0' }} />
              </ListItemIcon>
              <ListItemText 
                primary="Gestionar Permisos"
                primaryTypographyProps={{ fontWeight: 500 }}
              />
            </MenuItem>
            <Divider sx={{ my: 1 }} />
            <MenuItem
              onClick={() => {
                if (menuUserId) {
                  const user = users.find(u => u.id === menuUserId);
                  if (user) {
                    handleUpdateRole(menuUserId, user.role === 'admin' ? 'user' : 'admin');
                  }
                }
                handleMenuClose();
              }}
              sx={{
                py: 1.5,
                '&:hover': {
                  bgcolor: alpha('#1976d2', 0.08),
                }
              }}
            >
              <ListItemIcon>
                <EditIcon fontSize="small" color="primary" />
              </ListItemIcon>
              <ListItemText 
                primary="Cambiar Rol"
                primaryTypographyProps={{ fontWeight: 500 }}
              />
            </MenuItem>
            <MenuItem
              onClick={() => {
                if (menuUserId) {
                  const user = users.find(u => u.id === menuUserId);
                  if (user) {
                    handleDeactivateUser(menuUserId);
                  }
                }
                handleMenuClose();
              }}
              sx={{
                py: 1.5,
                '&:hover': {
                  bgcolor: alpha('#1976d2', 0.08),
                }
              }}
            >
              <ListItemIcon>
                {users.find(u => u.id === menuUserId)?.is_active ? (
                  <BlockIcon fontSize="small" color="warning" />
                ) : (
                  <CheckCircleIcon fontSize="small" color="success" />
                )}
              </ListItemIcon>
              <ListItemText 
                primary={users.find(u => u.id === menuUserId)?.is_active ? 'Desactivar' : 'Activar'}
                primaryTypographyProps={{ fontWeight: 500 }}
              />
            </MenuItem>
            <Divider sx={{ my: 1 }} />
            <MenuItem
              onClick={() => {
                if (menuUserId) {
                  handleDeleteUser(menuUserId);
                }
                handleMenuClose();
              }}
              sx={{
                py: 1.5,
                color: 'error.main',
                '&:hover': {
                  bgcolor: alpha('#d32f2f', 0.08),
                }
              }}
            >
              <ListItemIcon>
                <DeleteIcon fontSize="small" color="error" />
              </ListItemIcon>
              <ListItemText 
                primary="Eliminar Usuario"
                primaryTypographyProps={{ fontWeight: 600 }}
              />
            </MenuItem>
          </>
        )}
      </Menu>

      {/* Dialog para crear usuario mejorado */}
      <Dialog 
        open={createDialogOpen} 
        onClose={() => setCreateDialogOpen(false)} 
        maxWidth="sm" 
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 3,
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.12)',
          }
        }}
      >
        <DialogTitle
          sx={{
            background: 'linear-gradient(45deg, #1976d2, #42a5f5)',
            color: 'white',
            py: 2.5,
            display: 'flex',
            alignItems: 'center',
            gap: 1.5,
          }}
        >
          <AddIcon />
          <Typography variant="h6" fontWeight={600}>
            Crear Nuevo Usuario
          </Typography>
        </DialogTitle>
        <DialogContent sx={{ pt: 3 }}>
          <Stack spacing={2.5}>
            <TextField
              fullWidth
              label="Usuario"
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              required
              variant="outlined"
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 2,
                }
              }}
            />
            <TextField
              fullWidth
              label="Email"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              required
              variant="outlined"
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 2,
                }
              }}
            />
            <TextField
              fullWidth
              label="Contraseña"
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              required
              variant="outlined"
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 2,
                }
              }}
            />
            <FormControl fullWidth>
              <InputLabel>Rol</InputLabel>
              <Select
                value={formData.role}
                onChange={(e) => setFormData({ ...formData, role: e.target.value as 'admin' | 'user' })}
                label="Rol"
                sx={{
                  borderRadius: 2,
                }}
              >
                <MenuItem value="user">Usuario</MenuItem>
                <MenuItem value="admin">Administrador</MenuItem>
              </Select>
            </FormControl>
          </Stack>
        </DialogContent>
        <DialogActions sx={{ p: 2.5, pt: 1 }}>
          <Button 
            onClick={() => setCreateDialogOpen(false)}
            sx={{ borderRadius: 2, px: 3, textTransform: 'none' }}
          >
            Cancelar
          </Button>
          <Button 
            onClick={handleCreateUser} 
            variant="contained"
            sx={{
              borderRadius: 2,
              px: 3,
              textTransform: 'none',
              background: 'linear-gradient(45deg, #1976d2, #42a5f5)',
              '&:hover': {
                background: 'linear-gradient(45deg, #1565c0, #1976d2)',
              }
            }}
          >
            Crear Usuario
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog para ver detalles mejorado */}
      <Dialog 
        open={detailsDialogOpen} 
        onClose={() => setDetailsDialogOpen(false)} 
        maxWidth="md" 
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 3,
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.12)',
          }
        }}
      >
        <DialogTitle
          sx={{
            background: 'linear-gradient(45deg, #1976d2, #42a5f5)',
            color: 'white',
            py: 2.5,
            display: 'flex',
            alignItems: 'center',
            gap: 1.5,
          }}
        >
          <PersonIcon />
          <Box>
            <Typography variant="h6" fontWeight={600}>
              Detalles del Usuario
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.9 }}>
              {selectedUser?.username}
            </Typography>
    </Box>
        </DialogTitle>
        <DialogContent sx={{ pt: 3 }}>
          {userDetails ? (
            <Stack spacing={3}>
              <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 2 }}>
                <Card sx={{ flex: 1, borderRadius: 2, boxShadow: 2 }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                      <PersonIcon color="primary" />
                      <Typography variant="h6" fontWeight={600}>
                        Información Básica
                      </Typography>
                    </Box>
                    <Stack spacing={1.5}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 1, borderBottom: `1px solid ${alpha('#000', 0.08)}` }}>
                        <Typography variant="body2" color="text.secondary" fontWeight={600}>
                          ID:
                        </Typography>
                        <Typography variant="body2" fontWeight={500}>
                          {userDetails.user.id}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 1, borderBottom: `1px solid ${alpha('#000', 0.08)}` }}>
                        <Typography variant="body2" color="text.secondary" fontWeight={600}>
                          Usuario:
                        </Typography>
                        <Typography variant="body2" fontWeight={500}>
                          {userDetails.user.username}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 1, borderBottom: `1px solid ${alpha('#000', 0.08)}` }}>
                        <Typography variant="body2" color="text.secondary" fontWeight={600}>
                          Email:
                        </Typography>
                        <Typography variant="body2" fontWeight={500}>
                          {userDetails.user.email}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 1, borderBottom: `1px solid ${alpha('#000', 0.08)}` }}>
                        <Typography variant="body2" color="text.secondary" fontWeight={600}>
                          Rol:
                        </Typography>
                        <Chip
                          label={userDetails.user.role === 'admin' ? 'Administrador' : 'Usuario'}
                          color={userDetails.user.role === 'admin' ? 'primary' : 'default'}
                          size="small"
                          sx={{ fontWeight: 600 }}
                        />
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 1, borderBottom: `1px solid ${alpha('#000', 0.08)}` }}>
                        <Typography variant="body2" color="text.secondary" fontWeight={600}>
                          Estado:
                        </Typography>
                        <Chip
                          icon={userDetails.user.is_active ? <CheckCircleIcon /> : <BlockIcon />}
                          label={userDetails.user.is_active ? 'Activo' : 'Inactivo'}
                          color={userDetails.user.is_active ? 'success' : 'error'}
                          size="small"
                          sx={{ fontWeight: 600 }}
                        />
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 1, borderBottom: `1px solid ${alpha('#000', 0.08)}` }}>
                        <Typography variant="body2" color="text.secondary" fontWeight={600}>
                          Creado:
                        </Typography>
                        <Typography variant="body2" fontWeight={500}>
                          {formatDate(userDetails.user.created_at)}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 1 }}>
                        <Typography variant="body2" color="text.secondary" fontWeight={600}>
                          Último Login:
                        </Typography>
                        <Typography variant="body2" fontWeight={500}>
                          {formatDate(userDetails.user.last_login)}
                        </Typography>
                      </Box>
                    </Stack>
                  </CardContent>
                </Card>
                <Card sx={{ flex: 1, borderRadius: 2, boxShadow: 2 }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                      <CardMembershipIcon color="primary" />
                      <Typography variant="h6" fontWeight={600}>
                        Suscripción
                      </Typography>
                    </Box>
                    {userDetails.subscription ? (
                      <Stack spacing={1.5}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 1, borderBottom: `1px solid ${alpha('#000', 0.08)}` }}>
                          <Typography variant="body2" color="text.secondary" fontWeight={600}>
                            Plan:
                          </Typography>
                          <Chip
                            label={userDetails.subscription.plan_display_name}
                            color={userDetails.subscription.plan_name === 'admin' ? 'error' : 'primary'}
                            size="small"
                            sx={{ fontWeight: 600 }}
                          />
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 1, borderBottom: `1px solid ${alpha('#000', 0.08)}` }}>
                          <Typography variant="body2" color="text.secondary" fontWeight={600}>
                            Estado:
                          </Typography>
                          <Chip
                            label={userDetails.subscription.status}
                            color={userDetails.subscription.status === 'active' ? 'success' : 'default'}
                            size="small"
                            sx={{ fontWeight: 600 }}
                          />
                        </Box>
                        {userDetails.subscription.plan_name !== 'admin' && (
                          <>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 1, borderBottom: `1px solid ${alpha('#000', 0.08)}` }}>
                              <Typography variant="body2" color="text.secondary" fontWeight={600}>
                                Inicio:
                              </Typography>
                              <Typography variant="body2" fontWeight={500}>
                                {formatDate(userDetails.subscription.start_date)}
                              </Typography>
                            </Box>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 1 }}>
                              <Typography variant="body2" color="text.secondary" fontWeight={600}>
                                Expira:
                              </Typography>
                              <Typography variant="body2" fontWeight={500}>
                                {userDetails.subscription.end_date
                                  ? formatDate(userDetails.subscription.end_date)
                                  : 'Ilimitado'}
                              </Typography>
                            </Box>
                          </>
                        )}
                        {userDetails.subscription.plan_name === 'admin' && userDetails.subscription.features && (
                          <Box sx={{ mt: 2, pt: 2, borderTop: `1px solid ${alpha('#000', 0.08)}` }}>
                            <Typography variant="body2" color="text.secondary" fontWeight={600} gutterBottom>
                              Características:
                            </Typography>
                            <Stack spacing={0.5}>
                              {userDetails.subscription.features.map((feature: string, index: number) => (
                                <Typography key={index} variant="body2" sx={{ fontSize: '0.75rem', color: 'text.secondary' }}>
                                  • {feature}
                                </Typography>
                              ))}
                            </Stack>
                          </Box>
                        )}
                      </Stack>
                    ) : (
                      <Box sx={{ textAlign: 'center', py: 3 }}>
                        <Chip
                          label="Plan Freemium"
                          color="default"
                          sx={{ mb: 1 }}
                        />
                        <Typography variant="body2" color="text.secondary">
                          Sin suscripción activa
                        </Typography>
                      </Box>
                    )}
                  </CardContent>
                </Card>
              </Box>
              {userDetails.statistics && (
                <Card sx={{ borderRadius: 2, boxShadow: 2 }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                      <BarChartIcon color="primary" />
                      <Typography variant="h6" fontWeight={600}>
                        Estadísticas de Uso
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, gap: 2 }}>
                      <Card sx={{ flex: 1, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
                        <CardContent>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                            <ArticleIcon />
                            <Typography variant="body2" sx={{ opacity: 0.9 }}>
                              Artículos Totales
                            </Typography>
                          </Box>
                          <Typography variant="h4" fontWeight={700}>
                            {userDetails.statistics.total_articles}
                          </Typography>
                        </CardContent>
                      </Card>
                      <Card sx={{ flex: 1, background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', color: 'white' }}>
                        <CardContent>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                            <ImageIcon />
                            <Typography variant="body2" sx={{ opacity: 0.9 }}>
                              Imágenes Totales
                            </Typography>
                          </Box>
                          <Typography variant="h4" fontWeight={700}>
                            {userDetails.statistics.total_images}
                          </Typography>
                        </CardContent>
                      </Card>
                      <Card sx={{ flex: 1, background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', color: 'white' }}>
                        <CardContent>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                            <TrendingUpIcon />
                            <Typography variant="body2" sx={{ opacity: 0.9 }}>
                              Artículos Hoy
                            </Typography>
                          </Box>
                          <Typography variant="h4" fontWeight={700}>
                            {userDetails.statistics.articles_today}
                          </Typography>
                        </CardContent>
                      </Card>
                      <Card sx={{ flex: 1, background: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)', color: 'white' }}>
                        <CardContent>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                            <TrendingUpIcon />
                            <Typography variant="body2" sx={{ opacity: 0.9 }}>
                              Imágenes Hoy
                            </Typography>
                          </Box>
                          <Typography variant="h4" fontWeight={700}>
                            {userDetails.statistics.images_today}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Box>
                  </CardContent>
                </Card>
              )}
            </Stack>
          ) : (
            <Box display="flex" justifyContent="center" p={4}>
              <CircularProgress />
            </Box>
          )}
        </DialogContent>
        <DialogActions sx={{ p: 2.5, pt: 1 }}>
          <Button 
            onClick={() => setDetailsDialogOpen(false)}
            sx={{ borderRadius: 2, px: 3, textTransform: 'none' }}
          >
            Cerrar
          </Button>
          {selectedUser && selectedUser.role !== 'admin' && (
            <Button
              onClick={() => {
                if (selectedUser) {
                  setPlanDialogOpen(true);
                  setDetailsDialogOpen(false);
                }
              }}
              variant="contained"
              sx={{
                borderRadius: 2,
                px: 3,
                textTransform: 'none',
                background: 'linear-gradient(45deg, #1976d2, #42a5f5)',
                '&:hover': {
                  background: 'linear-gradient(45deg, #1565c0, #1976d2)',
                }
              }}
            >
              Cambiar Plan
            </Button>
          )}
        </DialogActions>
      </Dialog>

      {/* Dialog para cambiar plan mejorado */}
      <Dialog 
        open={planDialogOpen} 
        onClose={() => setPlanDialogOpen(false)} 
        maxWidth="sm" 
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 3,
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.12)',
          }
        }}
      >
        <DialogTitle
          sx={{
            background: 'linear-gradient(45deg, #1976d2, #42a5f5)',
            color: 'white',
            py: 2.5,
            display: 'flex',
            alignItems: 'center',
            gap: 1.5,
          }}
        >
          <CardMembershipIcon />
          <Box>
            <Typography variant="h6" fontWeight={600}>
              Cambiar Plan
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.9 }}>
              {selectedUser?.username}
            </Typography>
          </Box>
        </DialogTitle>
        <DialogContent sx={{ pt: 3 }}>
          <FormControl fullWidth>
            <InputLabel>Seleccionar Plan</InputLabel>
            <Select
              value={selectedPlanId || ''}
              onChange={(e) => setSelectedPlanId(Number(e.target.value))}
              label="Seleccionar Plan"
              sx={{
                borderRadius: 2,
              }}
            >
              {plans.map((plan) => (
                <MenuItem key={plan.id} value={plan.id}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%', alignItems: 'center' }}>
                    <Typography>{plan.display_name}</Typography>
                    <Chip
                      label={`$${plan.price}/${plan.currency === 'USD' ? 'mes' : plan.currency}`}
                      color="primary"
                      size="small"
                      sx={{ ml: 2 }}
                    />
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions sx={{ p: 2.5, pt: 1 }}>
          <Button 
            onClick={() => setPlanDialogOpen(false)}
            sx={{ borderRadius: 2, px: 3, textTransform: 'none' }}
          >
            Cancelar
          </Button>
          <Button
            onClick={() => {
              if (selectedUser) {
                handleChangePlan(selectedUser.id);
              }
            }}
            variant="contained"
            disabled={!selectedPlanId}
            sx={{
              borderRadius: 2,
              px: 3,
              textTransform: 'none',
              background: 'linear-gradient(45deg, #1976d2, #42a5f5)',
              '&:hover': {
                background: 'linear-gradient(45deg, #1565c0, #1976d2)',
              },
              '&:disabled': {
                background: 'rgba(0, 0, 0, 0.12)',
              }
            }}
          >
            Cambiar Plan
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog para cambiar contraseña mejorado */}
      <Dialog 
        open={passwordDialogOpen} 
        onClose={() => setPasswordDialogOpen(false)} 
        maxWidth="sm" 
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 3,
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.12)',
          }
        }}
      >
        <DialogTitle
          sx={{
            background: 'linear-gradient(45deg, #1976d2, #42a5f5)',
            color: 'white',
            py: 2.5,
            display: 'flex',
            alignItems: 'center',
            gap: 1.5,
          }}
        >
          <VpnKeyIcon />
          <Box>
            <Typography variant="h6" fontWeight={600}>
              Cambiar Contraseña
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.9 }}>
              {selectedUser?.username}
            </Typography>
          </Box>
        </DialogTitle>
        <DialogContent sx={{ pt: 3 }}>
          <TextField
            fullWidth
            label="Nueva Contraseña"
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
            helperText="La contraseña debe tener al menos 6 caracteres"
            variant="outlined"
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 2,
              }
            }}
          />
        </DialogContent>
        <DialogActions sx={{ p: 2.5, pt: 1 }}>
          <Button 
            onClick={() => setPasswordDialogOpen(false)}
            sx={{ borderRadius: 2, px: 3, textTransform: 'none' }}
          >
            Cancelar
          </Button>
          <Button
            onClick={() => {
              if (selectedUser) {
                handleChangePassword(selectedUser.id);
              }
            }}
            variant="contained"
            disabled={!newPassword || newPassword.length < 6}
            sx={{
              borderRadius: 2,
              px: 3,
              textTransform: 'none',
              background: 'linear-gradient(45deg, #1976d2, #42a5f5)',
              '&:hover': {
                background: 'linear-gradient(45deg, #1565c0, #1976d2)',
              },
              '&:disabled': {
                background: 'rgba(0, 0, 0, 0.12)',
              }
            }}
          >
            Cambiar Contraseña
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog para gestionar permisos */}
      <Dialog 
        open={permissionsDialogOpen} 
        onClose={() => setPermissionsDialogOpen(false)} 
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 3,
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.12)',
          }
        }}
      >
        <DialogTitle
          sx={{
            background: 'linear-gradient(45deg, #9c27b0, #ba68c8)',
            color: 'white',
            py: 2.5,
            display: 'flex',
            alignItems: 'center',
            gap: 1.5,
          }}
        >
          <SecurityIcon />
          <Box>
            <Typography variant="h6" fontWeight={600}>
              Gestionar Permisos
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.9, mt: 0.5 }}>
              {selectedUser?.username} - {selectedUser?.email}
            </Typography>
          </Box>
        </DialogTitle>
        <DialogContent sx={{ pt: 3 }}>
          <Alert severity="info" sx={{ mb: 3 }}>
            Selecciona los permisos que deseas otorgar a este usuario. Los permisos controlan qué secciones de la aplicación puede ver y usar.
          </Alert>

          {allPermissions.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <CircularProgress />
              <Typography sx={{ mt: 2 }}>Cargando permisos...</Typography>
            </Box>
          ) : (
            <Box>
              {['Navegación', 'Contenido', 'Análisis', 'Anuncios', 'Suscripciones', 'Redes Sociales', 'Administración'].map(category => {
                const categoryPerms = allPermissions.filter(p => p.category === category);
                if (categoryPerms.length === 0) return null;
                
                return (
                  <Accordion key={category} defaultExpanded sx={{ mb: 1 }}>
                    <AccordionSummary>
                      <Typography variant="subtitle1" fontWeight={600}>
                        {category} ({categoryPerms.length})
                      </Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <FormGroup>
                        {categoryPerms.map(permission => (
                          <FormControlLabel
                            key={permission.id}
                            control={
                              <Checkbox
                                checked={selectedPermissionIds.includes(permission.id)}
                                onChange={(e) => {
                                  if (e.target.checked) {
                                    setSelectedPermissionIds([...selectedPermissionIds, permission.id]);
                                  } else {
                                    setSelectedPermissionIds(selectedPermissionIds.filter(id => id !== permission.id));
                                  }
                                }}
                              />
                            }
                            label={
                              <Box>
                                <Typography variant="body1" fontWeight={500}>
                                  {permission.name}
                                </Typography>
                                {permission.description && (
                                  <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
                                    {permission.description}
                                  </Typography>
                                )}
                              </Box>
                            }
                          />
                        ))}
                      </FormGroup>
                    </AccordionDetails>
                  </Accordion>
                );
              })}
            </Box>
          )}
        </DialogContent>
        <DialogActions sx={{ p: 2.5, pt: 1 }}>
          <Button
            onClick={() => setPermissionsDialogOpen(false)}
            variant="outlined"
            sx={{ textTransform: 'none' }}
          >
            Cancelar
          </Button>
          <Button
            onClick={handleSavePermissions}
            variant="contained"
            disabled={!selectedUser || allPermissions.length === 0}
            sx={{
              borderRadius: 2,
              px: 3,
              textTransform: 'none',
              background: 'linear-gradient(45deg, #9c27b0, #ba68c8)',
              '&:hover': {
                background: 'linear-gradient(45deg, #7b1fa2, #9c27b0)',
              },
              '&:disabled': {
                background: 'rgba(0, 0, 0, 0.12)',
              }
            }}
          >
            Guardar Permisos
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default UserManagement;
