<template>
  <div class="container d-flex justify-content-center align-items-center vh-100">
    <div class="card p-4 shadow-sm" style="max-width: 400px; width: 100%;">
      <div class="text-center mb-4">
        <i class="bi bi-car-front-fill text-primary" style="font-size: 3rem;"></i>
        <h3 class="mt-2">Parking App</h3>
      </div>
      <form @submit.prevent="handleLogin">
        <div class="mb-3">
          <label for="email" class="form-label">Email address</label>
          <input type="email" class="form-control" id="email" v-model="email" required>
        </div>
        <div class="mb-3">
          <label for="password" class="form-label">Password</label>
          <input type="password" class="form-control" id="password" v-model="password" required>
        </div>
        <div v-if="error" class="alert alert-danger" role="alert">
          {{ error }}
        </div>
        <button type="submit" class="btn btn-primary w-100">Login</button>
      </form>
      <div class="mt-3 text-center">
        <p>Don't have an account? <router-link to="/register">Register</router-link></p>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../services/api';

export default {
  data() {
    return {
      email: '',
      password: '',
      error: ''
    };
  },
  methods: {
    async handleLogin() {
      try {
        const response = await api.post('/auth/token', {
          email: this.email,
          password: this.password
        });
        
        localStorage.setItem('access_token', response.data.access_token);
        
        // Fetch user role info (need an endpoint for this or decode token if included)
        // For now, let's assume we fetch profile to get role
        const profile = await api.get('/user/');
        
        // This is a simplification. Ideally, role is returned in login or explicit /me endpoint
        // profile.data.logged_in_as gives email. 
        // We might need to ask Backend for role.
        
        // Workaround: We'll add a helper endpoint in Backend or deduce
        // For now, let's just push to user and handle 403 there, or redirect based on email (bad practice)
        
        // Let's UPDATE BACKEND to return role in /user/
        const roleResponse = await api.get('/user/role');
        const role = roleResponse.data.role;
        localStorage.setItem('user_role', role);

        if (role === 'admin') {
          this.$router.push('/admin/dashboard');
        } else {
          this.$router.push('/user/dashboard');
        }

      } catch (err) {
        this.error = 'Invalid email or password';
        console.error(err);
      }
    }
  }
};
</script>
