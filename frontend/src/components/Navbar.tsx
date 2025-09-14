import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  Chip,
  Fade,
  Zoom,
  Avatar,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  PlayArrow as PlayIcon,
  Article as ArticleIcon,
  Image as ImageIcon,
  BarChart as StatsIcon,
  Settings as SettingsIcon,
  Web as WebIcon,
  AutoAwesome as AutoAwesomeIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';

const Navbar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    { label: 'PRINCIPAL', path: '/', icon: <DashboardIcon /> },
    { label: 'SCRAPING', path: '/scraping', icon: <PlayIcon /> },
    { label: 'ARTÍCULOS', path: '/articles', icon: <ArticleIcon /> },
    { label: 'IMÁGENES', path: '/images', icon: <ImageIcon /> },
    { label: 'ESTADÍSTICAS', path: '/statistics', icon: <StatsIcon /> },
    { label: 'BASE DE DATOS', path: '/database', icon: <SettingsIcon /> },
  ];

  // Configuración de colores para el diseño
  const colors = {
    primary: '#1976d2',
    secondary: '#42a5f5',
    gradient1: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    gradient2: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    gradient3: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    gradient4: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
    gradient5: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
    gradient6: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
  };

  return (
    <AppBar 
      position="static" 
      elevation={0}
      sx={{
        background: colors.gradient1,
        backdropFilter: 'blur(10px)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
        position: 'relative',
        overflow: 'hidden',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'linear-gradient(45deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)',
          zIndex: 0,
        },
      }}
    >
      <Toolbar sx={{ position: 'relative', zIndex: 2, py: 1 }}>
        {/* Logo/Brand Section */}
        <Fade in timeout={800}>
          <Box sx={{ display: 'flex', alignItems: 'center', mr: 4 }}>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                background: 'rgba(255, 255, 255, 0.15)',
                borderRadius: 3,
                px: 2,
                py: 1,
                backdropFilter: 'blur(10px)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
              }}
            >
              <Avatar
                sx={{
                  width: 40,
                  height: 40,
                  mr: 2,
                  background: 'rgba(255, 255, 255, 0.2)',
                  border: '2px solid rgba(255, 255, 255, 0.3)',
                }}
              >
                <WebIcon sx={{ fontSize: 24, color: 'white' }} />
              </Avatar>
              <Typography
                variant="h6"
                component="div"
                sx={{ 
                  fontWeight: 800,
                  color: 'white',
                  textShadow: '0 2px 4px rgba(0, 0, 0, 0.3)',
                  letterSpacing: '0.5px',
                }}
              >
                🕷️ Web Scraper
              </Typography>
            </Box>
          </Box>
        </Fade>
        
        {/* Navigation Menu */}
        <Box sx={{ display: 'flex', gap: 1, flexGrow: 1, justifyContent: 'center' }}>
          {menuItems.map((item, index) => {
            const isActive = location.pathname === item.path;
            const gradients = [colors.gradient2, colors.gradient3, colors.gradient4, colors.gradient5, colors.gradient6];
            const itemGradient = gradients[index % gradients.length];
            
            return (
              <Zoom in timeout={1000 + (index * 100)} key={item.path}>
                <Button
                  color="inherit"
                  startIcon={item.icon}
                  onClick={() => navigate(item.path)}
                  sx={{
                    position: 'relative',
                    borderRadius: 3,
                    px: 3,
                    py: 1.5,
                    minWidth: 140,
                    fontWeight: 600,
                    textTransform: 'none',
                    fontSize: '0.9rem',
                    letterSpacing: '0.5px',
                    background: isActive 
                      ? 'rgba(255, 255, 255, 0.25)' 
                      : 'rgba(255, 255, 255, 0.1)',
                    backdropFilter: 'blur(10px)',
                    border: isActive 
                      ? '2px solid rgba(255, 255, 255, 0.4)' 
                      : '2px solid rgba(255, 255, 255, 0.2)',
                    color: 'white',
                    textShadow: '0 1px 2px rgba(0, 0, 0, 0.3)',
                    boxShadow: isActive 
                      ? '0 8px 25px rgba(0, 0, 0, 0.2)' 
                      : '0 4px 15px rgba(0, 0, 0, 0.1)',
                    transform: isActive ? 'translateY(-2px)' : 'translateY(0)',
                    '&:hover': {
                      background: 'rgba(255, 255, 255, 0.2)',
                      border: '2px solid rgba(255, 255, 255, 0.4)',
                      transform: 'translateY(-3px)',
                      boxShadow: '0 12px 30px rgba(0, 0, 0, 0.25)',
                      '& .MuiButton-startIcon': {
                        transform: 'scale(1.1)',
                      },
                    },
                    '& .MuiButton-startIcon': {
                      transition: 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                      filter: 'drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3))',
                    },
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    '&::before': isActive ? {
                      content: '""',
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      right: 0,
                      bottom: 0,
                      background: itemGradient,
                      opacity: 0.1,
                      borderRadius: 3,
                      zIndex: -1,
                    } : {},
                  }}
                >
                  {item.label}
                </Button>
              </Zoom>
            );
          })}
        </Box>

        {/* Status Indicator */}
        <Fade in timeout={1500}>
          <Box sx={{ ml: 4 }}>
            <Chip
              icon={<AutoAwesomeIcon />}
              label="Sistema Activo"
              sx={{
                background: 'rgba(76, 175, 80, 0.2)',
                color: 'white',
                border: '1px solid rgba(76, 175, 80, 0.4)',
                fontWeight: 600,
                '& .MuiChip-icon': {
                  color: '#4caf50',
                },
                backdropFilter: 'blur(10px)',
                boxShadow: '0 4px 15px rgba(76, 175, 80, 0.2)',
              }}
            />
          </Box>
        </Fade>
      </Toolbar>

      {/* Decorative Elements */}
      <Box
        sx={{
          position: 'absolute',
          top: -50,
          right: -50,
          width: 150,
          height: 150,
          borderRadius: '50%',
          background: 'rgba(255, 255, 255, 0.05)',
          zIndex: 1,
        }}
      />
      <Box
        sx={{
          position: 'absolute',
          bottom: -30,
          left: -30,
          width: 100,
          height: 100,
          borderRadius: '50%',
          background: 'rgba(255, 255, 255, 0.03)',
          zIndex: 1,
        }}
      />
    </AppBar>
  );
};

export default Navbar;