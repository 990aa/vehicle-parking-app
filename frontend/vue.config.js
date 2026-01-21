const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  devServer: {
    port: 8080,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        secure: false,
        logLevel: 'debug'
      }
    }
  },
  pwa: {
    name: 'parkapp - Smart Parking',
    themeColor: '#1a56db',
    msTileColor: '#1a56db',
    manifestOptions: {
      short_name: 'parkapp',
      background_color: '#ffffff',
      display: 'standalone',
    },
    workboxOptions: {
      skipWaiting: true
    }
  }
})
