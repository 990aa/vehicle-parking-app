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
  name: 'UserLogin',
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
        
        // Fetch user role info
        const roleResponse = await api.get('/user/role');
        const role = roleResponse.data.role;
        localStorage.setItem('user_role', role);

        if (role === 'admin') {
          this.$router.push('/admin/dashboard');
        } else {
          this.$router.push('/user/dashboard'); // Fixed route from /dashboard/user to /user/dashboard based on earlier context
        }
      } catch (err) {
        this.error = 'Invalid email or password';
        console.error(err);
      }
    }
  }
};
</script>
