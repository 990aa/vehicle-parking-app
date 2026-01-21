<template>
  <div class="parking-page">
    <div class="container">
      <!-- Page Header -->
      <div class="page-header">
        <div class="header-content">
          <h1>Find Parking</h1>
          <p>Browse available parking lots and reserve your spot</p>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="loading-container">
        <div class="loading-spinner-large"></div>
        <p>Loading parking lots...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="error-container">
        <div class="error-icon">!</div>
        <h3>Failed to load parking lots</h3>
        <p>{{ error }}</p>
        <button @click="loadLots" class="btn btn-primary">Try Again</button>
      </div>

      <!-- Content -->
      <template v-else>
        <!-- Empty State -->
        <div v-if="lots.length === 0" class="empty-state">
          <div class="empty-icon">P</div>
          <h3>No parking lots available</h3>
          <p>Check back later for available parking options</p>
        </div>

        <!-- Parking Lots Grid -->
        <div v-else class="lots-grid">
          <div 
            v-for="lot in lots" 
            :key="lot.id"
            class="lot-card"
          >
            <div class="lot-header">
              <div class="lot-availability" :class="lot.available_spots > 0 ? 'available' : 'full'">
                {{ lot.available_spots > 0 ? `${lot.available_spots} spots` : 'Full' }}
              </div>
              <div class="lot-price">
                <span class="price-value">${{ lot.price_per_hr.toFixed(2) }}</span>
                <span class="price-unit">/hr</span>
              </div>
            </div>
            
            <div class="lot-body">
              <h3 class="lot-name">{{ lot.name }}</h3>
              <p class="lot-address">
                <span class="address-icon">@</span>
                {{ lot.address }}
              </p>
              
              <div class="lot-stats">
                <div class="stat">
                  <span class="stat-value">{{ lot.total_spots }}</span>
                  <span class="stat-label">Total</span>
                </div>
                <div class="stat">
                  <span class="stat-value text-success">{{ lot.available_spots }}</span>
                  <span class="stat-label">Available</span>
                </div>
                <div class="stat">
                  <span class="stat-value text-warning">{{ lot.occupancy }}%</span>
                  <span class="stat-label">Occupied</span>
                </div>
              </div>
              
              <div class="occupancy-bar">
                <div 
                  class="occupancy-fill"
                  :style="{ width: lot.occupancy + '%' }"
                  :class="getOccupancyClass(lot.occupancy)"
                ></div>
              </div>
            </div>
            
            <div class="lot-footer">
              <button 
                @click="openReservationModal(lot)"
                class="btn btn-primary btn-block"
                :disabled="lot.available_spots === 0"
              >
                {{ lot.available_spots > 0 ? 'Reserve Spot' : 'No Spots Available' }}
              </button>
            </div>
          </div>
        </div>
      </template>

      <!-- Reservation Modal -->
      <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
        <div class="modal">
          <div class="modal-header">
            <h3>Reserve Parking Spot</h3>
            <button class="modal-close" @click="closeModal">×</button>
          </div>
          
          <div class="modal-body">
            <!-- Selected Lot Info -->
            <div class="selected-lot-info">
              <h4>{{ selectedLot.name }}</h4>
              <p>{{ selectedLot.address }}</p>
              <p class="price-info">${{ selectedLot.price_per_hr.toFixed(2) }} per hour</p>
            </div>

            <!-- Error Message -->
            <div v-if="reservationError" class="alert alert-error">
              <span>!</span>
              <span>{{ reservationError }}</span>
            </div>

            <!-- Step 1: Select Spot -->
            <div v-if="reservationStep === 1" class="reservation-step">
              <h4>Step 1: Select a Spot</h4>
              
              <div v-if="loadingSpots" class="spots-loading">
                <div class="loading-spinner-large"></div>
                <p>Loading available spots...</p>
              </div>
              
              <div v-else class="spots-grid">
                <button 
                  v-for="spot in spots"
                  :key="spot.id"
                  :class="['spot-btn', { 
                    'available': spot.status === 'available',
                    'occupied': spot.status === 'occupied',
                    'selected': selectedSpot?.id === spot.id
                  }]"
                  :disabled="spot.status === 'occupied'"
                  @click="selectSpot(spot)"
                >
                  {{ spot.spot_no }}
                </button>
              </div>
              
              <div class="spots-legend">
                <span class="legend-item"><span class="legend-color available"></span> Available</span>
                <span class="legend-item"><span class="legend-color occupied"></span> Occupied</span>
                <span class="legend-item"><span class="legend-color selected"></span> Selected</span>
              </div>
              
              <button 
                @click="reservationStep = 2"
                class="btn btn-primary btn-block"
                :disabled="!selectedSpot"
              >
                Continue
              </button>
            </div>

            <!-- Step 2: Enter Details -->
            <div v-if="reservationStep === 2" class="reservation-step">
              <h4>Step 2: Enter Details</h4>
              
              <div class="form-group">
                <label class="form-label">Vehicle Number</label>
                <input 
                  v-model="reservationForm.vehicle_number"
                  type="text"
                  class="form-input"
                  placeholder="e.g., ABC-1234"
                />
              </div>
              
              <div class="form-row">
                <div class="form-group">
                  <label class="form-label">Parking Date</label>
                  <input 
                    v-model="reservationForm.date"
                    type="date"
                    class="form-input"
                    :min="minDate"
                  />
                </div>
              </div>
              
              <div class="form-row">
                <div class="form-group">
                  <label class="form-label">Start Time</label>
                  <input 
                    v-model="reservationForm.start_time"
                    type="time"
                    class="form-input"
                  />
                </div>
                <div class="form-group">
                  <label class="form-label">End Time</label>
                  <input 
                    v-model="reservationForm.end_time"
                    type="time"
                    class="form-input"
                  />
                </div>
              </div>
              
              <div v-if="estimatedCost" class="cost-summary">
                <div class="cost-row">
                  <span>Duration</span>
                  <span>{{ duration }} hours</span>
                </div>
                <div class="cost-row">
                  <span>Rate</span>
                  <span>${{ selectedLot.price_per_hr.toFixed(2) }}/hr</span>
                </div>
                <div class="cost-row total">
                  <span>Estimated Total</span>
                  <span>${{ estimatedCost.toFixed(2) }}</span>
                </div>
              </div>
              
              <div class="step-actions">
                <button @click="reservationStep = 1" class="btn btn-secondary">
                  Back
                </button>
                <button 
                  @click="submitReservation"
                  class="btn btn-primary"
                  :disabled="!canSubmit || isSubmitting"
                >
                  <span v-if="isSubmitting" class="loading-spinner-sm"></span>
                  <span v-else>Confirm Reservation</span>
                </button>
              </div>
            </div>

            <!-- Step 3: Confirmation -->
            <div v-if="reservationStep === 3" class="reservation-step confirmation">
              <div class="success-icon">OK</div>
              <h4>Reservation Confirmed!</h4>
              <p>Your parking spot has been reserved successfully.</p>
              
              <div class="confirmation-details">
                <div class="detail-row">
                  <span>Spot Number</span>
                  <span>{{ selectedSpot.spot_no }}</span>
                </div>
                <div class="detail-row">
                  <span>Vehicle</span>
                  <span>{{ reservationForm.vehicle_number }}</span>
                </div>
                <div class="detail-row">
                  <span>Date</span>
                  <span>{{ formatDate(reservationForm.date) }}</span>
                </div>
                <div class="detail-row">
                  <span>Time</span>
                  <span>{{ reservationForm.start_time }} - {{ reservationForm.end_time }}</span>
                </div>
                <div class="detail-row total">
                  <span>Total Cost</span>
                  <span>${{ estimatedCost.toFixed(2) }}</span>
                </div>
              </div>
              
              <button @click="closeModal" class="btn btn-primary btn-block">
                Done
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { parkingAPI } from '../services/api';

