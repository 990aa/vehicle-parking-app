<template>
  <div id="app" :class="{ 'has-navbar': showNavbar }">
    <!-- Navigation Bar -->
    <nav v-if="showNavbar" class="navbar">
      <div class="navbar-container">
        <router-link to="/" class="navbar-brand">
          <span class="brand-icon">🚗</span>
          <span class="brand-text">parkapp</span>
        </router-link>
        
        <button class="navbar-toggle" @click="mobileMenuOpen = !mobileMenuOpen" v-if="isLoggedIn">
          <span></span>
          <span></span>
          <span></span>
        </button>
        
        <div class="navbar-menu" :class="{ 'is-active': mobileMenuOpen }">
          <template v-if="!isLoggedIn">
            <router-link to="/login" class="nav-link">Sign In</router-link>
            <router-link to="/register" class="nav-link nav-link-primary">Get Started</router-link>
          </template>
          
          <template v-else>
            <router-link 
              v-if="userRole === 'admin'" 
              to="/admin/dashboard" 
              class="nav-link"
            >
              <span class="nav-icon">📊</span> Dashboard
            </router-link>
            <router-link 
              v-else 
              to="/user/dashboard" 
              class="nav-link"
            >
              <span class="nav-icon">🏠</span> Dashboard
            </router-link>
            
            <router-link to="/parking" class="nav-link" v-if="userRole !== 'admin'">
              <span class="nav-icon">🅿️</span> Find Parking
            </router-link>
            
            <div class="nav-user">
              <span class="user-greeting">{{ userName }}</span>
              <button @click="handleLogout" class="btn-logout">
                Sign Out
              </button>
            </div>
          </template>
        </div>
      </div>
    </nav>

    <!-- Main Content -->
    <main class="main-content">
      <router-view @login-success="handleLoginSuccess" />
    </main>

    <!-- Toast Notifications -->
    <div class="toast-container" v-if="toast.show">
      <div :class="['toast', `toast-${toast.type}`]">
        <span class="toast-icon">{{ toast.type === 'success' ? '✓' : toast.type === 'error' ? '✕' : 'ℹ' }}</span>
        <span class="toast-message">{{ toast.message }}</span>
        <button class="toast-close" @click="toast.show = false">×</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'App',
  data() {
    return {
      mobileMenuOpen: false,
      toast: {
        show: false,
        type: 'info',
        message: ''
      }
    };
  },
  computed: {
    isLoggedIn() {
      return !!localStorage.getItem('access_token');
    },
    userRole() {
      return localStorage.getItem('user_role') || 'user';
    },
    userName() {
      try {
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        return user.username || 'User';
      } catch {
        return 'User';
      }
    },
    showNavbar() {
      const authPages = ['/login', '/register'];
      return !authPages.includes(this.$route.path);
    }
  },
  methods: {
    handleLoginSuccess(userData) {
      this.showToast('success', `Welcome back, ${userData.username}!`);
      this.$forceUpdate();
    },
    handleLogout() {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user_role');
      localStorage.removeItem('user');
      this.showToast('info', 'You have been signed out');
      this.$router.push('/login');
    },
    showToast(type, message) {
      this.toast = { show: true, type, message };
      setTimeout(() => {
        this.toast.show = false;
      }, 4000);
    }
  },
  watch: {
    '$route'() {
      this.mobileMenuOpen = false;
    }
  }
};
</script>

<style>
/* CSS Variables for theming */
:root {
  --primary: #1a1a2e;
  --primary-light: #16213e;
  --accent: #0f3460;
  --accent-light: #e94560;
  --success: #10b981;
  --warning: #f59e0b;
  --danger: #ef4444;
  --info: #3b82f6;
  
  --text-primary: #1f2937;
  --text-secondary: #6b7280;
  --text-light: #9ca3af;
  
  --bg-primary: #ffffff;
  --bg-secondary: #f9fafb;
  --bg-tertiary: #f3f4f6;
  
  --border-color: #e5e7eb;
  --border-radius: 12px;
  --border-radius-sm: 8px;
  --border-radius-lg: 16px;
  
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  --shadow-md: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  --shadow-lg: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  
  --transition: all 0.2s ease;
  --navbar-height: 70px;
}

