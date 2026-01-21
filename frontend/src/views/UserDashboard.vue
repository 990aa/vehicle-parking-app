<template>
  <div class="dashboard">
    <div class="container">
      <!-- Page Header -->
      <div class="page-header">
        <div class="header-content">
          <h1>Welcome back, {{ userName }}! 👋</h1>
          <p>Manage your parking reservations and find new spots</p>
        </div>
        <router-link to="/parking" class="btn btn-primary">
          <span>🅿️</span> Find Parking
        </router-link>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="loading-container">
        <div class="loading-spinner-large"></div>
        <p>Loading your dashboard...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="error-container">
        <div class="error-icon">⚠️</div>
        <h3>Failed to load dashboard</h3>
        <p>{{ error }}</p>
        <button @click="loadDashboard" class="btn btn-primary">Try Again</button>
      </div>

      <!-- Dashboard Content -->
      <template v-else>
        <!-- Stats Cards -->
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon stat-icon-upcoming">📅</div>
            <div class="stat-content">
              <span class="stat-value">{{ stats.upcoming }}</span>
              <span class="stat-label">Upcoming</span>
            </div>
          </div>
          
          <div class="stat-card">
            <div class="stat-icon stat-icon-active">🚗</div>
            <div class="stat-content">
              <span class="stat-value">{{ stats.active }}</span>
              <span class="stat-label">Active</span>
            </div>
          </div>
          
          <div class="stat-card">
            <div class="stat-icon stat-icon-completed">✅</div>
            <div class="stat-content">
              <span class="stat-value">{{ stats.completed }}</span>
              <span class="stat-label">Completed</span>
            </div>
          </div>
          
          <div class="stat-card">
            <div class="stat-icon stat-icon-cancelled">❌</div>
            <div class="stat-content">
              <span class="stat-value">{{ stats.cancelled }}</span>
              <span class="stat-label">Cancelled</span>
            </div>
          </div>
        </div>

        <!-- Reservations Section -->
        <div class="section">
          <div class="section-header">
            <h2>My Reservations</h2>
            <div class="filter-tabs">
              <button 
                v-for="filter in filters"
                :key="filter.value"
                :class="['filter-tab', { active: activeFilter === filter.value }]"
                @click="activeFilter = filter.value"
              >
                {{ filter.label }}
              </button>
            </div>
          </div>

          <!-- Empty State -->
          <div v-if="filteredReservations.length === 0" class="empty-state">
            <div class="empty-icon">🚗</div>
            <h3>No {{ activeFilter === 'all' ? '' : activeFilter }} reservations</h3>
            <p>Book a parking spot to get started</p>
            <router-link to="/parking" class="btn btn-primary">Find Parking</router-link>
          </div>

          <!-- Reservations Grid -->
          <div v-else class="reservations-grid">
            <div 
              v-for="reservation in filteredReservations" 
              :key="reservation.id"
              class="reservation-card"
            >
              <div class="reservation-header">
                <span :class="['status-badge', `status-${reservation.status}`]">
                  {{ reservation.status }}
                </span>
                <span class="reservation-id">#{{ reservation.id }}</span>
              </div>
              
              <div class="reservation-body">
                <h3 class="lot-name">{{ reservation.lot_name }}</h3>
                <p class="lot-address">{{ reservation.lot_address }}</p>
                
                <div class="reservation-details">
                  <div class="detail-item">
                    <span class="detail-icon">🅿️</span>
                    <span>Spot {{ reservation.spot_no }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-icon">🚙</span>
                    <span>{{ reservation.vehicle_number }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-icon">📅</span>
                    <span>{{ formatDate(reservation.parking_time) }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-icon">⏰</span>
                    <span>{{ formatTime(reservation.parking_time) }} - {{ formatTime(reservation.leaving_time) }}</span>
                  </div>
                </div>
                
                <div class="reservation-cost" v-if="reservation.cost">
                  <span class="cost-label">Estimated Cost</span>
                  <span class="cost-value">${{ reservation.cost.toFixed(2) }}</span>
                </div>
              </div>
              
              <div class="reservation-actions" v-if="canCancel(reservation)">
                <button 
                  @click="cancelReservation(reservation.id)"
                  class="btn btn-danger btn-sm"
                  :disabled="cancelling === reservation.id"
                >
                  <span v-if="cancelling === reservation.id" class="loading-spinner-sm"></span>
                  <span v-else>Cancel Reservation</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script>
import { userAPI, parkingAPI } from '../services/api';

export default {
  name: 'UserDashboard',
  data() {
    return {
      isLoading: true,
      error: null,
      reservations: [],
      stats: {
        upcoming: 0,
        active: 0,
        completed: 0,
        cancelled: 0
      },
      activeFilter: 'all',
      cancelling: null,
      filters: [
        { label: 'All', value: 'all' },
        { label: 'Upcoming', value: 'upcoming' },
        { label: 'Active', value: 'active' },
        { label: 'Completed', value: 'completed' }
      ]
    };
  },
  computed: {
    userName() {
      try {
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        return user.username || 'User';
      } catch {
        return 'User';
      }
    },
    filteredReservations() {
      if (this.activeFilter === 'all') {
        return this.reservations;
      }
      return this.reservations.filter(r => r.status === this.activeFilter);
    }
  },
  methods: {
    async loadDashboard() {
      this.isLoading = true;
      this.error = null;
      
      try {
        const response = await userAPI.getDashboardData();
        this.reservations = response.data.reservations || [];
        this.stats = response.data.stats || { upcoming: 0, active: 0, completed: 0, cancelled: 0 };
      } catch (error) {
        console.error('Dashboard error:', error);
        this.error = error.message || 'Failed to load dashboard data';
      } finally {
        this.isLoading = false;
      }
    },
    
    canCancel(reservation) {
      return ['upcoming', 'active'].includes(reservation.status);
    },
    
    async cancelReservation(id) {
      if (!confirm('Are you sure you want to cancel this reservation?')) {
        return;
      }
      
      this.cancelling = id;
      
      try {
        await parkingAPI.cancelReservation(id);
        // Update local state
        const reservation = this.reservations.find(r => r.id === id);
        if (reservation) {
          // Decrement old status count
          if (this.stats[reservation.status] !== undefined) {
            this.stats[reservation.status]--;
          }
          // Update status
          reservation.status = 'cancelled';
          // Increment cancelled count
          this.stats.cancelled++;
        }
      } catch (error) {
        console.error('Cancel error:', error);
        alert(error.message || 'Failed to cancel reservation');
      } finally {
        this.cancelling = null;
      }
    },
    
    formatDate(dateString) {
      if (!dateString) return '-';
      return new Date(dateString).toLocaleDateString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric'
      });
    },
    
    formatTime(dateString) {
      if (!dateString) return '-';
      return new Date(dateString).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
      });
    }
  },
  mounted() {
    this.loadDashboard();
  }
};
</script>

