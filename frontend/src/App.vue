
<template>
  <div id="app">
    <router-view></router-view>
  </div>
</template>

<script>
export default {
  name: 'App',
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  color: #2c3e50;
  min-height: 100vh;
}
</style>
            <li class="nav-item">
              <a class="nav-link" href="#">Profile</a>
            </li>
          </ul>
        </div>
      </div>
    </nav>
    <main class="container py-4">
      <div class="row justify-content-center">
        <div class="col-12 col-md-8 col-lg-6 text-center">
          <img alt="Parking App Logo" src="./assets/logo.png" class="img-fluid mb-3" style="max-width:120px;">
          <h1 class="mb-3">Welcome to Vehicle Parking App</h1>
          <p class="lead">Unified, responsive parking management for all your needs. Works seamlessly on mobile and desktop.</p>
          <button class="btn btn-success mt-3" @click="addToDesktop" v-if="deferredPrompt">Add to Desktop</button>
          <div class="mt-4">
            <button class="btn btn-primary" @click="fetchUser">Test API: Get User Info</button>
            <div v-if="user" class="alert alert-info mt-3">
              <strong>User API Response:</strong>
              <pre class="text-start">{{ user }}</pre>
            </div>
            <div v-if="apiError" class="alert alert-danger mt-3">
              <strong>API Error:</strong> {{ apiError }}
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import api from './api';

export default {
  name: 'App',
  data() {
    return {
      deferredPrompt: null,
      user: null,
      apiError: null
    }
  },
  mounted() {
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      this.deferredPrompt = e;
    });
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
    async fetchUser() {
      this.apiError = null;
      this.user = null;
      try {
        const res = await api.get('/user/');
        this.user = JSON.stringify(res.data, null, 2);
      } catch (err) {
        this.apiError = err.response?.data?.message || err.message;
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
}

@media (max-width: 767px) {
  h1 {
    font-size: 2rem;
  }
  .container {
    padding: 1rem !important;
  }
}
</style>
