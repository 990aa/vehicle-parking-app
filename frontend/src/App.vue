
<template>
  <div id="app">
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
      <div class="container-fluid">
        <router-link class="navbar-brand" to="/">Parking App</router-link>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarNav">
          <ul class="navbar-nav me-auto mb-2 mb-lg-0">
            <li class="nav-item">
              <router-link class="nav-link" to="/">Home</router-link>
            </li>
            <li class="nav-item" v-if="!user">
              <router-link class="nav-link" to="/login">Login</router-link>
            </li>
            <li class="nav-item" v-if="!user">
              <router-link class="nav-link" to="/register">Register</router-link>
            </li>
            <li class="nav-item" v-if="user">
               <a class="nav-link" href="#" @click.prevent="logout">Logout</a>
            </li>
          </ul>
        </div>
      </div>
    </nav>

    <main class="container py-4">
      <router-view></router-view>
    </main>
    
    <div class="container text-center mt-5" v-if="deferredPrompt">
        <button class="btn btn-outline-primary btn-sm" @click="addToDesktop">Add App to Home Screen</button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'App',
  data() {
    return {
      deferredPrompt: null,
      user: null
    }
  },
  mounted() {
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      this.deferredPrompt = e;
    });
    this.checkUser();
  },
  methods: {
    addToDesktop() {
      if (this.deferredPrompt) {
        this.deferredPrompt.prompt();
        this.deferredPrompt.userChoice.then(() => {
          this.deferredPrompt = null;
        });
      }
    },
    async checkUser() {
      const token = localStorage.getItem('access_token');
      if (token) {
        this.user = { loggedIn: true }; 
      }
    },
    logout() {
      localStorage.removeItem('access_token');
      this.user = null;
      if (this.$route.path !== '/') {
        this.$router.push('/login');
      }
    }
  }
}
</script>

<style>
@import 'bootstrap/dist/css/bootstrap.min.css';
@import 'bootstrap-icons/font/bootstrap-icons.css';

#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  min-height: 100vh;
}
</style>