export default {
  name: 'ParkingView',
  data() {
    return {
      isLoading: true,
      error: null,
      lots: [],
      showModal: false,
      selectedLot: null,
      spots: [],
      loadingSpots: false,
      selectedSpot: null,
      reservationStep: 1,
      reservationError: null,
      isSubmitting: false,
      reservationForm: {
        vehicle_number: '',
        date: '',
        start_time: '',
        end_time: ''
      }
    };
  },
  computed: {
    minDate() {
      return new Date().toISOString().split('T')[0];
    },
    duration() {
      if (!this.reservationForm.start_time || !this.reservationForm.end_time) return 0;
      
      const start = this.timeToMinutes(this.reservationForm.start_time);
      const end = this.timeToMinutes(this.reservationForm.end_time);
      
      let diff = end - start;
      if (diff <= 0) diff += 24 * 60; // Handle overnight
      
      return Math.round(diff / 60 * 10) / 10; // Round to 1 decimal
    },
    estimatedCost() {
      if (!this.selectedLot || !this.duration) return null;
      return this.duration * this.selectedLot.price_per_hr;
    },
    canSubmit() {
      return (
        this.selectedSpot &&
        this.reservationForm.vehicle_number &&
        this.reservationForm.date &&
        this.reservationForm.start_time &&
        this.reservationForm.end_time &&
        this.duration > 0
      );
    }
  },
  methods: {
    async loadLots() {
      this.isLoading = true;
      this.error = null;
      
      try {
        const response = await parkingAPI.getLots();
        this.lots = response.data.lots || [];
      } catch (error) {
        console.error('Error loading lots:', error);
        this.error = error.message || 'Failed to load parking lots';
      } finally {
        this.isLoading = false;
      }
    },
    
    async openReservationModal(lot) {
      this.selectedLot = lot;
      this.showModal = true;
      this.reservationStep = 1;
      this.selectedSpot = null;
      this.reservationError = null;
      this.reservationForm = {
        vehicle_number: '',
        date: this.minDate,
        start_time: '',
        end_time: ''
      };
      
      await this.loadSpots(lot.id);
    },
    
    async loadSpots(lotId) {
      this.loadingSpots = true;
      
      try {
        const response = await parkingAPI.getSpots(lotId);
        this.spots = response.data.spots || [];
      } catch (error) {
        console.error('Error loading spots:', error);
        this.reservationError = 'Failed to load parking spots';
      } finally {
        this.loadingSpots = false;
      }
    },
    
    selectSpot(spot) {
      if (spot.status === 'available') {
        this.selectedSpot = spot;
      }
    },
    
    closeModal() {
      this.showModal = false;
      this.selectedLot = null;
      this.selectedSpot = null;
      this.spots = [];
      
      // Refresh lots if reservation was made
      if (this.reservationStep === 3) {
        this.loadLots();
      }
    },
    
    async submitReservation() {
      if (!this.canSubmit) return;
      
      this.isSubmitting = true;
      this.reservationError = null;
      
      try {
        const parkingTime = `${this.reservationForm.date}T${this.reservationForm.start_time}:00`;
        const leavingTime = `${this.reservationForm.date}T${this.reservationForm.end_time}:00`;
        
        await parkingAPI.reserve({
          spot_id: this.selectedSpot.id,
          vehicle_number: this.reservationForm.vehicle_number,
          parking_time: parkingTime,
          leaving_time: leavingTime
        });
        
        this.reservationStep = 3;
        
      } catch (error) {
        console.error('Reservation error:', error);
        this.reservationError = error.message || 'Failed to create reservation';
      } finally {
        this.isSubmitting = false;
      }
    },
    
    getOccupancyClass(occupancy) {
      if (occupancy < 50) return 'low';
      if (occupancy < 80) return 'medium';
      return 'high';
    },
    
    timeToMinutes(time) {
      const [hours, minutes] = time.split(':').map(Number);
      return hours * 60 + minutes;
    },
    
    formatDate(dateString) {
      return new Date(dateString).toLocaleDateString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric'
      });
    }
  },
  mounted() {
    this.loadLots();
  }
};
</script>

