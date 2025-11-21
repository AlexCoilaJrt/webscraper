import React, { useState, useEffect } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Box,
  Avatar,
  Menu,
  MenuItem,
  IconButton,
  Divider,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  PlayArrow as PlayIcon,
  Article as ArticleIcon,
  Image as ImageIcon,
  BarChart as StatsIcon,
  Settings as SettingsIcon,
  Web as WebIcon,
  Logout as LogoutIcon,
  People as PeopleIcon,
  Menu as MenuIcon,
  Payment as PaymentIcon,
  AdminPanelSettings as AdminIcon,
  Search as SearchIcon,
  Favorite as FavoriteIcon,
  TrendingUp as TrendingUpIcon,
  Twitter as TwitterIcon,
  SentimentSatisfied as SentimentIcon,
  Campaign as CampaignIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import ThemeToggle from './ThemeToggle';
import { api } from '../services/api';

const Navbar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout, isAdmin, hasPermission } = useAuth();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [userSubscription, setUserSubscription] = useState<any>(null);

  interface MenuItemType {
    label: string;
    path: string;
    icon: React.ReactElement;
    adminOnly?: boolean;
    requiresPlan?: 'premium' | 'enterprise' | 'any';
    permission?: string; // Código de permiso requerido
  }

  const mainMenuItems: MenuItemType[] = [
    { label: 'Principal', path: '/', icon: <DashboardIcon />, permission: 'view_dashboard' },
    { label: 'Artículos', path: '/articles', icon: <ArticleIcon />, permission: 'view_articles' },
    { label: 'Imágenes', path: '/images', icon: <ImageIcon />, permission: 'view_images' },
    { label: 'Análisis', path: '/analytics', icon: <StatsIcon />, permission: 'view_analytics' },
    { label: 'Sentimientos', path: '/sentiment-analysis', icon: <SentimentIcon />, permission: 'view_sentiments' },
    { label: 'Anuncios', path: '/ads-management', icon: <CampaignIcon />, adminOnly: true },
    { label: 'Suscripciones', path: '/subscriptions', icon: <PaymentIcon />, permission: 'view_subscriptions' },
    { label: 'Redes Sociales', path: '/social-media', icon: <TwitterIcon />, permission: 'view_social_media' },
  ];

  const secondaryMenuItems: MenuItemType[] = [
    { label: 'Scraping', path: '/scraping', icon: <PlayIcon />, permission: 'manage_scraping' },
    { label: 'Estadísticas', path: '/statistics', icon: <StatsIcon />, permission: 'view_analytics' },
    { label: 'Búsqueda', path: '/search', icon: <SearchIcon />, permission: 'view_articles' },
    { label: 'Favoritos', path: '/favorites', icon: <FavoriteIcon />, permission: 'view_articles' },
    { label: 'Competitive Intelligence', path: '/competitive-intelligence', icon: <SearchIcon />, requiresPlan: 'any' },
    { label: 'Trending Predictor', path: '/trending-predictor', icon: <TrendingUpIcon />, requiresPlan: 'any' },
    { label: 'Base de Datos', path: '/database', icon: <SettingsIcon />, adminOnly: true, permission: 'manage_database' },
    { label: 'Usuarios', path: '/users', icon: <PeopleIcon />, adminOnly: true, permission: 'view_users' },
    { label: 'Pagos', path: '/payments', icon: <AdminIcon />, adminOnly: true },
  ];

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    logout();
    handleMenuClose();
    navigate('/login');
  };

  useEffect(() => {
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

  const hasPlanAccess = (requiredPlan: 'premium' | 'enterprise' | 'any') => {
    // Admin siempre tiene acceso
    if (isAdmin) return true;
    // Verificar plan del usuario
    if (userSubscription) {
      const planName = userSubscription.plan_name?.toLowerCase() || '';
      if (requiredPlan === 'any') {
        return planName === 'premium' || planName === 'enterprise';
      }
      return planName === requiredPlan;
    }
    return false;
  };

  // Función para verificar si un item del menú debe mostrarse
  const shouldShowMenuItem = (item: MenuItemType): boolean => {
    // Si requiere admin y no es admin, no mostrar
    if (item.adminOnly && !isAdmin) return false;
    
    // Si requiere permiso específico, verificar
    if (item.permission && !hasPermission(item.permission)) return false;
    
    // Si requiere plan específico, verificar
    if (item.requiresPlan && !hasPlanAccess(item.requiresPlan)) return false;
    
    return true;
  };

  return (
    <AppBar 
      position="static" 
      elevation={0}
      sx={{
        background: 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)',
        borderBottom: '1px solid rgba(12, 74, 110, 0.3)',
        boxShadow: '0 2px 8px rgba(14, 165, 233, 0.15)',
        minHeight: '48px',
      }}
    >
      <Toolbar sx={{ 
        py: 0.25,
        px: { xs: 0.5, md: 1 },
        minHeight: '48px !important',
        justifyContent: 'space-between',
      }}>
        {/* Logo Section */}
        <Box 
          sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            cursor: 'pointer',
            '&:hover': { opacity: 0.8 },
            transition: 'opacity 0.2s ease-in-out',
          }}
          onClick={() => navigate('/')}
        >
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 1,
            }}
          >
            <Box
              sx={{
                width: 24,
                height: 24,
                borderRadius: 1,
                background: 'rgba(255, 255, 255, 0.2)',
                border: '1px solid rgba(255, 255, 255, 0.3)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backdropFilter: 'blur(10px)',
              }}
            >
              <WebIcon sx={{ fontSize: 14, color: 'white' }} />
            </Box>
            <Typography
              variant="h6"
              component="div"
              sx={{ 
                fontWeight: 500,
                color: 'white',
                fontSize: { xs: '0.8rem', md: '0.9rem' },
                display: { xs: 'none', sm: 'block' },
              }}
            >
              Web Scraper
            </Typography>
          </Box>
        </Box>
        
        {/* Desktop Navigation */}
        {!isMobile && (
          <Box sx={{ 
            display: 'flex', 
            gap: 0, 
            alignItems: 'center',
            flex: 1,
            justifyContent: 'center',
            maxWidth: '600px',
          }}>
            {mainMenuItems
              .filter(item => shouldShowMenuItem(item))
              .map((item) => {
              const isActive = location.pathname === item.path;
               
               return (
                 <Box
                   key={item.path}
                   onClick={() => navigate(item.path)}
                   sx={{
                     position: 'relative',
                     px: 1.5,
                     py: 0.75,
                     cursor: 'pointer',
                     color: isActive ? 'white' : 'rgba(255, 255, 255, 0.7)',
                     fontWeight: isActive ? 500 : 400,
                     fontSize: '0.75rem',
                     transition: 'all 0.2s ease-in-out',
                     borderRadius: 1,
                     '&:hover': {
                       color: 'white',
                       background: 'rgba(255, 255, 255, 0.1)',
                     },
                     '&::after': isActive ? {
                       content: '""',
                       position: 'absolute',
                       bottom: 0,
                       left: '50%',
                       transform: 'translateX(-50%)',
                       width: '60%',
                       height: 2,
                       background: 'white',
                       borderRadius: '1px 1px 0 0',
                     } : {},
                   }}
                 >
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 0.75,
                      color: 'inherit',
                      '& .MuiSvgIcon-root': {
                        fontSize: 16,
                        transition: 'color 0.2s ease-in-out',
                      },
                    }}
                  >
                    {item.icon}
                    <Typography
                      component="span"
                      sx={{
                        fontSize: '0.75rem',
                        fontWeight: isActive ? 600 : 400,
                        color: 'inherit',
                      }}
                    >
                      {item.label}
                    </Typography>
                  </Box>
                 </Box>
               );
             })}
          </Box>
        )}

        {/* Right Section */}
        <Box sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: 0.5,
        }}>
          
          {/* Theme Toggle */}
          <ThemeToggle />
          
          {/* User Avatar */}
          <IconButton
            onClick={handleMenuOpen}
            sx={{
              color: 'rgba(255, 255, 255, 0.8)',
              p: 0.25,
              '&:hover': {
                color: 'white',
                background: 'rgba(255, 255, 255, 0.1)',
              },
              transition: 'all 0.2s ease-in-out',
            }}
          >
            <Avatar
              sx={{
                width: 24,
                height: 24,
                background: 'rgba(255, 255, 255, 0.2)',
                border: '1px solid rgba(255, 255, 255, 0.3)',
                color: 'white',
                fontSize: '0.7rem',
                fontWeight: 600,
                backdropFilter: 'blur(10px)',
              }}
            >
              {user?.username?.charAt(0).toUpperCase()}
            </Avatar>
          </IconButton>

          {/* Mobile Menu Button */}
          {isMobile && (
            <IconButton
              onClick={handleMenuOpen}
              sx={{
                color: 'rgba(255, 255, 255, 0.8)',
                ml: 0.25,
                '&:hover': {
                  color: 'white',
                  background: 'rgba(255, 255, 255, 0.1)',
                },
              }}
            >
              <MenuIcon sx={{ fontSize: 18 }} />
            </IconButton>
          )}
        </Box>
      </Toolbar>
      
      {/* User Menu Dropdown */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        PaperProps={{
          sx: {
            mt: 0.5,
            minWidth: 180,
            background: 'white',
            border: '1px solid rgba(14, 165, 233, 0.2)',
            borderRadius: 2,
            boxShadow: '0 10px 25px rgba(14, 165, 233, 0.15)',
          },
        }}
      >
        {/* User Info Header */}
        <Box sx={{ p: 1, pb: 0.5 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Avatar
              sx={{
                width: 32,
                height: 32,
                background: 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)',
                color: 'white',
                fontWeight: 'bold',
                fontSize: '0.8rem',
              }}
            >
              {user?.username?.charAt(0).toUpperCase()}
            </Avatar>
            <Box>
              <Typography variant="body1" fontWeight="bold" color="#0f172a" sx={{ fontSize: '0.8rem' }}>
                {user?.username}
              </Typography>
              <Typography variant="body2" color="#64748b" sx={{ mt: 0.1, fontSize: '0.7rem' }}>
                {user?.email}
              </Typography>
              <Box sx={{ mt: 0.25 }}>
                <Box
                  sx={{ 
                    fontSize: '0.65rem',
                    height: 16,
                    px: 0.75,
                    py: 0.1,
                    background: 'rgba(14, 165, 233, 0.1)',
                    color: '#0ea5e9',
                    border: '1px solid rgba(14, 165, 233, 0.2)',
                    borderRadius: 1,
                    display: 'inline-block',
                  }}
                >
                  {user?.role === 'admin' ? 'Admin' : 'Usuario'}
                </Box>
              </Box>
            </Box>
          </Box>
        </Box>
        
        <Divider sx={{ borderColor: 'rgba(14, 165, 233, 0.2)' }} />
        
        {/* Main Menu Items */}
        {[...mainMenuItems, ...secondaryMenuItems]
          .filter(item => shouldShowMenuItem(item))
          .map((item) => {
          const isActive = location.pathname === item.path;
          
          return (
            <MenuItem
              key={item.path}
              onClick={() => {
                navigate(item.path);
                handleMenuClose();
              }}
              sx={{
                py: 0.6,
                px: 1.25,
                color: isActive ? '#0ea5e9' : '#64748b',
                '&:hover': {
                  background: 'rgba(14, 165, 233, 0.1)',
                  color: '#0ea5e9',
                },
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
                <Box
                  sx={{
                    color: isActive ? '#0ea5e9' : '#94a3b8',
                    display: 'flex',
                    alignItems: 'center',
                    fontSize: '0.8rem',
                  }}
                >
                  {item.icon}
                </Box>
                <Typography
                  variant="body2"
                  sx={{
                    fontWeight: isActive ? 600 : 400,
                    color: 'inherit',
                    fontSize: '0.75rem',
                  }}
                >
                  {item.label}
                </Typography>
              </Box>
            </MenuItem>
          );
        })}
        
        <Divider sx={{ borderColor: 'rgba(14, 165, 233, 0.2)' }} />
        
        {/* Logout */}
        <MenuItem 
          onClick={handleLogout}
          sx={{
            py: 0.75,
            px: 1.25,
            color: '#ef4444',
            '&:hover': {
              background: 'rgba(239, 68, 68, 0.1)',
            },
          }}
        >
          <LogoutIcon sx={{ mr: 1, color: '#ef4444', fontSize: '1rem' }} />
          <Typography color="#ef4444" fontWeight="medium" variant="body2" sx={{ fontSize: '0.75rem' }}>
            Cerrar Sesión
          </Typography>
        </MenuItem>
      </Menu>
    </AppBar>
  );
};

export default Navbar;