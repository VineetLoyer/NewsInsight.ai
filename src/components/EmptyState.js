import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Search, TrendingUp, FileText, Download } from 'lucide-react';
import { bootstrapArticles } from '../services/api';
import toast from 'react-hot-toast';

const EmptyState = ({ searchTerm, onTopicClick }) => {
  const [bootstrapping, setBootstrapping] = useState(false);

  const handleBootstrap = async () => {
    setBootstrapping(true);
    try {
      const result = await bootstrapArticles();
      toast.success(`✅ ${result.message}`);
      // Reload the page to show new articles
      window.location.reload();
    } catch (error) {
      toast.error('❌ Failed to bootstrap articles. Check your API keys.');
    } finally {
      setBootstrapping(false);
    }
  };
  const suggestions = [
    'Technology', 'Politics', 'Business', 'Science', 
    'Climate', 'AI', 'Healthcare', 'Economy'
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="text-center py-16"
    >
      <div className="max-w-md mx-auto">
        <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <FileText className="w-12 h-12 text-gray-400" />
        </div>
        
        <h3 className="text-2xl font-headline font-bold text-gray-900 mb-4">
          No articles found
        </h3>
        
        <p className="text-gray-600 text-lg mb-8">
          {searchTerm ? (
            <>We couldn't find any articles matching "<strong>{searchTerm}</strong>".</>
          ) : (
            <>No articles are currently available.</>
          )}
        </p>

        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          {!searchTerm ? (
            // No articles at all - show bootstrap option
            <>
              <h4 className="font-semibold text-gray-900 mb-4 flex items-center justify-center gap-2">
                <Download className="w-5 h-5" />
                Get Started with NewsInsight
              </h4>
              
              <p className="text-gray-600 mb-6 text-center">
                It looks like your database is empty. Let's fetch some articles to get started!
              </p>
              
              <button
                onClick={handleBootstrap}
                disabled={bootstrapping}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-6 py-3 rounded-lg font-medium mb-4 flex items-center justify-center gap-2"
              >
                <Download className="w-5 h-5" />
                {bootstrapping ? 'Fetching Articles...' : 'Fetch Sample Articles'}
              </button>
              
              <p className="text-sm text-gray-500 text-center mb-4">
                This will fetch articles from Technology, Politics, Business, Science, and World news
              </p>
            </>
          ) : (
            // Search term but no results
            <>
              <h4 className="font-semibold text-gray-900 mb-4 flex items-center justify-center gap-2">
                <Search className="w-5 h-5" />
                Try these suggestions:
              </h4>
              
              <ul className="text-left text-gray-600 space-y-2 mb-6">
                <li>• Use different or broader keywords</li>
                <li>• Check the trending topics below</li>
                <li>• Clear your search to see latest articles</li>
                <li>• Try searching for general topics</li>
              </ul>
            </>
          )}

          <div className="border-t border-gray-200 pt-4">
            <div className="flex items-center justify-center gap-2 mb-3">
              <TrendingUp className="w-4 h-4 text-gray-600" />
              <span className="text-sm font-medium text-gray-700">Quick Topics</span>
            </div>
            <div className="flex flex-wrap gap-2 justify-center">
              {suggestions.map((topic) => (
                <button
                  key={topic}
                  onClick={() => onTopicClick(topic)}
                  className="px-3 py-1 bg-gray-100 hover:bg-gray-900 hover:text-white text-gray-700 rounded-full text-sm transition-colors duration-200"
                >
                  {topic}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default EmptyState;