const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  pwa: {
    name: 'Vehicle Parking App',
    themeColor: '#0d6efd',
    msTileColor: '#0d6efd',
    manifestOptions: {
      short_name: 'ParkingApp',
      background_color: '#ffffff',
      display: 'standalone',
    },
    workboxOptions: {
      skipWaiting: true
    }
  }
})
