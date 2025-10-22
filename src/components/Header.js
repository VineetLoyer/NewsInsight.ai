import React from 'react';
import { motion } from 'framer-motion';
import { Newspaper, Sun, Moon } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

const Header = () => {
  const { isDark, toggleTheme } = useTheme();

  return (
    <header className="bg-parchment-400 dark:bg-charcoal-800 border-b-4 border-charcoal-700 dark:border-parchment-600 shadow-sm transition-colors duration-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 relative">
        {/* Dark Mode Toggle */}
        <div className="absolute top-4 right-4">
          <button
            onClick={toggleTheme}
            className="p-2 rounded-full bg-parchment-300 dark:bg-charcoal-700 hover:bg-parchment-200 dark:hover:bg-charcoal-600 transition-colors duration-200 shadow-md"
            aria-label="Toggle dark mode"
          >
            {isDark ? (
              <Sun className="w-5 h-5 text-parchment-100" />
            ) : (
              <Moon className="w-5 h-5 text-charcoal-700" />
            )}
          </button>
        </div>

        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center"
        >
          <div className="flex items-center justify-center mb-4">
            <Newspaper className="w-12 h-12 text-charcoal-700 dark:text-parchment-200 mr-3" />
            <h1 className="text-4xl md:text-5xl font-headline font-bold text-charcoal-800 dark:text-parchment-100 tracking-tight">
              NewsInsight
            </h1>
          </div>
          
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.3 }}
            className="space-y-2"
          >
            <p className="text-lg text-charcoal-600 dark:text-parchment-300 font-medium italic">
              Verified News Insights & Deep Analysis
            </p>
            <p className="text-sm text-charcoal-500 dark:text-parchment-400 tracking-wide">
              AI-Powered News Intelligence • Real-time Analysis • Sentiment & Emotion Tracking
            </p>
          </motion.div>
        </motion.div>
      </div>
    </header>
  );
};

export default Header;