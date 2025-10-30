# 🔄 Token Refresh System - Hybrid Approach

## Overview

Your authentication now uses a **Hybrid Token Refresh System** combining:
1. **Automatic Backend Refresh** - Seamless UX
2. **Manual Frontend Refresh** - Full control

---

## 🎯 How It Works

### Two Types of Tokens

| Token Type | Lifetime | Purpose | Storage |
|------------|----------|---------|---------|
| **Access Token** | 1 day | API requests | Memory/localStorage |
| **Refresh Token** | 30 days | Get new access tokens | Secure storage only |

---

## 🔐 Token Response Format

### Login Response
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "email_verified": true
  }
}
```

---

## 🌟 Method 1: Automatic Backend Refresh (Recommended for Web)

### How It Works
- Backend automatically issues new tokens when current token expires soon (< 2 hours)
- New token sent in response header: `X-New-Token`
- Frontend intercepts and updates token silently
- User never experiences interruption

### Frontend Implementation (JavaScript/React)

```javascript
// axios-config.js
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
});

// Request interceptor - Add token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - Check for auto-refreshed token
api.interceptors.response.use(
  (response) => {
    // Check if backend sent a new token
    const newToken = response.headers['x-new-token'];
    if (newToken) {
      console.log('🔄 Token auto-refreshed by backend');
      localStorage.setItem('access_token', newToken);
      // Update axios default header
      api.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
    }
    return response;
  },
  (error) => {
    // Handle 401 errors
    if (error.response?.status === 401) {
      // Token expired or invalid - redirect to login
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
```

### Usage
```javascript
// auth.js
export const login = async (email, password) => {
  const { data } = await api.post('/login', { email, password });
  
  // Store both tokens
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
  
  return data;
};

// Any API call
const getProducts = async () => {
  const { data } = await api.get('/products');
  // Token auto-refreshed if needed!
  return data;
};
```

---

## 🎮 Method 2: Manual Refresh (Full Control)

### How It Works
- Frontend tracks token expiration
- Calls `/api/refresh` before token expires
- Gets new access token
- Refresh token stays the same

### Frontend Implementation (JavaScript/React)

```javascript
// token-manager.js
import axios from 'axios';
import jwtDecode from 'jwt-decode';

class TokenManager {
  constructor() {
    this.refreshTimer = null;
    this.startAutoRefresh();
  }

  startAutoRefresh() {
    // Check every minute
    this.refreshTimer = setInterval(() => {
      this.checkAndRefresh();
    }, 60000); // 60 seconds
  }

  async checkAndRefresh() {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    try {
      const decoded = jwtDecode(token);
      const expiresIn = decoded.exp * 1000 - Date.now();
      
      // Refresh if expires in less than 2 hours
      if (expiresIn < 7200000) {
        console.log('🔄 Token expiring soon, refreshing...');
        await this.refresh();
      }
    } catch (error) {
      console.error('Token decode error:', error);
    }
  }

  async refresh() {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        throw new Error('No refresh token');
      }

      const response = await axios.post(
        'http://localhost:8000/api/refresh',
        {},
        {
          headers: {
            Authorization: `Bearer ${refreshToken}`
          }
        }
      );

      const { access_token } = response.data;
      localStorage.setItem('access_token', access_token);
      console.log('✅ Token refreshed successfully');
      
      return access_token;
    } catch (error) {
      console.error('Token refresh failed:', error);
      this.logout();
      throw error;
    }
  }

  logout() {
    clearInterval(this.refreshTimer);
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/login';
  }
}

// Initialize
export const tokenManager = new TokenManager();
```

### Usage with Axios Interceptor
```javascript
import axios from 'axios';
import { tokenManager } from './token-manager';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If 401 and not already retried
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        // Try to refresh token
        const newToken = await tokenManager.refresh();
        
        // Retry original request with new token
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;
```

---

## 🎨 React Context Example (Complete Solution)

```javascript
// AuthContext.jsx
import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';
import jwtDecode from 'jwt-decode';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for existing token on mount
    const token = localStorage.getItem('access_token');
    if (token) {
      try {
        const decoded = jwtDecode(token);
        if (decoded.exp * 1000 > Date.now()) {
          fetchCurrentUser();
        } else {
          attemptRefresh();
        }
      } catch {
        setLoading(false);
      }
    } else {
      setLoading(false);
    }

    // Set up auto-refresh
    const interval = setInterval(checkAndRefresh, 60000);
    return () => clearInterval(interval);
  }, []);

  const checkAndRefresh = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    const decoded = jwtDecode(token);
    const expiresIn = decoded.exp * 1000 - Date.now();
    
    if (expiresIn < 7200000) { // < 2 hours
      await attemptRefresh();
    }
  };

  const attemptRefresh = async () => {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      setLoading(false);
      return;
    }

    try {
      const { data } = await axios.post(
        'http://localhost:8000/api/refresh',
        {},
        { headers: { Authorization: `Bearer ${refreshToken}` } }
      );
      
      localStorage.setItem('access_token', data.access_token);
      setUser(data.user);
    } catch (error) {
      logout();
    } finally {
      setLoading(false);
    }
  };

  const fetchCurrentUser = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const { data } = await axios.get('http://localhost:8000/api/me', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUser(data);
    } catch (error) {
      console.error('Fetch user failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    const { data } = await axios.post('http://localhost:8000/api/login', {
      email,
      password
    });
    
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    setUser(data.user);
    
    return data;
  };

  const logout = async () => {
    try {
      const token = localStorage.getItem('access_token');
      await axios.post(
        'http://localhost:8000/api/logout',
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
    } catch (error) {
      console.error('Logout failed:', error);
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
```

---

## 📱 Mobile App (React Native Example)

```javascript
// tokenService.js
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';

class TokenService {
  async saveTokens(accessToken, refreshToken) {
    await AsyncStorage.setItem('access_token', accessToken);
    await AsyncStorage.setItem('refresh_token', refreshToken);
  }

  async getAccessToken() {
    return await AsyncStorage.getItem('access_token');
  }

  async getRefreshToken() {
    return await AsyncStorage.getItem('refresh_token');
  }

  async refreshAccessToken() {
    const refreshToken = await this.getRefreshToken();
    if (!refreshToken) throw new Error('No refresh token');

    const { data } = await axios.post(
      'http://your-api.com/api/refresh',
      {},
      { headers: { Authorization: `Bearer ${refreshToken}` } }
    );

    await AsyncStorage.setItem('access_token', data.access_token);
    return data.access_token;
  }

  async clearTokens() {
    await AsyncStorage.removeItem('access_token');
    await AsyncStorage.removeItem('refresh_token');
  }
}

export default new TokenService();
```

---

## 🧪 Testing

### Test Auto-Refresh
```bash
# 1. Login
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Test123!"}'

# Response includes both tokens

# 2. Make API calls with access token
curl http://localhost:8000/api/me \
  -H "Authorization: Bearer {access_token}"

# 3. Check response headers for X-New-Token
# (Will appear when token expires in < 2 hours)
```

### Test Manual Refresh
```bash
# Use refresh token to get new access token
curl -X POST http://localhost:8000/api/refresh \
  -H "Authorization: Bearer {refresh_token}"

# Response:
{
  "access_token": "new_access_token...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {...}
}
```

---

## 🔒 Security Best Practices

### DO ✅
- Store refresh token in httpOnly cookie (web) or secure storage (mobile)
- Always use HTTPS in production
- Set short lifetime for access tokens (1 day)
- Set longer lifetime for refresh tokens (30 days)
- Blacklist refresh tokens on logout
- Rotate refresh tokens periodically

### DON'T ❌
- Don't store refresh tokens in localStorage (XSS risk)
- Don't send refresh tokens in URL parameters
- Don't use refresh tokens for API requests (use access tokens)
- Don't share tokens between devices
- Don't expose tokens in console logs in production

---

## 📊 Token Lifecycle Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    USER LOGIN                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │ Backend Issues:            │
        │ - Access Token (1 day)     │
        │ - Refresh Token (30 days)  │
        └────────────┬───────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │ Frontend Stores Both       │
        └────────────┬───────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │ Use Access Token for APIs  │
        └────────────┬───────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
  Token Valid              Token Expires Soon
  (Keep using)             (< 2 hours)
                                 │
                    ┌────────────┴──────────┐
                    │                       │
                    ▼                       ▼
          AUTO-REFRESH              MANUAL REFRESH
          (Backend sends            (Frontend calls
           X-New-Token)             /api/refresh)
                    │                       │
                    └───────────┬───────────┘
                                ▼
                   ┌────────────────────────┐
                   │ New Access Token       │
                   │ (Valid for 1 more day) │
                   └────────────────────────┘
```

---

## 🎯 Recommendation

**For Web Apps:** Use **both methods**
- Auto-refresh as primary (seamless UX)
- Manual refresh as fallback (when auto fails)

**For Mobile Apps:** Use **manual refresh only**
- Better battery life
- More control over network requests
- Background refresh with app lifecycle

---

## 🚀 Quick Start

1. **Update your `.env` file:**
   ```env
   REFRESH_TOKEN_ENABLED=true
   REFRESH_TOKEN_EXPIRE_DAYS=30
   ```

2. **Restart your backend:**
   ```bash
   uv run uvicorn app.main:app --reload
   ```

3. **Test login - you'll get both tokens:**
   ```bash
   curl -X POST http://localhost:8000/api/login \
     -H "Content-Type: application/json" \
     -d '{"email":"your@email.com","password":"yourpass"}'
   ```

4. **Implement frontend using examples above**

---

## 📞 Support

Your hybrid token refresh system is now fully configured and ready to use! 🎉

**Need help?** Check the examples above or refer to the authentication documentation.
