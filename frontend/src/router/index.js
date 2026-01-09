import { createRouter, createWebHistory } from 'vue-router';
import Login from '../views/Login.vue';
import UserDashboard from '../views/UserDashboard.vue';
import AdminDashboard from '../views/AdminDashboard.vue';

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue')
  },
  {
    path: '/user/dashboard',
    name: 'UserDashboard',
    component: UserDashboard,
    meta: { requiresAuth: true, role: 'user' }
  },
  {
    path: '/admin/dashboard',
    name: 'AdminDashboard',
    component: AdminDashboard,
    meta: { requiresAuth: true, role: 'admin' }
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach((to, from, next) => {
    const token = localStorage.getItem('access_token');
    const role = localStorage.getItem('user_role');

    if (to.meta.requiresAuth && !token) {
        next('/login');
    } else if (to.meta.role && to.meta.role !== role) {
        // Redirect if role doesn't match
        if (role === 'admin') next('/admin/dashboard');
        else if (role === 'user') next('/user/dashboard');
        else next('/login');
    } else {
        next();
    }
});

export default router;
