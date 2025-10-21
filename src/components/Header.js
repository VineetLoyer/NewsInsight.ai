import React from 'react';
import { motion } from 'framer-motion';
import { Newspaper } from 'lucide-react';

const Header = () => {
  return (
    <header className="bg-white border-b-4 border-gray-900 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center"
        >
          <div className="flex items-center justify-center mb-4">
            <Newspaper className="w-16 h-16 text-gray-900 mr-4" />
            <h1 className="newspaper-title">
              NewsInsight
            </h1>
          </div>
          
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.3 }}
            className="space-y-2"
          >
            <p className="text-xl text-gray-600 font-medium italic">
              Verified News Insights & Deep Analysis
            </p>
            <p className="text-sm text-gray-500 tracking-wide">
              AI-Powered News Intelligence • Real-time Analysis • Sentiment & Emotion Tracking
            </p>
          </motion.div>
        </motion.div>
      </div>
    </header>
  );
};

export default Header;