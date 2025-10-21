import axios from 'axios';

// Create axios instance with base configuration
const baseURL = process.env.REACT_APP_API_URL || 
  (process.env.NODE_ENV === 'production' 
    ? 'https://newsinsightai-production.up.railway.app'
    : 'http://localhost:8000');

console.log('🔧 API Configuration:', {
  baseURL,
  env: process.env.REACT_APP_API_URL,
  nodeEnv: process.env.NODE_ENV
});

const api = axios.create({
  baseURL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Response Error:', error);
    
    if (error.response) {
      // Server responded with error status
      const message = error.response.data?.detail || error.response.data?.message || 'Server error';
      throw new Error(message);
    } else if (error.request) {
      // Request was made but no response received
      throw new Error('Network error - please check your connection');
    } else {
      // Something else happened
      throw new Error('Request failed');
    }
  }
);

// API functions
export const searchArticles = async (query = '', limit = 6) => {
  try {
    console.log(`🔍 Searching for articles: "${query}" (limit: ${limit})`);
    console.log(`🔗 API URL: ${api.defaults.baseURL}/api/articles/search`);
    
    const response = await api.get('/api/articles/search', {
      params: { query, limit }
    });
    
    console.log(`✅ Backend response:`, response.data);
    console.log(`✅ Found ${response.data.length} real articles from backend`);
    
    // Check if we got real data
    if (response.data && response.data.length > 0) {
      // Mark as real data
      response.data.forEach(article => {
        article._isRealData = true;
      });
    }
    
    return response.data;
  } catch (error) {
    console.error('❌ Search articles error:', error);
    console.error('❌ Error details:', {
      message: error.message,
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data
    });
    
    // Only return mock data if backend is completely unavailable
    if (error.code === 'ECONNREFUSED' || error.message.includes('Network Error')) {
      console.log('🔄 Backend unavailable, using mock data');
      return getMockArticles(query, limit);
    }
    
    // For other errors, still try to return real empty array
    return [];
  }
};

export const explainArticle = async (articleId, content) => {
  try {
    console.log(`🧠 Requesting explanation for article: ${articleId}`);
    const response = await api.post('/api/articles/explain', {
      article_id: articleId,
      content: content
    });
    console.log('✅ Explanation generated successfully');
    return response.data.explanation;
  } catch (error) {
    console.error('❌ Explain article error:', error);
    if (error.message.includes('Network error')) {
      return getMockExplanation();
    }
    throw error;
  }
};

export const chatWithArticle = async (articleId, content, message, history = []) => {
  try {
    console.log(`💬 Chat request for article: ${articleId}, message: "${message}"`);
    const response = await api.post('/api/articles/chat', {
      article_id: articleId,
      content: content,
      message: message,
      history: history
    });
    console.log('✅ Chat response received');
    return response.data.response;
  } catch (error) {
    console.error('❌ Chat with article error:', error);
    if (error.message.includes('Network error')) {
      return getMockChatResponse(message);
    }
    throw error;
  }
};

export const ingestTopic = async (topic) => {
  try {
    const response = await api.post('/api/articles/ingest', {
      topic: topic
    });
    return response.data;
  } catch (error) {
    console.error('Ingest topic error:', error);
    throw error;
  }
};

export const bootstrapArticles = async () => {
  try {
    console.log('🚀 Bootstrapping articles database...');
    const response = await api.post('/api/articles/bootstrap');
    console.log('✅ Bootstrap complete');
    return response.data;
  } catch (error) {
    console.error('❌ Bootstrap error:', error);
    throw error;
  }
};

export const refreshArticles = async () => {
  try {
    console.log('🔄 Refreshing articles cache...');
    const response = await api.post('/api/articles/refresh');
    console.log('✅ Cache refreshed');
    return response.data;
  } catch (error) {
    console.error('❌ Refresh error:', error);
    throw error;
  }
};

export const searchArticlesStream = (query = '', limit = 6, onUpdate) => {
  const baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  const url = `${baseURL}/api/articles/search-stream?query=${encodeURIComponent(query)}&limit=${limit}`;
  
  console.log('🌊 Starting streaming search for:', query);
  
  const eventSource = new EventSource(url);
  
  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      console.log('📡 Stream update:', data.type, data);
      onUpdate(data);
    } catch (error) {
      console.error('❌ Stream parsing error:', error);
    }
  };
  
  eventSource.onerror = (error) => {
    console.error('❌ Stream error:', error);
    eventSource.close();
    onUpdate({ type: 'error', message: 'Connection lost' });
  };
  
  // Return function to close the stream
  return () => {
    console.log('🔌 Closing stream');
    eventSource.close();
  };
};

