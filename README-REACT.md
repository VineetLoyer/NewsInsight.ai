# NewsInsight React UI

A modern, responsive React frontend for NewsInsight - AI-powered news analysis with sentiment and emotion tracking.

## 🎨 Features

### Modern Design
- **Classic newspaper typography** with Playfair Display and Crimson Text fonts
- **Clean, readable interface** with proper contrast and spacing
- **Responsive design** that works on desktop, tablet, and mobile
- **Smooth animations** using Framer Motion
- **Tailwind CSS** for consistent styling

### User Experience
- **Intuitive search** with trending topics and suggestions
- **Real-time filtering** by sentiment (positive, neutral, negative)
- **Interactive article cards** with hover effects and animations
- **Clickable tags** for topic exploration
- **Loading states** and error handling
- **Toast notifications** for user feedback

### Article Interaction
- **Three main actions** per article:
  - 🔗 **Original Article** - Direct link to source
  - 💡 **Explain in Detail** - AI-powered analysis
  - 💬 **Chat with Article** - Interactive Q&A
- **Sentiment analysis** with color-coded indicators
- **Emotion detection** showing NRC emotions with intensity levels
- **Related topics** as clickable tags

### Analytics Dashboard
- **Article statistics** showing total count and sentiment distribution
- **Visual metrics** with icons and color coding
- **Real-time updates** based on current filters

## 🚀 Quick Start

### Prerequisites
- Node.js 16+ 
- npm or yarn
- Python 3.8+ (for backend)

### 1. Setup Backend
```bash
# Install backend dependencies
python setup-backend.py

# Configure environment variables
# Edit .env file with your AWS credentials

# Start backend server
python backend.py
```

### 2. Setup Frontend
```bash
# Install React dependencies
npm install

# Start development server
npm start
```

### 3. Open Application
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 📁 Project Structure

```
newsinsight-react/
├── public/
│   └── index.html              # HTML template
├── src/
│   ├── components/             # React components
│   │   ├── Header.js          # Main header with branding
│   │   ├── SearchSection.js   # Search and filters
│   │   ├── StatsSection.js    # Analytics dashboard
│   │   ├── ArticleGrid.js     # Article layout
│   │   ├── ArticleCard.js     # Individual article
│   │   ├── LoadingSpinner.js  # Loading states
│   │   └── EmptyState.js      # No results state
│   ├── pages/
│   │   └── HomePage.js        # Main page component
│   ├── services/
│   │   └── api.js             # API service layer
│   ├── App.js                 # Main app component
│   ├── index.js               # React entry point
│   └── index.css              # Global styles
├── backend.py                  # FastAPI backend
├── package.json               # Dependencies
├── tailwind.config.js         # Tailwind configuration
└── README-REACT.md            # This file
```

## 🎨 Design System

### Typography
- **Headlines**: Playfair Display (serif, elegant)
- **Body Text**: Crimson Text (serif, readable)
- **UI Elements**: Inter (sans-serif, modern)

### Colors
- **Primary**: Gray-900 (#1a1a1a) for headlines and buttons
- **Text**: Gray-700 (#374151) for body text
- **Background**: Gray-50 (#f9fafb) for page background
- **Cards**: White with subtle shadows

### Sentiment Colors
- **Positive**: Green tones (#ecfdf5, #065f46)
- **Neutral**: Gray tones (#f8fafc, #64748b)  
- **Negative**: Red tones (#fef2f2, #dc2626)

### Components
- **Cards**: Rounded corners, subtle shadows, hover effects
- **Buttons**: Consistent padding, focus states, disabled states
- **Tags**: Pill-shaped, hover animations, clickable
- **Inputs**: Clean borders, focus rings, proper sizing

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the root directory:

```env
# API Configuration
REACT_APP_API_URL=http://localhost:8000
REACT_APP_APP_NAME=NewsInsight
REACT_APP_VERSION=1.0.0

# Development
REACT_APP_DEBUG=true
```

### Tailwind Configuration
The `tailwind.config.js` file includes:
- Custom font families
- Extended color palette
- Animation keyframes
- Component utilities

## 📱 Responsive Design

### Breakpoints
- **Mobile**: < 768px (sm)
- **Tablet**: 768px - 1024px (md)
- **Desktop**: > 1024px (lg)

### Responsive Features
- **Grid layouts** adapt to screen size
- **Typography scales** appropriately
- **Navigation** optimized for touch
- **Cards stack** vertically on mobile

## 🔌 API Integration

### Endpoints Used
- `GET /api/articles/search` - Search articles
- `POST /api/articles/explain` - Get AI analysis
- `POST /api/articles/chat` - Chat with article
- `POST /api/articles/ingest` - Ingest new articles

### Error Handling
- **Network errors** show user-friendly messages
- **API failures** fall back to mock data in development
- **Loading states** provide visual feedback
- **Toast notifications** inform users of actions

## 🧪 Development

### Available Scripts
```bash
npm start          # Start development server
npm run build      # Build for production
npm test           # Run tests
npm run eject      # Eject from Create React App
```

### Development Features
- **Hot reloading** for instant updates
- **Mock data** when backend is unavailable
- **Console logging** for debugging
- **Error boundaries** for graceful failures

### Code Organization
- **Components** are modular and reusable
- **Services** handle API communication
- **Styles** use Tailwind utility classes
- **State management** with React hooks

## 🚀 Deployment

### Production Build
```bash
npm run build
```

### Environment Setup
1. Configure production API URL
2. Set up HTTPS certificates
3. Configure CORS for production domain
4. Optimize images and assets

### Hosting Options
- **Netlify** - Easy deployment with Git integration
- **Vercel** - Optimized for React applications
- **AWS S3 + CloudFront** - Scalable static hosting
- **Docker** - Containerized deployment

## 🔍 Troubleshooting

### Common Issues

#### Backend Connection Failed
- Check if backend is running on port 8000
- Verify CORS configuration
- Check network connectivity

#### Styling Issues
- Ensure Tailwind CSS is properly configured
- Check for conflicting CSS rules
- Verify font loading from Google Fonts

#### Search Not Working
- Check API endpoint configuration
- Verify backend database connection
- Check for proper error handling

### Debug Mode
Enable debug mode in `.env`:
```env
REACT_APP_DEBUG=true
```

This provides:
- Console logging for API calls
- Mock data when backend unavailable
- Additional error information

## 📈 Performance

### Optimizations
- **Code splitting** with React.lazy()
- **Image optimization** with proper formats
- **Caching** for API responses
- **Lazy loading** for components

### Monitoring
- **Bundle size** analysis with webpack-bundle-analyzer
- **Performance metrics** with React DevTools
- **Network requests** monitoring in browser

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

### Code Standards
- **ESLint** for code quality
- **Prettier** for formatting
- **Component documentation**
- **Accessibility compliance**

## 📄 License

This project is part of the NewsInsight application suite.

---

## 🆘 Support

For issues and questions:
1. Check this README
2. Review the troubleshooting section
3. Check the backend logs
4. Verify environment configuration

The React UI provides a modern, intuitive interface for NewsInsight while maintaining full compatibility with the existing backend infrastructure.