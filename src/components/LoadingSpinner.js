import React from 'react';
import { motion } from 'framer-motion';
import { Loader2 } from 'lucide-react';

const LoadingSpinner = () => {
  return (
    <div className="flex flex-col items-center justify-center py-16">
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="text-center"
      >
        <Loader2 className="w-12 h-12 text-gray-600 animate-spin mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Searching for articles...
        </h3>
        <p className="text-gray-600">
          Please wait while we fetch the latest news insights
        </p>
      </motion.div>
    </div>
  );
};

export default LoadingSpinner;