// Mock data for development/fallback
const getMockArticles = (query, limit) => {
  const mockArticles = [
    {
      id: 'mock-1',
      headline: 'AI Revolution Transforms Global Markets',
      summary: 'Artificial intelligence technologies are reshaping financial markets worldwide, with new algorithms driving unprecedented trading volumes and market efficiency.',
      source: 'Tech Today',
      date: '2024-01-15T10:30:00Z',
      url: 'https://example.com/ai-markets',
      overall_sentiment: 'positive',
      sentiment: 'positive',
      entities: [
        { text: 'Artificial Intelligence', type: 'technology' },
        { text: 'Financial Markets', type: 'business' },
        { text: 'Trading', type: 'finance' }
      ],
      emotions: {
        anticipation: 'high',
        trust: 'medium',
        joy: 'low'
      }
    },
    {
      id: 'mock-2',
      headline: 'Climate Summit Reaches Historic Agreement',
      summary: 'World leaders have reached a groundbreaking consensus on climate action, setting ambitious targets for carbon reduction and renewable energy adoption.',
      source: 'Global News',
      date: '2024-01-14T15:45:00Z',
      url: 'https://example.com/climate-summit',
      overall_sentiment: 'very_positive',
      sentiment: 'positive',
      entities: [
        { text: 'Climate Change', type: 'environment' },
        { text: 'Renewable Energy', type: 'technology' },
        { text: 'Carbon Reduction', type: 'policy' }
      ],
      emotions: {
        anticipation: 'high',
        trust: 'high',
        joy: 'medium'
      }
    },
    {
      id: 'mock-3',
      headline: 'Economic Uncertainty Grips Financial Sector',
      summary: 'Rising inflation and geopolitical tensions are creating significant challenges for financial institutions, leading to increased market volatility.',
      source: 'Financial Times',
      date: '2024-01-13T09:20:00Z',
      url: 'https://example.com/economic-uncertainty',
      overall_sentiment: 'negative',
      sentiment: 'negative',
      entities: [
        { text: 'Inflation', type: 'economics' },
        { text: 'Financial Institutions', type: 'business' },
        { text: 'Market Volatility', type: 'finance' }
      ],
      emotions: {
        fear: 'high',
        sadness: 'medium',
        anger: 'low'
      }
    },
    {
      id: 'mock-4',
      headline: 'Breakthrough in Quantum Computing Research',
      summary: 'Scientists have achieved a major milestone in quantum computing, demonstrating error correction capabilities that bring practical quantum computers closer to reality.',
      source: 'Science Daily',
      date: '2024-01-12T14:10:00Z',
      url: 'https://example.com/quantum-breakthrough',
      overall_sentiment: 'positive',
      sentiment: 'positive',
      entities: [
        { text: 'Quantum Computing', type: 'technology' },
        { text: 'Error Correction', type: 'science' },
        { text: 'Research', type: 'academia' }
      ],
      emotions: {
        anticipation: 'high',
        surprise: 'medium',
        joy: 'high'
      }
    },
    {
      id: 'mock-5',
      headline: 'Healthcare Innovation Addresses Global Challenges',
      summary: 'New medical technologies and treatment approaches are showing promise in addressing some of the world\'s most pressing health challenges.',
      source: 'Medical Journal',
      date: '2024-01-11T11:30:00Z',
      url: 'https://example.com/healthcare-innovation',
      overall_sentiment: 'positive',
      sentiment: 'positive',
      entities: [
        { text: 'Healthcare', type: 'medicine' },
        { text: 'Medical Technology', type: 'technology' },
        { text: 'Treatment', type: 'medicine' }
      ],
      emotions: {
        trust: 'high',
        anticipation: 'medium',
        joy: 'medium'
      }
    },
    {
      id: 'mock-6',
      headline: 'Political Tensions Rise Over Trade Policies',
      summary: 'International trade negotiations have reached a critical juncture as nations struggle to balance economic interests with diplomatic relationships.',
      source: 'Political Review',
      date: '2024-01-10T16:45:00Z',
      url: 'https://example.com/trade-tensions',
      overall_sentiment: 'neutral',
      sentiment: 'neutral',
      entities: [
        { text: 'Trade Policy', type: 'politics' },
        { text: 'International Relations', type: 'politics' },
        { text: 'Economic Interests', type: 'economics' }
      ],
      emotions: {
        anticipation: 'medium',
        fear: 'low',
        anger: 'low'
      }
    }
  ];

  // Filter by query if provided
  let filtered = mockArticles;
  if (query && query.trim()) {
    const searchTerm = query.toLowerCase();
    filtered = mockArticles.filter(article => 
      article.headline.toLowerCase().includes(searchTerm) ||
      article.summary.toLowerCase().includes(searchTerm) ||
      article.entities.some(entity => 
        entity.text.toLowerCase().includes(searchTerm)
      )
    );
  }

  return filtered.slice(0, limit);
};

const getMockExplanation = () => {
  return `**What happened:**
• Major technological breakthrough achieved in the field
• Significant implications for industry and society
• Key stakeholders are responding positively to developments

**Why it matters:**
• This represents a fundamental shift in how we approach the problem
• Economic implications could be substantial over the next decade
• Sets important precedent for future policy and innovation

**What to watch next:**
• Implementation timeline and practical applications
• Regulatory response and policy adaptations`;
};

const getMockChatResponse = (message) => {
  const responses = [
    "Based on the article, this development could have significant implications for the industry. The key factors to consider are the timeline for implementation and the potential regulatory response.",
    "The article suggests that this is part of a larger trend we've been seeing in recent months. The stakeholders mentioned are likely to play crucial roles in how this unfolds.",
    "From what's described in the article, the main challenges appear to be around scalability and adoption. However, the potential benefits seem to outweigh the risks.",
    "The article provides good context for understanding the broader implications. This could be a turning point, but it will depend on how various factors develop over time."
  ];
  
  return responses[Math.floor(Math.random() * responses.length)];
};

// Test function to verify backend connection
export const testBackendConnection = async () => {
  try {
    console.log('🧪 Testing backend connection...');
    const response = await api.get('/api/health');
    console.log('✅ Backend connection successful:', response.data);
    return response.data;
  } catch (error) {
    console.error('❌ Backend connection failed:', error);
    throw error;
  }
};

// Make test function available globally for debugging
if (typeof window !== 'undefined') {
  window.testBackend = testBackendConnection;
}

export default api;