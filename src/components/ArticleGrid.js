import React from 'react';
import { motion } from 'framer-motion';
import ArticleCard from './ArticleCard';

const ArticleGrid = ({ articles, onTopicClick }) => {
  return (
    <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
      {articles.map((article, index) => (
        <motion.div
          key={article.id || index}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: index * 0.1 }}
        >
          <ArticleCard 
            article={article} 
            onTopicClick={onTopicClick}
          />
        </motion.div>
      ))}
    </div>
  );
};

export default ArticleGrid;