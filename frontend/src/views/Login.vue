<template>
  <div class="auth-page">
    <div class="auth-container">
      <!-- Left Side - Branding -->
      <div class="auth-branding">
        <div class="branding-content">
          <div class="brand-logo">🚗</div>
          <h1 class="brand-title">ParkEase</h1>
          <p class="brand-tagline">Smart Parking Solutions</p>
          
          <div class="features-list">
            <div class="feature-item">
              <span class="feature-icon">📍</span>
              <span>Find parking spots instantly</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">💳</span>
              <span>Easy online reservations</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">⏰</span>
              <span>Save time, every day</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Right Side - Login Form -->
      <div class="auth-form-container">
        <div class="auth-form-wrapper">
          <div class="auth-header">
            <h2>Welcome back</h2>
            <p>Sign in to your account to continue</p>
          </div>
          
          <!-- Global Error Message -->
          <div v-if="globalError" class="alert alert-error">
            <span class="alert-icon">⚠️</span>
            <span>{{ globalError }}</span>
          </div>
          
          <!-- Success Message -->
          <div v-if="successMessage" class="alert alert-success">
            <span class="alert-icon">✓</span>
            <span>{{ successMessage }}</span>
          </div>
          
          <form @submit.prevent="handleLogin" class="auth-form">
            <div class="form-group">
              <label for="email" class="form-label">Email Address</label>
              <div class="input-wrapper" :class="{ 'has-error': errors.email }">
                <span class="input-icon">✉️</span>
                <input
                  type="email"
                  id="email"
                  v-model="email"
                  placeholder="Enter your email"
                  class="form-input"
                  :class="{ 'input-error': errors.email }"
                  @focus="clearError('email')"
                  autocomplete="email"
                />
              </div>
              <span v-if="errors.email" class="error-message">{{ errors.email }}</span>
            </div>
            
            <div class="form-group">
              <div class="label-row">
                <label for="password" class="form-label">Password</label>
              </div>
              <div class="input-wrapper" :class="{ 'has-error': errors.password }">
                <span class="input-icon">🔒</span>
                <input
                  :type="showPassword ? 'text' : 'password'"
                  id="password"
                  v-model="password"
                  placeholder="Enter your password"
                  class="form-input"
                  :class="{ 'input-error': errors.password }"
                  @focus="clearError('password')"
                  autocomplete="current-password"
                />
                <button 
                  type="button" 
                  class="password-toggle"
                  @click="showPassword = !showPassword"
                >
                  {{ showPassword ? '👁️' : '👁️‍🗨️' }}
                </button>
              </div>
              <span v-if="errors.password" class="error-message">{{ errors.password }}</span>
            </div>
            
            <button 
              type="submit" 
              class="btn btn-primary btn-block"
              :disabled="isLoading"
            >
              <span v-if="isLoading" class="loading-spinner"></span>
              <span v-else>Sign In</span>
            </button>
          </form>
          
          <div class="auth-divider">
            <span>or</span>
          </div>
          
          <!-- Demo Credentials -->
          <div class="demo-credentials">
            <p class="demo-title">Demo Accounts</p>
            <div class="demo-buttons">
              <button 
                type="button" 
                class="btn btn-demo"
                @click="fillAdminCredentials"
              >
                <span>👔</span> Admin Login
              </button>
              <button 
                type="button" 
                class="btn btn-demo"
                @click="fillUserCredentials"
              >
                <span>👤</span> User Login
              </button>
            </div>
          </div>
          
          <div class="auth-footer">
            <p>Don't have an account? <router-link to="/register">Create one</router-link></p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { authAPI, userAPI } from '../services/api';

export default {
  name: 'LoginView',
  data() {
    return {
      email: '',
      password: '',
      showPassword: false,
      isLoading: false,
      globalError: '',
      successMessage: '',
      errors: {
        email: '',
        password: ''
      }
    };
  },
  methods: {
    clearError(field) {
      this.errors[field] = '';
      this.globalError = '';
    },
    
    fillAdminCredentials() {
      this.email = 'admin@parkease.com';
      this.password = 'admin123';
      this.clearAllErrors();
    },
    
    fillUserCredentials() {
      this.email = 'user@example.com';
      this.password = 'password123';
      this.clearAllErrors();
    },
    
    clearAllErrors() {
      this.errors = { email: '', password: '' };
      this.globalError = '';
    },
    
    async handleLogin() {
      this.clearAllErrors();
      
      // Client-side validation
      if (!this.email) {
        this.errors.email = 'Please enter your email address';
        return;
      }
      if (!this.password) {
        this.errors.password = 'Please enter your password';
        return;
      }
      
      this.isLoading = true;
      
      try {
        const response = await authAPI.login(this.email, this.password);
        const { access_token, user, message } = response.data;
        
        // Store auth data
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('user_role', user.role);
        localStorage.setItem('user', JSON.stringify(user));
        
        this.successMessage = message || 'Login successful!';
        
        // Emit login success event
        this.$emit('login-success', user);
        
        // Redirect based on role
        setTimeout(() => {
          if (user.role === 'admin') {
            this.$router.push('/admin/dashboard');
          } else {
            this.$router.push('/user/dashboard');
          }
        }, 500);
        
      } catch (error) {
        console.error('Login error:', error);
        
        if (error.errors) {
          if (error.errors.email) this.errors.email = error.errors.email;
          if (error.errors.password) this.errors.password = error.errors.password;
          if (error.errors.general) this.globalError = error.errors.general;
        }
        
        if (!this.errors.email && !this.errors.password && !this.globalError) {
          this.globalError = error.message || 'Login failed. Please try again.';
        }
      } finally {
        this.isLoading = false;
      }
    }
  }
};
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  background: var(--bg-secondary);
}