<style scoped>
.parking-page {
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
  margin-bottom: 32px;
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

/* Loading & Error */
.loading-container,
.error-container,
.empty-state {
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

.empty-icon,
.error-icon {
  font-size: 4rem;
  margin-bottom: 16px;
  opacity: 0.5;
}

/* Buttons */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
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

.btn-block {
  width: 100%;
}

.btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

/* Lots Grid */
.lots-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 24px;
}

.lot-card {
  background: var(--bg-primary);
  border-radius: var(--border-radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-color);
  transition: var(--transition);
}

.lot-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-4px);
}

.lot-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: var(--bg-tertiary);
}

.lot-availability {
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
}

.lot-availability.available {
  background: #d1fae5;
  color: #047857;
}

.lot-availability.full {
  background: #fee2e2;
  color: #b91c1c;
}

.lot-price {
  text-align: right;
}

.price-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--primary);
}

.price-unit {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.lot-body {
  padding: 20px;
}

.lot-name {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.lot-address {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-secondary);
  font-size: 0.9rem;
  margin-bottom: 20px;
}

.lot-stats {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}

.stat {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
  text-transform: uppercase;
}

.text-success { color: var(--success); }
.text-warning { color: var(--warning); }

.occupancy-bar {
  height: 8px;
  background: var(--bg-tertiary);
  border-radius: 4px;
  overflow: hidden;
}

.occupancy-fill {
  height: 100%;
  transition: width 0.3s ease;
}

.occupancy-fill.low { background: var(--success); }
.occupancy-fill.medium { background: var(--warning); }
.occupancy-fill.high { background: var(--danger); }

.lot-footer {
  padding: 16px 20px;
  border-top: 1px solid var(--border-color);
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
  max-width: 560px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-lg);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color);
  position: sticky;
  top: 0;
  background: var(--bg-primary);
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
}

