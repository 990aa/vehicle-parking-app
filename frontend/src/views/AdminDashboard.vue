<template>
  <div class="container mt-4">
    <h2>Admin Dashboard</h2>
    <div class="row mb-4">
       <div class="col-md-3">
        <div class="card text-white bg-primary">
          <div class="card-body">
            <h5>Total Lots</h5>
             <h3>{{ stats.total_lots }}</h3>
          </div>
        </div>
      </div>
       <div class="col-md-3">
        <div class="card text-white bg-success">
          <div class="card-body">
            <h5>Total Revenue</h5>
             <h3>${{ stats.total_revenue }}</h3>
          </div>
        </div>
      </div>
    </div>

    <div class="card">
        <div class="card-header">All Lots</div>
        <div class="card-body">
            <table class="table">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Address</th>
                        <th>Price/Hr</th>
                        <th>Occupancy</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="lot in lots" :key="lot.id">
                        <td>{{ lot.name }}</td>
                        <td>{{ lot.address }}</td>
                        <td>{{ lot.price }}</td>
                         <td>{{ lot.occupancy }}%</td>
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
            lots: [],
            stats: { total_lots: 0, total_revenue: 0 }
        }
    },
    async mounted() {
        try {
             const res = await api.get('/admin/dashboard-data');
             this.lots = res.data.lots;
             this.stats = res.data.stats;
        } catch (e) {
            console.error(e);
        }
    }
}
</script>
