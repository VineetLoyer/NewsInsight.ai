import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ExternalLink, 
  MessageCircle, 
  Lightbulb, 
  Calendar, 
  Building2,
  Hash,
  Heart,
  Brain,
  Send,
  X
} from 'lucide-react';
import { explainArticle, chatWithArticle } from '../services/api';
import toast from 'react-hot-toast';

const ArticleCard = ({ article, onTopicClick }) => {
  const [showChat, setShowChat] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [explanation, setExplanation] = useState('');
  const [showExplanation, setShowExplanation] = useState(false);

  const getSentimentClass = (sentiment) => {
    if (!sentiment) return 'sentiment-neutral';
    const s = sentiment.toLowerCase();
    if (s.includes('positive')) return 'sentiment-positive';
    if (s.includes('negative')) return 'sentiment-negative';
    return 'sentiment-neutral';
  };

  const getSentimentLabel = (sentiment) => {
    if (!sentiment) return 'Neutral';
    const s = sentiment.toLowerCase();
    if (s.includes('very_positive')) return 'Very Positive';
    if (s.includes('positive')) return 'Positive';
    if (s.includes('very_negative')) return 'Very Negative';
    if (s.includes('negative')) return 'Negative';
    return 'Neutral';
  };

  const formatDate = (dateString) => {
    if (!dateString || dateString === 'Unknown date') return 'Unknown date';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateString;
    }
  };

  const handleExplain = async () => {
    if (explanation) {
      setShowExplanation(!showExplanation);
      return;
    }

    setLoading(true);
    try {
      const result = await explainArticle(article.id, article.summary || article.headline);
      setExplanation(result);
      setShowExplanation(true);
      toast.success('Analysis generated successfully');
    } catch (error) {
      toast.error('Failed to generate analysis');
      console.error('Explain error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleChatSubmit = async (e) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const userMessage = chatInput.trim();
    setChatInput('');
    
    // Add user message immediately
    const newMessages = [...chatMessages, { type: 'user', content: userMessage }];
    setChatMessages(newMessages);

    setLoading(true);
    try {
      const response = await chatWithArticle(
        article.id,
        article.summary || article.headline,
        userMessage,
        chatMessages
      );
      
      setChatMessages([...newMessages, { type: 'assistant', content: response }]);
    } catch (error) {
      toast.error('Failed to get response');
      console.error('Chat error:', error);
    } finally {
      setLoading(false);
    }
  };

  const getEmotionClass = (level) => {
    switch (level?.toLowerCase()) {
      case 'high': return 'emotion-high';
      case 'medium': return 'emotion-medium';
      case 'low': return 'emotion-low';
      default: return 'emotion-low';
    }
  };

  // Extract entities/tags
  const entities = article.entities || [];
  const displayEntities = entities.slice(0, 6).filter(entity => {
    const text = typeof entity === 'string' ? entity : entity.text;
    return text && text.length > 2;
  });

  // Extract emotions
  const emotions = article.emotions || {};
  const displayEmotions = Object.entries(emotions)
    .filter(([_, level]) => level && level !== 'none')
    .slice(0, 4);

  return (
    <div className="article-card">
      {/* Headline */}
      <h3 className="article-headline">
        {article.headline || 'Untitled Article'}
      </h3>

      {/* Meta Information */}
      <div className="article-meta">
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4" />
          <span>{formatDate(article.date)}</span>
        </div>
        <div className="flex items-center gap-2">
          <Building2 className="w-4 h-4" />
          <span className="font-medium">{article.source || 'Unknown Source'}</span>
        </div>
        <div className={`sentiment-chip ${getSentimentClass(article.overall_sentiment || article.sentiment)}`}>
          {getSentimentLabel(article.overall_sentiment || article.sentiment)}
        </div>
      </div>

      {/* Article Teaser */}
      <div className="article-teaser">
        "{article.summary || article.teaser || 'No summary available'}"
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3 mb-6">
        {article.url && (
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-primary flex items-center gap-2 flex-1 justify-center"
          >
            <ExternalLink className="w-4 h-4" />
            Original
          </a>
        )}
        
        <button
          onClick={handleExplain}
          disabled={loading}
          className="btn-secondary flex items-center gap-2 flex-1 justify-center"
        >
          <Lightbulb className="w-4 h-4" />
          {loading ? 'Loading...' : 'Explain'}
        </button>
        
        <button
          onClick={() => setShowChat(!showChat)}
          className="btn-secondary flex items-center gap-2 flex-1 justify-center"
        >
          <MessageCircle className="w-4 h-4" />
          Chat
        </button>
      </div>

      {/* Tags/Entities */}
      {displayEntities.length > 0 && (
        <div className="mb-4">
          <div className="flex items-center gap-2 mb-3">
            <Hash className="w-4 h-4 text-gray-600" />
            <span className="text-sm font-medium text-gray-700">Related Topics</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {displayEntities.map((entity, index) => {
              const text = typeof entity === 'string' ? entity : entity.text;
              return (
                <button
                  key={index}
                  onClick={() => onTopicClick(text)}
                  className="topic-tag"
                >
                  #{text}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Emotions */}
      {displayEmotions.length > 0 && (
        <div className="mb-4">
          <div className="flex items-center gap-2 mb-3">
            <Heart className="w-4 h-4 text-gray-600" />
            <span className="text-sm font-medium text-gray-700">Emotional Tone</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {displayEmotions.map(([emotion, level]) => (
              <span
                key={emotion}
                className={`emotion-badge ${getEmotionClass(level)}`}
              >
                {emotion} • {level}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Explanation Section */}
      <AnimatePresence>
        {showExplanation && explanation && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-4 p-4 bg-blue-50 rounded-lg border border-blue-200"
          >
            <div className="flex items-center gap-2 mb-3">
              <Brain className="w-4 h-4 text-blue-600" />
              <span className="text-sm font-medium text-blue-800">AI Analysis</span>
            </div>
            <div className="text-sm text-blue-700 whitespace-pre-wrap">
              {explanation}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Chat Section */}
      <AnimatePresence>
        {showChat && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="border-t border-gray-200 pt-4"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <MessageCircle className="w-4 h-4 text-gray-600" />
                <span className="text-sm font-medium text-gray-700">Chat About This Article</span>
              </div>
              <button
                onClick={() => setShowChat(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Chat Messages */}
            {chatMessages.length > 0 && (
              <div className="max-h-48 overflow-y-auto mb-4 space-y-3">
                {chatMessages.map((message, index) => (
                  <div
                    key={index}
                    className={`p-3 rounded-lg ${
                      message.type === 'user'
                        ? 'bg-gray-100 ml-4'
                        : 'bg-blue-50 mr-4'
                    }`}
                  >
                    <div className="text-xs font-medium text-gray-600 mb-1">
                      {message.type === 'user' ? 'You' : 'AI Assistant'}
                    </div>
                    <div className="text-sm text-gray-800">
                      {message.content}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Chat Input */}
            <form onSubmit={handleChatSubmit} className="flex gap-2">
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder="Ask a question about this article..."
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading || !chatInput.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ArticleCard;