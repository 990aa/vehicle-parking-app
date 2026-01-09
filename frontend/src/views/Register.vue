<template>
  <div class="container d-flex justify-content-center align-items-center vh-100">
    <div class="card p-4 shadow-sm" style="max-width: 400px; width: 100%;">
      <div class="text-center mb-4">
        <h3 class="mt-2">Register</h3>
      </div>
      <form @submit.prevent="handleRegister">
        <div class="mb-3">
          <label for="username" class="form-label">Username</label>
          <input type="text" class="form-control" id="username" v-model="username" required>
        </div>
        <div class="mb-3">
          <label for="email" class="form-label">Email address</label>
          <input type="email" class="form-control" id="email" v-model="email" required>
        </div>
        <div class="mb-3">
          <label for="password" class="form-label">Password</label>
          <input type="password" class="form-control" id="password" v-model="password" required>
        </div>
        <div v-if="error" class="alert alert-danger">{{ error }}</div>
        <button type="submit" class="btn btn-success w-100">Sign Up</button>
      </form>
      <div class="mt-3 text-center">
        <p>Allowed? <router-link to="/login">Login</router-link></p>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../services/api';

export default {
  data() {
    return {
      username: '',
      email: '',
      password: '',
      error: ''
    };
  },
  methods: {
    async handleRegister() {
        // We need a register endpoint in the backend. 
        // Existing app likely handles it in authorisation.py
        try {
            await api.post('/auth/register', {
                username: this.username,
                email: this.email,
                password: this.password
            });
            this.$router.push('/login');
        } catch (err) {
            this.error = err.response?.data?.message || 'Registration failed';
        }
    }
  }
};
</script>
