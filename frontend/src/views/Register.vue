<template>
  <div class="auth-page">
    <div class="auth-container">
      <!-- Left Side - Branding -->
      <div class="auth-branding">
        <div class="branding-content">
          <div class="brand-logo">🚗</div>
          <h1 class="brand-title">parkapp</h1>
          <p class="brand-tagline">Smart Parking Solutions</p>
          
          <div class="features-list">
            <div class="feature-item">
              <span class="feature-icon">✨</span>
              <span>Create your free account</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">🎯</span>
              <span>Reserve spots in seconds</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">💰</span>
              <span>Save money with smart pricing</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Right Side - Register Form -->
      <div class="auth-form-container">
        <div class="auth-form-wrapper">
          <div class="auth-header">
            <h2>Create Account</h2>
            <p>Join thousands of users finding parking easily</p>
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
          
          <form @submit.prevent="handleRegister" class="auth-form">
            <div class="form-group">
              <label for="username" class="form-label">Username</label>
              <div class="input-wrapper" :class="{ 'has-error': errors.username }">
                <span class="input-icon">👤</span>
                <input
                  type="text"
                  id="username"
                  v-model="username"
                  placeholder="Choose a username"
                  class="form-input"
                  :class="{ 'input-error': errors.username }"
                  @focus="clearError('username')"
                  autocomplete="username"
                />
              </div>
              <span v-if="errors.username" class="error-message">{{ errors.username }}</span>
              <span v-else class="hint-text">At least 3 characters</span>
            </div>
            
            <div class="form-group">
              <label for="email" class="form-label">Email Address</label>
              <div class="input-wrapper" :class="{ 'has-error': errors.email }">
                <span class="input-icon">✉️</span>
                <input
                  type="email"
                  id="email"
                  v-model="email"
                  placeholder="you@example.com"
                  class="form-input"
                  :class="{ 'input-error': errors.email }"
                  @focus="clearError('email')"
                  autocomplete="email"
                />
              </div>
              <span v-if="errors.email" class="error-message">{{ errors.email }}</span>
            </div>
            
            <div class="form-group">
              <label for="password" class="form-label">Password</label>
              <div class="input-wrapper" :class="{ 'has-error': errors.password }">
                <span class="input-icon">🔒</span>
                <input
                  :type="showPassword ? 'text' : 'password'"
                  id="password"
                  v-model="password"
                  placeholder="Create a strong password"
                  class="form-input"
                  :class="{ 'input-error': errors.password }"
                  @focus="clearError('password')"
                  @input="checkPasswordStrength"
                  autocomplete="new-password"
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
              
              <!-- Password Strength Indicator -->
              <div v-if="password && !errors.password" class="password-strength">
                <div class="strength-bar">
                  <div 
                    class="strength-fill" 
                    :class="passwordStrength.class"
                    :style="{ width: passwordStrength.width }"
                  ></div>
                </div>
                <span class="strength-text" :class="passwordStrength.class">
                  {{ passwordStrength.text }}
                </span>
              </div>
            </div>
            
            <div class="form-group">
              <label for="confirmPassword" class="form-label">Confirm Password</label>
              <div class="input-wrapper" :class="{ 'has-error': errors.confirmPassword }">
                <span class="input-icon">🔐</span>
                <input
                  :type="showPassword ? 'text' : 'password'"
                  id="confirmPassword"
                  v-model="confirmPassword"
                  placeholder="Confirm your password"
                  class="form-input"
                  :class="{ 'input-error': errors.confirmPassword }"
                  @focus="clearError('confirmPassword')"
                  autocomplete="new-password"
                />
              </div>
              <span v-if="errors.confirmPassword" class="error-message">{{ errors.confirmPassword }}</span>
            </div>
            
            <button 
              type="submit" 
              class="btn btn-primary btn-block"
              :disabled="isLoading"
            >
              <span v-if="isLoading" class="loading-spinner"></span>
              <span v-else>Create Account</span>
            </button>
          </form>
          
          <div class="auth-footer">
            <p>Already have an account? <router-link to="/login">Sign in</router-link></p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { authAPI } from '../services/api';

