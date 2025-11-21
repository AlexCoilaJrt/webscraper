import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import CssBaseline from '@mui/material/CssBaseline';
import { Box } from '@mui/material';

// Components
import Navbar from './components/Navbar';
// import NotificationSystem from './components/NotificationSystem'; // Eliminado
// import PaymentNotifications from './components/PaymentNotifications'; // Deshabilitado temporalmente
import Login from './components/Login';
import ProtectedRoute from './components/ProtectedRoute';
import Dashboard from './pages/Dashboard';
import ScrapingControl from './pages/ScrapingControl';
import ArticlesList from './pages/ArticlesList';
import ImagesGallery from './pages/ImagesGallery';
import Analytics from './pages/Analytics';
import Statistics from './pages/Statistics';
import DatabaseConfig from './pages/DatabaseConfig';
import UserManagement from './pages/UserManagement';
import Subscriptions from './pages/Subscriptions';
import PaymentManagement from './pages/PaymentManagement';
import AdvancedSearch from './components/AdvancedSearch';
import Favorites from './pages/Favorites';
import CompetitiveIntelligence from './pages/CompetitiveIntelligence';
import TrendingPredictor from './pages/TrendingPredictor';
import SocialMedia from './pages/SocialMedia';
import SentimentAnalysis from './pages/SentimentAnalysis';
import AdsManagement from './pages/AdsManagement';

// Contexts
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { FavoritesProvider } from './contexts/FavoritesContext';

// Utils
// import { initializePWA } from './utils/registerSW'; // Deshabilitado temporalmente

function App() {
  // Inicializar PWA (deshabilitado temporalmente)
  // React.useEffect(() => {
  //   initializePWA();
  // }, []);

  return (
    <ThemeProvider>
      <CssBaseline />
      <AuthProvider>
        <FavoritesProvider>
        <Router>
          <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/*" element={
                <ProtectedRoute>
                  <Navbar />
                  <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
                    <Routes>
                      <Route path="/" element={<Dashboard />} />
                      <Route path="/scraping" element={<ScrapingControl />} />
                      <Route path="/articles" element={<ArticlesList />} />
                      <Route path="/images" element={<ImagesGallery />} />
                      <Route path="/analytics" element={<Analytics />} />
                      <Route path="/statistics" element={<Statistics />} />
                      <Route path="/database" element={
                        <ProtectedRoute requireAdmin>
                          <DatabaseConfig />
                        </ProtectedRoute>
                      } />
                      <Route path="/users" element={
                        <ProtectedRoute requireAdmin>
                          <UserManagement />
                        </ProtectedRoute>
                      } />
                      <Route path="/subscriptions" element={<Subscriptions />} />
                      <Route path="/payments" element={
                        <ProtectedRoute requireAdmin>
                          <PaymentManagement />
                        </ProtectedRoute>
                      } />
                      <Route path="/search" element={<AdvancedSearch />} />
                      <Route path="/favorites" element={<Favorites />} />
                      <Route path="/competitive-intelligence" element={<CompetitiveIntelligence />} />
                      <Route path="/trending-predictor" element={<TrendingPredictor />} />
                      <Route path="/social-media" element={<SocialMedia />} />
                      <Route path="/sentiment-analysis" element={<SentimentAnalysis />} />
                      <Route path="/ads-management" element={
                        <ProtectedRoute requireAdmin>
                          <AdsManagement />
                        </ProtectedRoute>
                      } />
                    </Routes>
                  </Box>
                </ProtectedRoute>
              } />
            </Routes>
          </Box>
        </Router>
        </FavoritesProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;