.auth-container {
  display: flex;
  width: 100%;
  min-height: 100vh;
}

/* Branding Side */
.auth-branding {
  flex: 1;
  background: var(--primary);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px;
  position: relative;
  overflow: hidden;
}

.auth-branding::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -50%;
  width: 100%;
  height: 100%;
  background: var(--primary-light);
  border-radius: 50%;
  opacity: 0.3;
}

.auth-branding::after {
  content: '';
  position: absolute;
  bottom: -30%;
  left: -30%;
  width: 80%;
  height: 80%;
  background: var(--accent);
  border-radius: 50%;
  opacity: 0.2;
}

.branding-content {
  position: relative;
  z-index: 1;
  color: white;
  text-align: center;
}

.brand-logo {
  font-size: 5rem;
  margin-bottom: 16px;
}

.brand-title {
  font-size: 3rem;
  font-weight: 800;
  margin-bottom: 8px;
}

.brand-tagline {
  font-size: 1.25rem;
  opacity: 0.9;
  margin-bottom: 48px;
}

.features-list {
  text-align: left;
  max-width: 280px;
  margin: 0 auto;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 0;
  border-bottom: 1px solid rgba(255,255,255,0.1);
  font-size: 1.1rem;
}

.feature-item:last-child {
  border-bottom: none;
}

.feature-icon {
  font-size: 1.5rem;
}

/* Form Side */
.auth-form-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px;
  background: var(--bg-primary);
}

.auth-form-wrapper {
  width: 100%;
  max-width: 420px;
}

.auth-header {
  margin-bottom: 32px;
}

.auth-header h2 {
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.auth-header p {
  color: var(--text-secondary);
  font-size: 1rem;
}

/* Alerts */
.alert {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-radius: var(--border-radius-sm);
  margin-bottom: 24px;
  font-size: 0.95rem;
}

.alert-error {
  background: #fef2f2;
  color: #991b1b;
  border: 1px solid #fecaca;
}

.alert-success {
  background: #f0fdf4;
  color: #166534;
  border: 1px solid #bbf7d0;
}

.alert-icon {
  font-size: 1.1rem;
}

/* Form Styles */
.auth-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-primary);
}

.label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 14px;
  font-size: 1.1rem;
  pointer-events: none;
}

.form-input {
  width: 100%;
  padding: 14px 14px 14px 48px;
  font-size: 1rem;
  border: 2px solid var(--border-color);
  border-radius: var(--border-radius-sm);
  background: var(--bg-primary);
  color: var(--text-primary);
  transition: var(--transition);
}

.form-input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 4px rgba(26, 26, 46, 0.1);
}

.form-input.input-error {
  border-color: var(--danger);
}

.input-wrapper.has-error .form-input:focus {
  box-shadow: 0 0 0 4px rgba(239, 68, 68, 0.1);
}

.password-toggle {
  position: absolute;
  right: 14px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.1rem;
  padding: 4px;
}

.error-message {
  font-size: 0.85rem;
  color: var(--danger);
  margin-top: 4px;
}

/* Buttons */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px 24px;
  font-size: 1rem;
  font-weight: 600;
  border-radius: var(--border-radius-sm);
  cursor: pointer;
  transition: var(--transition);
  border: none;
}

.btn-primary {
  background: var(--primary);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: var(--primary-light);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.btn-primary:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.btn-block {
  width: 100%;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Divider */
.auth-divider {
  display: flex;
  align-items: center;
  margin: 24px 0;
  color: var(--text-light);
}

.auth-divider::before,
.auth-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--border-color);
}

.auth-divider span {
  padding: 0 16px;
  font-size: 0.9rem;
}

/* Demo Credentials */
.demo-credentials {
  text-align: center;
}

.demo-title {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-bottom: 12px;
}

.demo-buttons {
  display: flex;
  gap: 12px;
}

.btn-demo {
  flex: 1;
  padding: 12px 16px;
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  font-size: 0.9rem;
  border: 1px solid var(--border-color);
}

.btn-demo:hover {
  background: var(--bg-secondary);
  border-color: var(--primary);
  color: var(--primary);
}

/* Footer */
.auth-footer {
  text-align: center;
  margin-top: 32px;
  color: var(--text-secondary);
}

.auth-footer a {
  color: var(--primary);
  font-weight: 600;
  text-decoration: none;
}

.auth-footer a:hover {
  text-decoration: underline;
}

/* Responsive */
@media (max-width: 968px) {
  .auth-branding {
    display: none;
  }
  
  .auth-form-container {
    padding: 24px;
  }
}

@media (max-width: 480px) {
  .demo-buttons {
    flex-direction: column;
  }
}
</style>