/* Reset & Base */
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html {
  scroll-behavior: smooth;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  font-size: 16px;
  line-height: 1.6;
  color: var(--text-primary);
  background-color: var(--bg-secondary);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

#app.has-navbar {
  padding-top: var(--navbar-height);
}

/* Navbar */
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: var(--navbar-height);
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-color);
  z-index: 1000;
  display: flex;
  align-items: center;
}

.navbar-container {
  width: 100%;
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.navbar-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  font-weight: 700;
  font-size: 1.5rem;
  color: var(--primary);
}

.brand-icon {
  font-size: 1.75rem;
}

.navbar-toggle {
  display: none;
  flex-direction: column;
  gap: 5px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 8px;
}

.navbar-toggle span {
  display: block;
  width: 24px;
  height: 2px;
  background: var(--text-primary);
  transition: var(--transition);
}

.navbar-menu {
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  text-decoration: none;
  color: var(--text-secondary);
  font-weight: 500;
  border-radius: var(--border-radius-sm);
  transition: var(--transition);
}

.nav-link:hover {
  color: var(--text-primary);
  background: var(--bg-tertiary);
}

.nav-link.router-link-active {
  color: var(--primary);
  background: var(--bg-tertiary);
}

.nav-link-primary {
  background: var(--primary);
  color: white !important;
}

.nav-link-primary:hover {
  background: var(--primary-light);
}

.nav-icon {
  font-size: 1.1rem;
}

.nav-user {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-left: 16px;
  padding-left: 16px;
  border-left: 1px solid var(--border-color);
}

.user-greeting {
  font-weight: 500;
  color: var(--text-secondary);
}

.btn-logout {
  padding: 8px 16px;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-sm);
  color: var(--text-secondary);
  font-weight: 500;
  cursor: pointer;
  transition: var(--transition);
}

.btn-logout:hover {
  background: var(--danger);
  border-color: var(--danger);
  color: white;
}

/* Main Content */
.main-content {
  flex: 1;
  width: 100%;
}

/* Toast Notifications */
.toast-container {
  position: fixed;
  top: 90px;
  right: 24px;
  z-index: 9999;
}

.toast {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: var(--bg-primary);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-lg);
  animation: slideIn 0.3s ease;
  min-width: 300px;
}

.toast-success {
  border-left: 4px solid var(--success);
}

.toast-error {
  border-left: 4px solid var(--danger);
}

.toast-info {
  border-left: 4px solid var(--info);
}

.toast-icon {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 14px;
  font-weight: bold;
}

.toast-success .toast-icon {
  background: #d1fae5;
  color: var(--success);
}

.toast-error .toast-icon {
  background: #fee2e2;
  color: var(--danger);
}

.toast-info .toast-icon {
  background: #dbeafe;
  color: var(--info);
}

.toast-message {
  flex: 1;
  font-weight: 500;
}

.toast-close {
  background: none;
  border: none;
  font-size: 20px;
  color: var(--text-light);
  cursor: pointer;
  padding: 0 4px;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* Mobile Responsive */
@media (max-width: 768px) {
  .navbar-toggle {
    display: flex;
  }
  
  .navbar-menu {
    position: fixed;
    top: var(--navbar-height);
    left: 0;
    right: 0;
    background: var(--bg-primary);
    flex-direction: column;
    padding: 16px;
    border-bottom: 1px solid var(--border-color);
    display: none;
    gap: 8px;
  }
  
  .navbar-menu.is-active {
    display: flex;
  }
  
  .nav-user {
    margin: 16px 0 0;
    padding: 16px 0 0;
    border-left: none;
    border-top: 1px solid var(--border-color);
    width: 100%;
    justify-content: space-between;
  }
  
  .toast-container {
    left: 16px;
    right: 16px;
  }
  
  .toast {
    min-width: auto;
  }
}

/* Utility Classes */
.container {
  width: 100%;
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 24px;
}

.text-center {
  text-align: center;
}

.mt-1 { margin-top: 0.25rem; }
.mt-2 { margin-top: 0.5rem; }
.mt-3 { margin-top: 1rem; }
.mt-4 { margin-top: 1.5rem; }
.mt-5 { margin-top: 2rem; }

.mb-1 { margin-bottom: 0.25rem; }
.mb-2 { margin-bottom: 0.5rem; }
.mb-3 { margin-bottom: 1rem; }
.mb-4 { margin-bottom: 1.5rem; }
.mb-5 { margin-bottom: 2rem; }
</style>
