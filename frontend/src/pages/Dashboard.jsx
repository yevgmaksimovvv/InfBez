import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.jsx';

function Dashboard() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen">
      <nav className="bg-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-800">CyberSecurity</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-gray-700">Пользователь: {user?.username}</span>
              <span className="text-gray-500">({user?.role})</span>
              <button
                onClick={logout}
                className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
              >
                Выйти
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Link
            to="/crypto"
            className="bg-white rounded-lg shadow-md p-6 hover:shadow-xl transition cursor-pointer"
          >
            <h2 className="text-xl font-semibold text-gray-800 mb-2">
              Шифрование
            </h2>
            <p className="text-gray-600">
              Шифруйте и расшифровывайте текст с помощью RSA-32768 или Кузнечик
            </p>
          </Link>

          <Link
            to="/documents"
            className="bg-white rounded-lg shadow-md p-6 hover:shadow-xl transition cursor-pointer"
          >
            <h2 className="text-xl font-semibold text-gray-800 mb-2">
              Документы
            </h2>
            <p className="text-gray-600">
              Просматривайте и экспортируйте документы в PDF с ЭЦП
            </p>
          </Link>

          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-2">
              Хеширование
            </h2>
            <p className="text-gray-600">
              Хешируйте данные с помощью Стрибог-512
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;

