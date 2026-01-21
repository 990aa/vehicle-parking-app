<template>
  <div class="dashboard admin-dashboard">
    <div class="container">
      <!-- Page Header -->
      <div class="page-header">
        <div class="header-content">
          <h1>Admin Dashboard</h1>
          <p>Manage parking lots, users, and monitor system activity</p>
        </div>
        <button @click="showAddLotModal = true" class="btn btn-primary">
          Add Parking Lot
        </button>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="loading-container">
        <div class="loading-spinner-large"></div>
        <p>Loading dashboard data...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="error-container">
        <div class="error-icon">!</div>
        <h3>Failed to load dashboard</h3>
        <p>{{ error }}</p>
        <button @click="loadDashboard" class="btn btn-primary">Try Again</button>
      </div>

      <!-- Dashboard Content -->
      <template v-else>
        <!-- Stats Cards -->
        <div class="stats-grid">
          <div class="stat-card stat-card-primary">
            <div class="stat-icon">L</div>
            <div class="stat-content">
              <span class="stat-value">{{ stats.total_lots }}</span>
              <span class="stat-label">Total Lots</span>
            </div>
          </div>
          
          <div class="stat-card stat-card-info">
            <div class="stat-icon">P</div>
            <div class="stat-content">
              <span class="stat-value">{{ stats.total_spots }}</span>
              <span class="stat-label">Total Spots</span>
            </div>
          </div>
          
          <div class="stat-card stat-card-warning">
            <div class="stat-icon">O</div>
            <div class="stat-content">
              <span class="stat-value">{{ stats.total_occupied }}</span>
              <span class="stat-label">Occupied</span>
            </div>
          </div>
          
          <div class="stat-card stat-card-success">
            <div class="stat-icon">A</div>
            <div class="stat-content">
              <span class="stat-value">{{ stats.total_available }}</span>
              <span class="stat-label">Available</span>
            </div>
          </div>
          
          <div class="stat-card stat-card-secondary">
            <div class="stat-icon">U</div>
            <div class="stat-content">
              <span class="stat-value">{{ stats.total_users }}</span>
              <span class="stat-label">Users</span>
            </div>
          </div>
          
          <div class="stat-card stat-card-accent">
            <div class="stat-icon">R</div>
            <div class="stat-content">
              <span class="stat-value">{{ stats.total_reservations }}</span>
              <span class="stat-label">Reservations</span>
            </div>
          </div>
          
          <div class="stat-card stat-card-revenue">
            <div class="stat-icon">$</div>
            <div class="stat-content">
              <span class="stat-value">${{ stats.total_revenue.toFixed(2) }}</span>
              <span class="stat-label">Revenue</span>
            </div>
          </div>
          
          <div class="stat-card stat-card-rate">
            <div class="stat-icon">%</div>
            <div class="stat-content">
              <span class="stat-value">{{ stats.occupancy_rate }}%</span>
              <span class="stat-label">Occupancy</span>
            </div>
          </div>
        </div>

        <!-- Tabs -->
        <div class="tabs-container">
          <div class="tabs">
            <button 
              v-for="tab in tabs"
              :key="tab.id"
              :class="['tab', { active: activeTab === tab.id }]"
              @click="activeTab = tab.id"
            >
              <span class="tab-icon">{{ tab.icon }}</span>
              {{ tab.label }}
            </button>
          </div>
        </div>

        <!-- Tab Content -->
        <div class="tab-content">
          <!-- Parking Lots Tab -->
          <div v-if="activeTab === 'lots'" class="section">
            <div class="table-responsive">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Address</th>
                    <th>Price/Hr</th>
                    <th>Spots</th>
                    <th>Occupancy</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="lot in lots" :key="lot.id">
                    <td>
                      <div class="lot-name-cell">
                        <span class="lot-icon">L</span>
                        <span>{{ lot.name }}</span>
                      </div>
                    </td>
                    <td>{{ lot.address }}</td>
                    <td class="price-cell">${{ lot.price_per_hr.toFixed(2) }}</td>
                    <td>
                      <span class="spots-badge">
                        {{ lot.available }}/{{ lot.total_spots }}
                      </span>
                    </td>
                    <td>
                      <div class="occupancy-bar-container">
                        <div class="occupancy-bar">
                          <div 
                            class="occupancy-fill"
                            :style="{ width: lot.occupancy + '%' }"
                            :class="getOccupancyClass(lot.occupancy)"
                          ></div>
                        </div>
                        <span class="occupancy-text">{{ lot.occupancy }}%</span>
                      </div>
                    </td>
                    <td>
                      <span :class="['status-indicator', lot.available > 0 ? 'status-open' : 'status-full']">
                        {{ lot.available > 0 ? 'Open' : 'Full' }}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Users Tab -->
          <div v-if="activeTab === 'users'" class="section">
            <div v-if="usersLoading" class="section-loading">
              <div class="loading-spinner-large"></div>
            </div>
            <div v-else-if="users.length === 0" class="empty-state">
              <p>No users found</p>
            </div>
            <div v-else class="table-responsive">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>User</th>
                    <th>Email</th>
                    <th>Role</th>
                    <th>Status</th>
                    <th>Joined</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="user in users" :key="user.id">
                    <td>
                      <div class="user-cell">
                        <div class="user-avatar">{{ user.username.charAt(0).toUpperCase() }}</div>
                        <span>{{ user.username }}</span>
                      </div>
                    </td>
                    <td>{{ user.email }}</td>
                    <td>
                      <span :class="['role-badge', `role-${user.role}`]">
                        {{ user.role }}
                      </span>
                    </td>
                    <td>
                      <span :class="['status-indicator', user.active ? 'status-active' : 'status-inactive']">
                        {{ user.active ? 'Active' : 'Inactive' }}
                      </span>
                    </td>
                    <td>{{ formatDate(user.created_at) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Reservations Tab -->
          <div v-if="activeTab === 'reservations'" class="section">
            <div v-if="reservationsLoading" class="section-loading">
              <div class="loading-spinner-large"></div>
            </div>
            <div v-else-if="reservations.length === 0" class="empty-state">
              <p>No reservations found</p>
            </div>
            <div v-else class="table-responsive">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>User</th>
                    <th>Lot</th>
                    <th>Spot</th>
                    <th>Vehicle</th>
                    <th>Time</th>
                    <th>Cost</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="res in reservations" :key="res.id">
                    <td>#{{ res.id }}</td>
                    <td>{{ res.user }}</td>
                    <td>{{ res.lot_name }}</td>
                    <td>{{ res.spot_no }}</td>
                    <td>{{ res.vehicle_number }}</td>
                    <td>{{ formatDateTime(res.parking_time) }}</td>
                    <td>${{ res.cost ? res.cost.toFixed(2) : '0.00' }}</td>
                    <td>
                      <span :class="['status-badge', `status-${res.status}`]">
                        {{ res.status }}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </template>

      <!-- Add Lot Modal -->
      <div v-if="showAddLotModal" class="modal-overlay" @click.self="showAddLotModal = false">
        <div class="modal">
          <div class="modal-header">
            <h3>Add New Parking Lot</h3>
            <button class="modal-close" @click="showAddLotModal = false">×</button>
          </div>
          <form @submit.prevent="createLot" class="modal-body">
            <div class="form-group">
              <label class="form-label">Lot Name</label>
              <input 
                v-model="newLot.name" 
                type="text" 
                class="form-input" 
                placeholder="e.g., Downtown Central Parking"
                required
              />
            </div>
            <div class="form-group">
              <label class="form-label">Address</label>
              <input 
                v-model="newLot.address" 
                type="text" 
                class="form-input" 
                placeholder="Full address"
                required
              />
            </div>
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">PIN Code</label>
                <input 
                  v-model="newLot.pin_code" 
                  type="text" 
                  class="form-input" 
                  placeholder="10001"
                  required
                />
              </div>
              <div class="form-group">
                <label class="form-label">Price per Hour ($)</label>
                <input 
                  v-model.number="newLot.price_per_hr" 
                  type="number" 
                  step="0.01"
                  min="0"
                  class="form-input" 
                  placeholder="5.00"
                  required
                />
              </div>
            </div>
            <div class="form-group">
              <label class="form-label">Number of Spots</label>
              <input 
                v-model.number="newLot.max_spots" 
                type="number" 
                min="1"
                class="form-input" 
                placeholder="50"
                required
              />
            </div>
            <div class="modal-actions">
              <button type="button" class="btn btn-secondary" @click="showAddLotModal = false">
                Cancel
              </button>
              <button type="submit" class="btn btn-primary" :disabled="creatingLot">
                <span v-if="creatingLot" class="loading-spinner-sm"></span>
                <span v-else>Create Lot</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { adminAPI } from '../services/api';

export default {
  name: 'AdminDashboard',
  data() {
    return {
      isLoading: true,
      error: null,
      lots: [],
      users: [],
      reservations: [],
      stats: {
        total_lots: 0,
        total_spots: 0,
        total_occupied: 0,
        total_available: 0,
        total_users: 0,
        total_reservations: 0,
        total_revenue: 0,
        occupancy_rate: 0
      },
      activeTab: 'lots',
      usersLoading: false,
      reservationsLoading: false,
      showAddLotModal: false,
      creatingLot: false,
      newLot: {
        name: '',
        address: '',
        pin_code: '',
        price_per_hr: null,
        max_spots: null
      },
      tabs: [
        { id: 'lots', label: 'Parking Lots', icon: 'L' },
        { id: 'users', label: 'Users', icon: 'U' },
        { id: 'reservations', label: 'Reservations', icon: 'R' }
      ]
    };
  },
  methods: {
    async loadDashboard() {
      this.isLoading = true;
      this.error = null;
      
      try {
        const response = await adminAPI.getDashboardData();
        this.lots = response.data.lots || [];
        this.stats = response.data.stats || this.stats;
      } catch (error) {
        console.error('Dashboard error:', error);
        this.error = error.message || 'Failed to load dashboard data';
      } finally {
        this.isLoading = false;
      }
    },
    
    async loadUsers() {
      if (this.users.length > 0) return;
      
      this.usersLoading = true;
      try {
        const response = await adminAPI.getUsers();
        this.users = response.data.users || [];
      } catch (error) {
        console.error('Users error:', error);
      } finally {
        this.usersLoading = false;
      }
    },
    
    async loadReservations() {
      if (this.reservations.length > 0) return;
      
      this.reservationsLoading = true;
      try {
        const response = await adminAPI.getReservations();
        this.reservations = response.data.reservations || [];
      } catch (error) {
        console.error('Reservations error:', error);
      } finally {
        this.reservationsLoading = false;
      }
    },
    
    async createLot() {
      this.creatingLot = true;
      
      try {
        await adminAPI.createLot(this.newLot);
        this.showAddLotModal = false;
        this.newLot = { name: '', address: '', pin_code: '', price_per_hr: null, max_spots: null };
        await this.loadDashboard();
      } catch (error) {
        console.error('Create lot error:', error);
        alert(error.message || 'Failed to create parking lot');
      } finally {
        this.creatingLot = false;
      }
    },
    
    getOccupancyClass(occupancy) {
      if (occupancy < 50) return 'low';
      if (occupancy < 80) return 'medium';
      return 'high';
    },
    
    formatDate(dateString) {
      if (!dateString) return '-';
      return new Date(dateString).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      });
    },
    
    formatDateTime(dateString) {
      if (!dateString) return '-';
      return new Date(dateString).toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    }
  },
  watch: {
    activeTab(newTab) {
      if (newTab === 'users') this.loadUsers();
      if (newTab === 'reservations') this.loadReservations();
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
  max-width: 1400px;
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

/* Buttons */
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
}

.btn-primary {
  background: var(--primary);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: var(--primary-light);
}

.btn-secondary {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.btn-secondary:hover {
  background: var(--bg-secondary);
}

.btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

/* Loading */
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

.section-loading {
  display: flex;
  justify-content: center;
  padding: 60px;
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 32px;
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
  background: var(--bg-tertiary);
}

.stat-card-primary .stat-icon { background: #dbeafe; }
.stat-card-info .stat-icon { background: #e0e7ff; }
.stat-card-warning .stat-icon { background: #fef3c7; }
.stat-card-success .stat-icon { background: #d1fae5; }
.stat-card-secondary .stat-icon { background: #f3e8ff; }
.stat-card-accent .stat-icon { background: #fce7f3; }
.stat-card-revenue .stat-icon { background: #dcfce7; }
.stat-card-rate .stat-icon { background: #fed7aa; }

.stat-content {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
}

.stat-label {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin-top: 4px;
}

/* Tabs */
.tabs-container {
  margin-bottom: 24px;
}

.tabs {
  display: flex;
  gap: 8px;
  background: var(--bg-primary);
  padding: 8px;
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-color);
}

.tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: transparent;
  border: none;
  border-radius: var(--border-radius-sm);
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  transition: var(--transition);
}

.tab:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.tab.active {
  background: var(--primary);
  color: white;
}

.tab-icon {
  font-size: 1.1rem;
}

/* Section */
.section {
  background: var(--bg-primary);
  border-radius: var(--border-radius-lg);
  padding: 24px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-color);
}

/* Table */
.table-responsive {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 16px;
  text-align: left;
  border-bottom: 1px solid var(--border-color);
}

.data-table th {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  background: var(--bg-tertiary);
}

.data-table tbody tr:hover {
  background: var(--bg-secondary);
}

.lot-name-cell {
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 500;
}

.lot-icon {
  font-size: 1.25rem;
}

.price-cell {
  font-weight: 600;
  color: var(--primary);
}

.spots-badge {
  padding: 4px 12px;
  background: var(--bg-tertiary);
  border-radius: 20px;
  font-size: 0.875rem;
  font-weight: 500;
}

.occupancy-bar-container {
  display: flex;
  align-items: center;
  gap: 12px;
}

.occupancy-bar {
  flex: 1;
  height: 8px;
  background: var(--bg-tertiary);
  border-radius: 4px;
  overflow: hidden;
  min-width: 100px;
}

.occupancy-fill {
  height: 100%;
  transition: width 0.3s ease;
}

.occupancy-fill.low { background: var(--success); }
.occupancy-fill.medium { background: var(--warning); }
.occupancy-fill.high { background: var(--danger); }

.occupancy-text {
  font-size: 0.875rem;
  font-weight: 500;
  min-width: 40px;
}

.status-indicator {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
}

.status-open { background: #d1fae5; color: #047857; }
.status-full { background: #fee2e2; color: #b91c1c; }
.status-active { background: #d1fae5; color: #047857; }
.status-inactive { background: #fee2e2; color: #b91c1c; }

.user-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--primary);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.875rem;
}

.role-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: capitalize;
}

.role-admin { background: #fef3c7; color: #b45309; }
.role-user { background: #dbeafe; color: #1d4ed8; }

.status-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: capitalize;
}

.status-upcoming { background: #dbeafe; color: #1d4ed8; }
.status-active { background: #fef3c7; color: #b45309; }
.status-completed { background: #d1fae5; color: #047857; }
.status-cancelled { background: #fee2e2; color: #b91c1c; }

/* Empty State */
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-secondary);
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 24px;
}

.modal {
  background: var(--bg-primary);
  border-radius: var(--border-radius-lg);
  width: 100%;
  max-width: 500px;
  box-shadow: var(--shadow-lg);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  font-size: 1.25rem;
  font-weight: 600;
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: var(--text-light);
  padding: 4px;
}

.modal-close:hover {
  color: var(--text-primary);
}

.modal-body {
  padding: 24px;
}

.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.form-input {
  width: 100%;
  padding: 12px 16px;
  font-size: 1rem;
  border: 2px solid var(--border-color);
  border-radius: var(--border-radius-sm);
  transition: var(--transition);
}

.form-input:focus {
  outline: none;
  border-color: var(--primary);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 8px;
}

/* Responsive */
@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

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
  
  .tabs {
    flex-direction: column;
  }
  
  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>
