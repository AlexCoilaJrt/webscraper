import React, { useState } from 'react';
import {
  IconButton,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Tooltip,
  Box,
  Typography,
  Divider,
} from '@mui/material';
import {
  LightMode as LightModeIcon,
  DarkMode as DarkModeIcon,
  SettingsBrightness as AutoModeIcon,
  Palette as PaletteIcon,
} from '@mui/icons-material';
import { useTheme } from '../contexts/ThemeContext';

const ThemeToggle: React.FC = () => {
  const { mode, setMode, toggleTheme } = useTheme();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleModeSelect = (newMode: 'light' | 'dark' | 'auto') => {
    setMode(newMode);
    handleClose();
  };

  const getCurrentIcon = () => {
    switch (mode) {
      case 'light':
        return <LightModeIcon />;
      case 'dark':
        return <DarkModeIcon />;
      case 'auto':
        return <AutoModeIcon />;
      default:
        return <LightModeIcon />;
    }
  };

  const getCurrentLabel = () => {
    switch (mode) {
      case 'light':
        return 'Modo Claro';
      case 'dark':
        return 'Modo Oscuro';
      case 'auto':
        return 'Automático';
      default:
        return 'Modo Claro';
    }
  };

  return (
    <>
      <Tooltip title={`Tema: ${getCurrentLabel()}`}>
        <IconButton
          onClick={handleClick}
          sx={{
            color: 'inherit',
            transition: 'all 0.3s ease',
            '&:hover': {
              transform: 'scale(1.1)',
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
            },
          }}
        >
          {getCurrentIcon()}
        </IconButton>
      </Tooltip>

      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        PaperProps={{
          sx: {
            minWidth: 280,
            borderRadius: 3,
            boxShadow: '0 12px 40px rgba(0, 0, 0, 0.15)',
            border: '1px solid',
            borderColor: 'divider',
            mt: 1,
            overflow: 'hidden',
          },
        }}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <Box 
          sx={{ 
            px: 2.5, 
            py: 1.5,
            background: 'linear-gradient(135deg, #0ea5e9 0%, #38bdf8 100%)',
            color: 'white',
          }}
        >
          <Typography variant="subtitle1" sx={{ fontWeight: 700, fontSize: '0.95rem' }}>
            Seleccionar Tema
          </Typography>
        </Box>
        <Divider />
        
        <MenuItem 
          onClick={() => handleModeSelect('light')}
          selected={mode === 'light'}
          sx={{
            py: 1.5,
            px: 2,
            '&.Mui-selected': {
              backgroundColor: 'primary.main',
              color: 'white',
              '&:hover': {
                backgroundColor: 'primary.dark',
              },
              '& .MuiListItemIcon-root': {
                color: 'white',
              },
              '& .MuiListItemText-primary': {
                color: 'white',
                fontWeight: 600,
              },
              '& .MuiListItemText-secondary': {
                color: 'rgba(255, 255, 255, 0.8)',
              },
            },
            '&:hover': {
              backgroundColor: 'action.hover',
            },
          }}
        >
          <ListItemIcon>
            <LightModeIcon 
              sx={{ 
                fontSize: 24,
                color: mode === 'light' ? 'primary.main' : 'text.secondary',
              }} 
            />
          </ListItemIcon>
          <ListItemText 
            primary="Modo Claro" 
            secondary="Tema claro para uso diurno"
            primaryTypographyProps={{
              fontWeight: mode === 'light' ? 600 : 500,
              fontSize: '0.95rem',
            }}
            secondaryTypographyProps={{
              fontSize: '0.8rem',
            }}
          />
        </MenuItem>

        <MenuItem 
          onClick={() => handleModeSelect('dark')}
          selected={mode === 'dark'}
          sx={{
            py: 1.5,
            px: 2,
            '&.Mui-selected': {
              backgroundColor: 'primary.main',
              color: 'white',
              '&:hover': {
                backgroundColor: 'primary.dark',
              },
              '& .MuiListItemIcon-root': {
                color: 'white',
              },
              '& .MuiListItemText-primary': {
                color: 'white',
                fontWeight: 600,
              },
              '& .MuiListItemText-secondary': {
                color: 'rgba(255, 255, 255, 0.8)',
              },
            },
            '&:hover': {
              backgroundColor: 'action.hover',
            },
          }}
        >
          <ListItemIcon>
            <DarkModeIcon 
              sx={{ 
                fontSize: 24,
                color: mode === 'dark' ? 'primary.main' : 'text.secondary',
              }} 
            />
          </ListItemIcon>
          <ListItemText 
            primary="Modo Oscuro" 
            secondary="Tema oscuro para uso nocturno"
            primaryTypographyProps={{
              fontWeight: mode === 'dark' ? 600 : 500,
              fontSize: '0.95rem',
            }}
            secondaryTypographyProps={{
              fontSize: '0.8rem',
            }}
          />
        </MenuItem>

        <MenuItem 
          onClick={() => handleModeSelect('auto')}
          selected={mode === 'auto'}
          sx={{
            py: 1.5,
            px: 2,
            '&.Mui-selected': {
              backgroundColor: 'primary.main',
              color: 'white',
              '&:hover': {
                backgroundColor: 'primary.dark',
              },
              '& .MuiListItemIcon-root': {
                color: 'white',
              },
              '& .MuiListItemText-primary': {
                color: 'white',
                fontWeight: 600,
              },
              '& .MuiListItemText-secondary': {
                color: 'rgba(255, 255, 255, 0.8)',
              },
            },
            '&:hover': {
              backgroundColor: 'action.hover',
            },
          }}
        >
          <ListItemIcon>
            <AutoModeIcon 
              sx={{ 
                fontSize: 24,
                color: mode === 'auto' ? 'primary.main' : 'text.secondary',
              }} 
            />
          </ListItemIcon>
          <ListItemText 
            primary="Automático" 
            secondary="Sigue la configuración del sistema"
            primaryTypographyProps={{
              fontWeight: mode === 'auto' ? 600 : 500,
              fontSize: '0.95rem',
            }}
            secondaryTypographyProps={{
              fontSize: '0.8rem',
            }}
          />
        </MenuItem>

        <Divider sx={{ my: 0.5 }} />
        
        <MenuItem 
          onClick={toggleTheme}
          sx={{
            py: 1.5,
            px: 2,
            '&:hover': {
              backgroundColor: 'action.hover',
            },
          }}
        >
          <ListItemIcon>
            <PaletteIcon sx={{ fontSize: 24, color: 'text.secondary' }} />
          </ListItemIcon>
          <ListItemText 
            primary="Alternar Tema" 
            secondary="Cambiar entre claro y oscuro"
            primaryTypographyProps={{
              fontWeight: 500,
              fontSize: '0.95rem',
            }}
            secondaryTypographyProps={{
              fontSize: '0.8rem',
            }}
          />
        </MenuItem>
      </Menu>
    </>
  );
};

export default ThemeToggle;













