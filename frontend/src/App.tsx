import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box } from '@mui/material';

// Components
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import ScrapingControl from './pages/ScrapingControl';
import ArticlesList from './pages/ArticlesList';
import ImagesGallery from './pages/ImagesGallery';
import Statistics from './pages/Statistics';
import DatabaseConfig from './pages/DatabaseConfig';

// Create theme
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
          <Navbar />
          <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/scraping" element={<ScrapingControl />} />
              <Route path="/articles" element={<ArticlesList />} />
              <Route path="/images" element={<ImagesGallery />} />
              <Route path="/statistics" element={<Statistics />} />
              <Route path="/database" element={<DatabaseConfig />} />
            </Routes>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;