<style scoped>
.dashboard {
  padding: 32px 0;
  min-height: calc(100vh - var(--navbar-height));
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
}

/* Page Header */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  flex-wrap: wrap;
  gap: 16px;
}

.header-content h1 {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.header-content p {
  color: var(--text-secondary);
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  font-size: 0.95rem;
  font-weight: 600;
  border-radius: var(--border-radius-sm);
  cursor: pointer;
  transition: var(--transition);
  border: none;
  text-decoration: none;
}

.btn-primary {
  background: var(--primary);
  color: white;
}

.btn-primary:hover {
  background: var(--primary-light);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.btn-danger {
  background: var(--danger);
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background: #dc2626;
}

.btn-sm {
  padding: 8px 16px;
  font-size: 0.875rem;
}

.btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

/* Loading & Error States */
.loading-container,
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  text-align: center;
}

.loading-spinner-large {
  width: 48px;
  height: 48px;
  border: 4px solid var(--border-color);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

.loading-spinner-sm {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-icon {
  font-size: 3rem;
  margin-bottom: 16px;
}

.error-container h3 {
  margin-bottom: 8px;
  color: var(--text-primary);
}

.error-container p {
  color: var(--text-secondary);
  margin-bottom: 24px;
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 40px;
}

.stat-card {
  background: var(--bg-primary);
  border-radius: var(--border-radius);
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-color);
  transition: var(--transition);
}

.stat-card:hover {
  box-shadow: var(--shadow);
  transform: translateY(-2px);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: var(--border-radius);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
}

.stat-icon-upcoming { background: #dbeafe; }
.stat-icon-active { background: #fef3c7; }
.stat-icon-completed { background: #d1fae5; }
.stat-icon-cancelled { background: #fee2e2; }

.stat-content {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
}

.stat-label {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin-top: 4px;
}

/* Section */
.section {
  background: var(--bg-primary);
  border-radius: var(--border-radius-lg);
  padding: 24px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-color);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;
}

.section-header h2 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
}

.filter-tabs {
  display: flex;
  gap: 8px;
  background: var(--bg-tertiary);
  padding: 4px;
  border-radius: var(--border-radius-sm);
}

.filter-tab {
  padding: 8px 16px;
  background: transparent;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  transition: var(--transition);
}

.filter-tab:hover {
  color: var(--text-primary);
}

.filter-tab.active {
  background: var(--bg-primary);
  color: var(--primary);
  box-shadow: var(--shadow-sm);
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-state h3 {
  font-size: 1.25rem;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.empty-state p {
  color: var(--text-secondary);
  margin-bottom: 24px;
}

/* Reservations Grid */
.reservations-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.reservation-card {
  background: var(--bg-secondary);
  border-radius: var(--border-radius);
  overflow: hidden;
  border: 1px solid var(--border-color);
  transition: var(--transition);
}

.reservation-card:hover {
  box-shadow: var(--shadow);
  transform: translateY(-2px);
}

.reservation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: var(--bg-tertiary);
  border-bottom: 1px solid var(--border-color);
}

.status-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: capitalize;
}

.status-upcoming {
  background: #dbeafe;
  color: #1d4ed8;
}

.status-active {
  background: #fef3c7;
  color: #b45309;
}

.status-completed {
  background: #d1fae5;
  color: #047857;
}

.status-cancelled {
  background: #fee2e2;
  color: #b91c1c;
}

.reservation-id {
  font-size: 0.8rem;
  color: var(--text-light);
  font-weight: 500;
}

.reservation-body {
  padding: 20px;
}

.lot-name {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.lot-address {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin-bottom: 16px;
}

.reservation-details {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 16px;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.detail-icon {
  font-size: 1rem;
}

.reservation-cost {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
}

.cost-label {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.cost-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--primary);
}

.reservation-actions {
  padding: 16px;
  background: var(--bg-tertiary);
  border-top: 1px solid var(--border-color);
}

/* Responsive */
@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .section-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .reservation-details {
    grid-template-columns: 1fr;
  }
}
</style>
