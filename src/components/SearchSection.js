import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Search, TrendingUp, Filter, BarChart3 } from 'lucide-react';

const SearchSection = ({
  onSearch,
  onTopicClick,
  searchTerm,
  sentimentFilter,
  onSentimentFilterChange,
  articleLimit,
  onArticleLimitChange,
  useStreaming,
  onStreamingToggle,
  streamStatus
}) => {
  const [inputValue, setInputValue] = useState(searchTerm);

  const trendingTopics = [
    'Politics', 'Technology', 'Business', 'Markets',
    'Science', 'World', 'Climate', 'AI',
    'Healthcare', 'Economy', 'Sports', 'Entertainment'
  ];

  const sentimentOptions = ['All', 'Positive', 'Neutral', 'Negative'];
  const limitOptions = [3, 6, 9, 12, 15];

  const handleSubmit = (e) => {
    e.preventDefault();
    onSearch(inputValue);
  };

  const handleTopicClick = (topic) => {
    setInputValue(topic);
    onTopicClick(topic);
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8 mb-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        {/* Search Header */}
        <div className="flex items-center mb-6">
          <Search className="w-6 h-6 text-gray-600 mr-3" />
          <h2 className="text-2xl font-headline font-bold text-gray-900">
            Search News & Analysis
          </h2>
        </div>

        {/* Search Form */}
        <form onSubmit={handleSubmit} className="mb-8">
          <div className="flex gap-4">
            <div className="flex-1">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Search for topics like 'AI regulation', 'climate change', 'market trends'..."
                className="search-input"
              />
            </div>
            <button
              type="submit"
              className="btn-primary px-8 py-3 text-lg flex items-center gap-2"
            >
              <Search className="w-5 h-5" />
              Search
            </button>
          </div>
        </form>

        {/* Controls Row */}
        <div className="flex flex-wrap gap-6 mb-8 p-4 bg-gray-50 rounded-xl">
          {/* Sentiment Filter */}
          <div className="flex items-center gap-3">
            <Filter className="w-5 h-5 text-gray-600" />
            <label className="text-sm font-medium text-gray-700">Sentiment:</label>
            <select
              value={sentimentFilter}
              onChange={(e) => onSentimentFilterChange(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-gray-500 focus:border-transparent"
            >
              {sentimentOptions.map(option => (
                <option key={option} value={option}>{option}</option>
              ))}
            </select>
          </div>

          {/* Article Limit */}
          <div className="flex items-center gap-3">
            <BarChart3 className="w-5 h-5 text-gray-600" />
            <label className="text-sm font-medium text-gray-700">Show:</label>
            <select
              value={articleLimit}
              onChange={(e) => onArticleLimitChange(Number(e.target.value))}
              className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-gray-500 focus:border-transparent"
            >
              {limitOptions.map(limit => (
                <option key={limit} value={limit}>{limit} articles</option>
              ))}
            </select>
          </div>

          {/* Streaming Toggle */}
          <div className="flex items-center gap-3">
            <label className="text-sm font-medium text-gray-700">Real-time mode:</label>
            <button
              onClick={() => onStreamingToggle(!useStreaming)}
              className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                useStreaming 
                  ? 'bg-blue-100 text-blue-800 border border-blue-200' 
                  : 'bg-gray-100 text-gray-600 border border-gray-200'
              }`}
            >
              {useStreaming ? '🌊 Streaming' : '⚡ Fast'}
            </button>
          </div>
        </div>

        {/* Stream Status */}
        {streamStatus && (
          <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
              <span className="text-blue-800 text-sm font-medium">{streamStatus}</span>
            </div>
          </div>
        )}

        {/* Trending Topics */}
        <div>
          <div className="flex items-center mb-4">
            <TrendingUp className="w-5 h-5 text-gray-600 mr-2" />
            <h3 className="text-lg font-headline font-semibold text-gray-900">
              Trending Topics
            </h3>
          </div>
          <p className="text-gray-600 mb-4">
            Click on any topic below to explore related articles:
          </p>
          
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
            {trendingTopics.map((topic, index) => (
              <motion.button
                key={topic}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
                onClick={() => handleTopicClick(topic)}
                className="topic-tag text-center py-2"
              >
                {topic}
              </motion.button>
            ))}
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default SearchSection;