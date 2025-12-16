import React from 'react';

/**
 * Переиспользуемый компонент карточки
 */
const Card = ({ children, title, className = '' }) => {
  return (
    <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
      {title && (
        <h2 className="text-2xl font-bold mb-4 text-gray-800">{title}</h2>
      )}
      {children}
    </div>
  );
};

export default Card;
