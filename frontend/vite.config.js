import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  build: {
    // Increase the warning limit to eliminate the warning
    chunkSizeWarningLimit: 600,
    
    rollupOptions: {
      output: {
        // Code splitting configuration
        manualChunks: {
          // Split React and ReactDOM into a separate vendor chunk
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          
          // Split chart.js related libraries
          'vendor-charts': ['chart.js', 'react-chartjs-2', '@kurkle/color'],
          
          // Split fontawesome
          'vendor-icons': [
            '@fortawesome/fontawesome-svg-core',
            '@fortawesome/free-solid-svg-icons',
            '@fortawesome/react-fontawesome'
          ],
          
          // Split other third-party libraries
          'vendor-other': ['axios', 'mermaid', '@react-oauth/google']
        }
      }
    }
  }
});
