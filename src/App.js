import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { ThemeProvider } from './contexts/ThemeContext';
import HomePage from './pages/HomePage';
import './App.css';

function App() {
  return (
    <ThemeProvider>
      <Router>
        <div className="App min-h-screen bg-parchment-200 dark:bg-charcoal-900 transition-colors duration-300">
          <Toaster 
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: 'var(--toast-bg)',
                color: 'var(--toast-color)',
              },
            }}
          />
          <Routes>
            <Route path="/" element={<HomePage />} />
          </Routes>
        </div>
      </Router>
    </ThemeProvider>
  );
}

export default App;