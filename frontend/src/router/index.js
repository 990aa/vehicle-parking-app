import { createRouter, createWebHistory } from 'vue-router';

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { guest: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
    meta: { guest: true }
  },
  {
    path: '/user/dashboard',
    name: 'UserDashboard',
    component: () => import('../views/UserDashboard.vue'),
    meta: { requiresAuth: true, role: 'user' }
  },
  {
    path: '/admin/dashboard',
    name: 'AdminDashboard',
    component: () => import('../views/AdminDashboard.vue'),
    meta: { requiresAuth: true, role: 'admin' }
  },
  {
    path: '/parking',
    name: 'Parking',
    component: () => import('../views/Parking.vue'),
    meta: { requiresAuth: true }
  },
  // Catch-all redirect
  {
    path: '/:pathMatch(.*)*',
    redirect: '/login'
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

// Navigation guard
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token');
  const userRole = localStorage.getItem('user_role');
  
  // If route requires authentication
  if (to.meta.requiresAuth) {
    if (!token) {
      // No token, redirect to login
      next({ name: 'Login', query: { redirect: to.fullPath } });
      return;
    }
    
    // Check role-based access
    if (to.meta.role) {
      if (to.meta.role === 'admin' && userRole !== 'admin') {
        // Non-admin trying to access admin route
        next({ name: 'UserDashboard' });
        return;
      }
      if (to.meta.role === 'user' && userRole === 'admin') {
        // Admin accessing user route - redirect to admin dashboard
        next({ name: 'AdminDashboard' });
        return;
      }
    }
  }
  
  // If route is for guests only (login/register) and user is logged in
  if (to.meta.guest && token) {
    if (userRole === 'admin') {
      next({ name: 'AdminDashboard' });
    } else {
      next({ name: 'UserDashboard' });
    }
    return;
  }
  
  next();
});

export default router;
