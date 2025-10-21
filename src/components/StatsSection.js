import React from 'react';
import { motion } from 'framer-motion';
import { BarChart3, TrendingUp, Smile, Meh, Frown } from 'lucide-react';

const StatsSection = ({ stats, searchTerm }) => {
  const statItems = [
    {
      label: 'Total Articles',
      value: stats.total,
      icon: BarChart3,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      label: 'Positive',
      value: stats.positive,
      icon: Smile,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
    },
    {
      label: 'Neutral',
      value: stats.neutral,
      icon: Meh,
      color: 'text-gray-600',
      bgColor: 'bg-gray-50',
    },
    {
      label: 'Negative',
      value: stats.negative,
      icon: Frown,
      color: 'text-red-600',
      bgColor: 'bg-red-50',
    },
  ];

  return (
    <div className="mb-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="mb-6"
      >
        <h2 className="text-3xl font-headline font-bold text-gray-900 mb-2">
          {searchTerm ? (
            <>News Analysis for "{searchTerm}"</>
          ) : (
            <>Latest Verified News Insights</>
          )}
        </h2>
        <p className="text-gray-600 text-lg">
          {searchTerm ? (
            <>Found insights related to your search</>
          ) : (
            <>Real-time analysis of breaking news and trending topics</>
          )}
        </p>
      </motion.div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {statItems.map((item, index) => {
          const Icon = item.icon;
          return (
            <motion.div
              key={item.label}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3, delay: index * 0.1 }}
              className={`${item.bgColor} rounded-xl p-4 border border-gray-200`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 mb-1">
                    {item.label}
                  </p>
                  <p className={`text-2xl font-bold ${item.color}`}>
                    {item.value}
                  </p>
                </div>
                <Icon className={`w-8 h-8 ${item.color}`} />
              </div>
            </motion.div>
          );
        })}
      </div>

      <div className="border-b border-gray-200"></div>
    </div>
  );
};

export default StatsSection;