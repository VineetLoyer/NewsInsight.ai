import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import Header from '../components/Header';
import SearchSection from '../components/SearchSection';
import StatsSection from '../components/StatsSection';
import ArticleGrid from '../components/ArticleGrid';
import LoadingSpinner from '../components/LoadingSpinner';
import EmptyState from '../components/EmptyState';
import { searchArticles, searchArticlesStream } from '../services/api';
import toast from 'react-hot-toast';
import axios from 'axios';

const HomePage = () => {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [sentimentFilter, setSentimentFilter] = useState('All');
  const [articleLimit, setArticleLimit] = useState(6);
  const [streamStatus, setStreamStatus] = useState('');
  const [useStreaming, setUseStreaming] = useState(false);
  const [stats, setStats] = useState({
    total: 0,
    positive: 0,
    neutral: 0,
    negative: 0
  });
  const [railwayStatus, setRailwayStatus] = useState('testing');
  const [ageFilter, setAgeFilter] = useState(2); // Default: 2 days

  // Test Railway connection on load
  useEffect(() => {
    testRailwayConnection();
    loadArticles();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const testRailwayConnection = async () => {
    try {
      console.log('🧪 Testing Railway connection...');
      const railwayUrl = 'https://newsinsightai-production.up.railway.app';
      
      const response = await axios.get(railwayUrl, { timeout: 10000 });
      console.log('✅ Railway connection successful!', response.data);
      setRailwayStatus('connected');
      toast.success('✅ Railway Backend Connected!');
    } catch (error) {
      console.error('❌ Railway connection failed:', error);
      setRailwayStatus('failed');
      toast.error('❌ Railway Connection Failed');
    }
  };

  // Update stats when articles change
  useEffect(() => {
    calculateStats();
  }, [articles]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadArticles = async (term = '', limit = 6) => {
    // Decide whether to use streaming based on term and expected results
    const shouldStream = term && term.length > 0;
    
    if (shouldStream && useStreaming) {
      loadArticlesStream(term, limit);
    } else {
      loadArticlesRegular(term, limit);
    }
  };

  const loadArticlesRegular = async (term = '', limit = 6) => {
    setLoading(true);
    setStreamStatus('');
    try {
      console.log(`🔄 Loading articles for: "${term}"`);
      const data = await searchArticles(term, limit, ageFilter);
      setArticles(data);
      
      if (term && data.length === 0) {
        toast.error(`No articles found for "${term}"`);
      } else if (term && data.length > 0) {
        toast.success(`Found ${data.length} articles for "${term}"`);
      } else if (!term && data.length > 0) {
        toast.success(`Loaded ${data.length} latest articles`);
      }
      
      // Check if we're getting real data vs mock data
      if (data.length > 0) {
        if (data[0].id && data[0].id.startsWith('mock-')) {
          toast('⚠️ Using demo data - backend not available', {
            duration: 5000,
            style: { background: '#f59e0b', color: 'white' }
          });
        } else if (data[0]._isRealData) {
          toast.success('✅ Loaded real articles from your database!');
        }
      }
    } catch (error) {
      console.error('❌ Error loading articles:', error);
      toast.error('Failed to load articles. Check backend connection.');
      setArticles([]);
    } finally {
      setLoading(false);
    }
  };

  const loadArticlesStream = (term, limit) => {
    setLoading(true);
    setStreamStatus('Connecting...');
    setArticles([]); // Clear existing articles
    
    const closeStream = searchArticlesStream(term, limit, (update) => {
      console.log('📡 Stream update:', update);
      
      switch (update.type) {
        case 'existing':
          setArticles(update.articles);
          setStreamStatus(`Found ${update.count} existing articles`);
          if (update.count >= limit) {
            setLoading(false);
            setStreamStatus('');
            toast.success(`✅ Found ${update.count} articles instantly!`);
          }
          break;
          
        case 'status':
          setStreamStatus(update.message);
          break;
          
        case 'new_article':
          setArticles(prev => [...prev, update.article]);
          setStreamStatus(`Processing article ${update.progress}/${update.total}...`);
          break;
          
        case 'complete':
          setLoading(false);
          setStreamStatus('');
          toast.success(update.message);
          break;
          
        case 'error':
          setLoading(false);
          setStreamStatus('');
          toast.error(update.message);
          break;
          
        default:
          console.log('Unknown stream update type:', update.type);
          break;
      }
    });
    
    // Store cleanup function
    window.currentStream = closeStream;
  };

  const calculateStats = () => {
    const filtered = filterArticlesBySentiment(articles);
    const sentimentCounts = filtered.reduce(
      (acc, article) => {
        const sentiment = getSentimentBucket(article.overall_sentiment || article.sentiment);
        acc[sentiment] = (acc[sentiment] || 0) + 1;
        return acc;
      },
      { positive: 0, neutral: 0, negative: 0 }
    );

    setStats({
      total: filtered.length,
      ...sentimentCounts
    });
  };

  const getSentimentBucket = (sentiment) => {
    if (!sentiment) return 'neutral';
    const s = sentiment.toLowerCase();
    if (s.includes('positive')) return 'positive';
    if (s.includes('negative')) return 'negative';
    return 'neutral';
  };

  const filterArticlesBySentiment = (articleList) => {
    if (sentimentFilter === 'All') return articleList;
    return articleList.filter(article => {
      const sentiment = getSentimentBucket(article.overall_sentiment || article.sentiment);
      return sentiment === sentimentFilter.toLowerCase();
    });
  };

  const handleSearch = async (term) => {
    setSearchTerm(term);
    await loadArticles(term, articleLimit);
    
    // If no articles were found, wait a moment and try again
    // (in case new articles were just ingested)
    if (articles.length === 0 && term) {
      setTimeout(async () => {
        console.log('🔄 Retrying search after potential ingestion...');
        await loadArticles(term, articleLimit);
      }, 2000);
    }
  };

  const handleTopicClick = (topic) => {
    setSearchTerm(topic);
    loadArticles(topic, articleLimit);
  };

  const handleSentimentFilterChange = (filter) => {
    setSentimentFilter(filter);
  };

  const handleArticleLimitChange = (limit) => {
    setArticleLimit(limit);
    if (searchTerm) {
      loadArticles(searchTerm, limit);
    } else {
      loadArticles('', limit);
    }
  };

  const filteredArticles = filterArticlesBySentiment(articles);

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      {/* Railway Connection Status */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2">
          <div className="flex items-center justify-center">
            {railwayStatus === 'testing' && (
              <div className="flex items-center text-yellow-600">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-yellow-600 mr-2"></div>
                <span className="text-sm">Testing Railway connection...</span>
              </div>
            )}
            {railwayStatus === 'connected' && (
              <div className="flex items-center text-green-600">
                <div className="h-4 w-4 bg-green-500 rounded-full mr-2"></div>
                <span className="text-sm font-medium">✅ Railway Backend Connected</span>
              </div>
            )}
            {railwayStatus === 'failed' && (
              <div className="flex items-center text-red-600">
                <div className="h-4 w-4 bg-red-500 rounded-full mr-2"></div>
                <span className="text-sm font-medium">❌ Railway Connection Failed</span>
              </div>
            )}
          </div>
        </div>
      </div>
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <SearchSection
            onSearch={handleSearch}
            onTopicClick={handleTopicClick}
            searchTerm={searchTerm}
            sentimentFilter={sentimentFilter}
            onSentimentFilterChange={handleSentimentFilterChange}
            articleLimit={articleLimit}
            onArticleLimitChange={handleArticleLimitChange}
            useStreaming={useStreaming}
            onStreamingToggle={setUseStreaming}
            streamStatus={streamStatus}
            ageFilter={ageFilter}
            onAgeFilterChange={setAgeFilter}
          />
        </motion.div>

        {loading ? (
          <LoadingSpinner />
        ) : (
          <>
            {filteredArticles.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.2 }}
              >
                <StatsSection stats={stats} searchTerm={searchTerm} />
              </motion.div>
            )}

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
            >
              {filteredArticles.length > 0 ? (
                <ArticleGrid 
                  articles={filteredArticles} 
                  onTopicClick={handleTopicClick}
                />
              ) : (
                <EmptyState 
                  searchTerm={searchTerm}
                  onTopicClick={handleTopicClick}
                />
              )}
            </motion.div>
          </>
        )}
      </main>
    </div>
  );
};

export default HomePage;