export default {
  name: 'RegisterView',
  data() {
    return {
      username: '',
      email: '',
      password: '',
      confirmPassword: '',
      showPassword: false,
      isLoading: false,
      globalError: '',
      successMessage: '',
      errors: {
        username: '',
        email: '',
        password: '',
        confirmPassword: ''
      },
      passwordStrength: {
        class: '',
        width: '0%',
        text: ''
      }
    };
  },
  methods: {
    clearError(field) {
      this.errors[field] = '';
      this.globalError = '';
    },
    
    clearAllErrors() {
      this.errors = { username: '', email: '', password: '', confirmPassword: '' };
      this.globalError = '';
    },
    
    checkPasswordStrength() {
      const password = this.password;
      let strength = 0;
      
      if (password.length >= 6) strength++;
      if (password.length >= 8) strength++;
      if (/[A-Z]/.test(password)) strength++;
      if (/[0-9]/.test(password)) strength++;
      if (/[^A-Za-z0-9]/.test(password)) strength++;
      
      const levels = [
        { class: 'weak', width: '20%', text: 'Weak' },
        { class: 'weak', width: '40%', text: 'Fair' },
        { class: 'medium', width: '60%', text: 'Good' },
        { class: 'strong', width: '80%', text: 'Strong' },
        { class: 'strong', width: '100%', text: 'Excellent' }
      ];
      
      this.passwordStrength = levels[Math.min(strength, 4)];
    },
    
    validateForm() {
      let isValid = true;
      this.clearAllErrors();
      
      // Username validation
      if (!this.username.trim()) {
        this.errors.username = 'Username is required';
        isValid = false;
      } else if (this.username.length < 3) {
        this.errors.username = 'Username must be at least 3 characters';
        isValid = false;
      } else if (this.username.length > 50) {
        this.errors.username = 'Username must be less than 50 characters';
        isValid = false;
      }
      
      // Email validation
      if (!this.email.trim()) {
        this.errors.email = 'Email is required';
        isValid = false;
      } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(this.email)) {
        this.errors.email = 'Please enter a valid email address';
        isValid = false;
      }
      
      // Password validation
      if (!this.password) {
        this.errors.password = 'Password is required';
        isValid = false;
      } else if (this.password.length < 6) {
        this.errors.password = 'Password must be at least 6 characters';
        isValid = false;
      }
      
      // Confirm password validation
      if (!this.confirmPassword) {
        this.errors.confirmPassword = 'Please confirm your password';
        isValid = false;
      } else if (this.password !== this.confirmPassword) {
        this.errors.confirmPassword = 'Passwords do not match';
        isValid = false;
      }
      
      return isValid;
    },
    
    async handleRegister() {
      if (!this.validateForm()) {
        return;
      }
      
      this.isLoading = true;
      
      try {
        const response = await authAPI.register(
          this.username.trim(),
          this.email.trim().toLowerCase(),
          this.password
        );
        
        const { access_token, user, message } = response.data;
        
        // Store auth data
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('user_role', user.role);
        localStorage.setItem('user', JSON.stringify(user));
        
        this.successMessage = message || 'Account created successfully!';
        
        // Redirect to dashboard
        setTimeout(() => {
          this.$router.push('/user/dashboard');
        }, 1000);
        
      } catch (error) {
        console.error('Registration error:', error);
        
        if (error.errors) {
          if (error.errors.username) this.errors.username = error.errors.username;
          if (error.errors.email) this.errors.email = error.errors.email;
          if (error.errors.password) this.errors.password = error.errors.password;
          if (error.errors.general) this.globalError = error.errors.general;
        }
        
        if (!this.globalError && !Object.values(this.errors).some(e => e)) {
          this.globalError = error.message || 'Registration failed. Please try again.';
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
  overflow-y: auto;
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

.hint-text {
  font-size: 0.8rem;
  color: var(--text-light);
}

/* Password Strength */
.password-strength {
  margin-top: 8px;
}

.strength-bar {
  height: 4px;
  background: var(--bg-tertiary);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 4px;
}

.strength-fill {
  height: 100%;
  transition: width 0.3s ease, background 0.3s ease;
}

.strength-fill.weak {
  background: var(--danger);
}

.strength-fill.medium {
  background: var(--warning);
}

.strength-fill.strong {
  background: var(--success);
}

.strength-text {
  font-size: 0.75rem;
  font-weight: 500;
}

.strength-text.weak {
  color: var(--danger);
}

.strength-text.medium {
  color: var(--warning);
}

.strength-text.strong {
  color: var(--success);
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
</style>
