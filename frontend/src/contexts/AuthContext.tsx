import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { api } from '../services/api';

interface User {
  id: number;
  username: string;
  email: string;
  role: 'admin' | 'user';
  is_active: boolean;
  subscription?: any; // Información de suscripción opcional
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  permissions: string[];
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
  isLoading: boolean;
  isAuthenticated: boolean;
  isAdmin: boolean;
  hasPermission: (permissionCode: string) => boolean;
  refreshPermissions: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [permissions, setPermissions] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = !!user && !!token;
  const isAdmin = user?.role === 'admin';

  const fetchPermissions = async () => {
    if (!token) return;
    try {
      const response = await api.get('/auth/my-permissions', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if ((response.data as any).success) {
        const perms = (response.data as any).permissions || [];
        console.log('🔐 Permisos cargados:', perms);
        setPermissions(perms);
      }
    } catch (error) {
      console.error('Error cargando permisos:', error);
      setPermissions([]);
    }
  };

  const hasPermission = (permissionCode: string): boolean => {
    // Los administradores tienen todos los permisos
    if (isAdmin) return true;
    const has = permissions.includes(permissionCode);
    console.log(`🔍 Verificando permiso "${permissionCode}": ${has} (Permisos actuales: [${permissions.join(', ')}])`);
    return has;
  };

  const refreshPermissions = async () => {
    await fetchPermissions();
  };

  // Verificar token al cargar la aplicación
  useEffect(() => {
    const verifyToken = async () => {
      const storedToken = localStorage.getItem('token');
      if (storedToken) {
        try {
          const response = await api.get('/auth/verify', {
            headers: { Authorization: `Bearer ${storedToken}` }
          });
          
          if ((response.data as any).success) {
            setUser((response.data as any).user);
            setToken(storedToken);
            await fetchPermissions();
          } else {
            localStorage.removeItem('token');
            setToken(null);
          }
        } catch (error) {
          console.error('Error verifying token:', error);
          localStorage.removeItem('token');
          setToken(null);
        }
      }
      setIsLoading(false);
    };

    verifyToken();
  }, []);

  const login = async (username: string, password: string): Promise<boolean> => {
    try {
      console.log('Attempting login for:', username);
      const response = await api.post('/auth/login', { username, password });
      console.log('Login response:', response.data);
      
      if ((response.data as any).success) {
        const { token: newToken, user: userData } = response.data as any;
        
        localStorage.setItem('token', newToken);
        setToken(newToken);
        setUser(userData);
        setIsLoading(false); // Asegurar que isLoading se establezca en false
        
        // Cargar permisos después del login
        await fetchPermissions();
        
        console.log('Login successful, user set:', userData);
        return true;
      }
      console.log('Login failed: success=false');
      return false;
    } catch (error) {
      console.error('Login error:', error);
      return false;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    setPermissions([]);
  };

  const value: AuthContextType = {
    user,
    token,
    permissions,
    login,
    logout,
    isLoading,
    isAuthenticated,
    isAdmin,
    hasPermission,
    refreshPermissions,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