.modal-body {
  padding: 24px;
}

.selected-lot-info {
  background: var(--bg-tertiary);
  padding: 16px;
  border-radius: var(--border-radius-sm);
  margin-bottom: 24px;
}

.selected-lot-info h4 {
  font-size: 1.1rem;
  margin-bottom: 4px;
}

.selected-lot-info p {
  color: var(--text-secondary);
  font-size: 0.9rem;
  margin-bottom: 4px;
}

.price-info {
  color: var(--primary) !important;
  font-weight: 600;
}

.alert {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-radius: var(--border-radius-sm);
  margin-bottom: 20px;
}

.alert-error {
  background: #fef2f2;
  color: #991b1b;
  border: 1px solid #fecaca;
}

.reservation-step h4 {
  margin-bottom: 20px;
  font-size: 1rem;
}

/* Spots Grid */
.spots-loading {
  text-align: center;
  padding: 40px;
}

.spots-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(50px, 1fr));
  gap: 8px;
  margin-bottom: 16px;
}

.spot-btn {
  aspect-ratio: 1;
  border: 2px solid var(--border-color);
  border-radius: var(--border-radius-sm);
  background: var(--bg-primary);
  font-weight: 600;
  cursor: pointer;
  transition: var(--transition);
}

.spot-btn.available {
  border-color: var(--success);
  color: var(--success);
}

.spot-btn.available:hover {
  background: var(--success);
  color: white;
}

.spot-btn.occupied {
  border-color: var(--border-color);
  color: var(--text-light);
  background: var(--bg-tertiary);
  cursor: not-allowed;
}

.spot-btn.selected {
  background: var(--primary);
  border-color: var(--primary);
  color: white;
}

.spots-legend {
  display: flex;
  gap: 20px;
  margin-bottom: 24px;
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 4px;
  border: 2px solid;
}

.legend-color.available { border-color: var(--success); }
.legend-color.occupied { border-color: var(--border-color); background: var(--bg-tertiary); }
.legend-color.selected { border-color: var(--primary); background: var(--primary); }

/* Form */
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

/* Cost Summary */
.cost-summary {
  background: var(--bg-tertiary);
  padding: 16px;
  border-radius: var(--border-radius-sm);
  margin-bottom: 24px;
}

.cost-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-secondary);
}

.cost-row:last-child {
  border-bottom: none;
}

.cost-row.total {
  font-weight: 700;
  color: var(--text-primary);
  font-size: 1.1rem;
  padding-top: 12px;
}

.step-actions {
  display: flex;
  gap: 12px;
}

.step-actions .btn {
  flex: 1;
}

/* Confirmation */
.confirmation {
  text-align: center;
}

.success-icon {
  font-size: 4rem;
  margin-bottom: 16px;
}

.confirmation h4 {
  font-size: 1.5rem;
}

.confirmation-details {
  background: var(--bg-tertiary);
  padding: 20px;
  border-radius: var(--border-radius-sm);
  margin: 24px 0;
  text-align: left;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid var(--border-color);
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-row.total {
  font-weight: 700;
  font-size: 1.1rem;
  padding-top: 16px;
}

/* Responsive */
@media (max-width: 640px) {
  .lots-grid {
    grid-template-columns: 1fr;
  }
  
  .form-row {
    grid-template-columns: 1fr;
  }
  
  .step-actions {
    flex-direction: column;
  }
}
</style>
