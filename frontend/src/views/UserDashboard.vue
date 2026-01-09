<template>
  <div class="container mt-4">
    <h2>User Dashboard</h2>
    <div class="row mb-4">
      <div class="col-md-3">
        <div class="card bg-light">
          <div class="card-body">
            <h5>Active</h5>
            <h3>{{ stats.active }}</h3>
          </div>
        </div>
      </div>
       <div class="col-md-3">
        <div class="card bg-light">
          <div class="card-body">
            <h5>Completed</h5>
             <h3>{{ stats.completed }}</h3>
          </div>
        </div>
      </div>
    </div>

    <div class="card">
        <div class="card-header">My Reservations</div>
        <div class="card-body">
            <table class="table">
                <thead>
                    <tr>
                        <th>Lot</th>
                        <th>Spot</th>
                        <th>Time In</th>
                        <th>Time Out</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="res in reservations" :key="res.id">
                        <td>{{ res.lot_name }}</td>
                        <td>{{ res.spot_no }}</td>
                        <td>{{ res.parking_time }}</td>
                        <td>{{ res.leaving_time }}</td>
                        <td>{{ res.status }}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
  </div>
</template>

<script>
import api from '../services/api';

export default {
    data() {
        return {
            reservations: [],
            stats: { active: 0, completed: 0 }
        }
    },
    async mounted() {
        try {
            const res = await api.get('/user/dashboard-data');
            this.reservations = res.data.reservations;
            this.stats = res.data.stats;
        } catch (e) {
            console.error(e);
        }
    }
}
</script>
