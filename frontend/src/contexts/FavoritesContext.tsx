import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiService } from '../services/api';

interface FavoriteArticle {
  id: number;
  title: string;
  content: string;
  url: string;
  newspaper: string;
  category: string;
  published_date: string;
  image_url?: string;
  author?: string;
  added_date: string;
}

interface FavoritesContextType {
  favorites: FavoriteArticle[];
  addToFavorites: (article: any) => Promise<boolean>;
  removeFromFavorites: (articleId: number) => Promise<boolean>;
  isFavorite: (articleId: number) => boolean;
  clearFavorites: () => Promise<boolean>;
  loading: boolean;
  error: string | null;
}

const FavoritesContext = createContext<FavoritesContextType | undefined>(undefined);

interface FavoritesProviderProps {
  children: ReactNode;
}

export const FavoritesProvider: React.FC<FavoritesProviderProps> = ({ children }) => {
  const [favorites, setFavorites] = useState<FavoriteArticle[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Cargar favoritos al inicializar
  useEffect(() => {
    loadFavorites();
  }, []);

  const loadFavorites = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Cargar desde localStorage como fallback
      const localFavorites = JSON.parse(localStorage.getItem('favorites') || '[]');
      setFavorites(localFavorites);
      
      // En el futuro, aquí se cargarían desde el backend
      // const response = await apiService.getFavorites();
      // setFavorites(response.favorites);
      
    } catch (err) {
      console.error('Error cargando favoritos:', err);
      setError('Error cargando favoritos');
    } finally {
      setLoading(false);
    }
  };

  const addToFavorites = async (article: any): Promise<boolean> => {
    try {
      setError(null);
      
      // Verificar si ya está en favoritos
      if (isFavorite(article.id)) {
        return false;
      }

      const favoriteArticle: FavoriteArticle = {
        id: article.id,
        title: article.title,
        content: article.content,
        url: article.url,
        newspaper: article.newspaper,
        category: article.category,
        published_date: article.published_date,
        image_url: article.image_url,
        author: article.author,
        added_date: new Date().toISOString(),
      };

      const newFavorites = [...favorites, favoriteArticle];
      setFavorites(newFavorites);
      
      // Guardar en localStorage
      localStorage.setItem('favorites', JSON.stringify(newFavorites));
      
      // En el futuro, aquí se guardaría en el backend
      // await apiService.addToFavorites(article.id);
      
      return true;
    } catch (err) {
      console.error('Error agregando a favoritos:', err);
      setError('Error agregando a favoritos');
      return false;
    }
  };

  const removeFromFavorites = async (articleId: number): Promise<boolean> => {
    try {
      setError(null);
      
      const newFavorites = favorites.filter(fav => fav.id !== articleId);
      setFavorites(newFavorites);
      
      // Guardar en localStorage
      localStorage.setItem('favorites', JSON.stringify(newFavorites));
      
      // En el futuro, aquí se eliminaría del backend
      // await apiService.removeFromFavorites(articleId);
      
      return true;
    } catch (err) {
      console.error('Error removiendo de favoritos:', err);
      setError('Error removiendo de favoritos');
      return false;
    }
  };

  const isFavorite = (articleId: number): boolean => {
    return favorites.some(fav => fav.id === articleId);
  };

  const clearFavorites = async (): Promise<boolean> => {
    try {
      setError(null);
      setFavorites([]);
      localStorage.removeItem('favorites');
      
      // En el futuro, aquí se limpiarían en el backend
      // await apiService.clearFavorites();
      
      return true;
    } catch (err) {
      console.error('Error limpiando favoritos:', err);
      setError('Error limpiando favoritos');
      return false;
    }
  };

  const value: FavoritesContextType = {
    favorites,
    addToFavorites,
    removeFromFavorites,
    isFavorite,
    clearFavorites,
    loading,
    error,
  };

  return (
    <FavoritesContext.Provider value={value}>
      {children}
    </FavoritesContext.Provider>
  );
};

export const useFavorites = (): FavoritesContextType => {
  const context = useContext(FavoritesContext);
  if (context === undefined) {
    throw new Error('useFavorites must be used within a FavoritesProvider');
  }
  return context;
};


















