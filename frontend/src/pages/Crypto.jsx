import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

function Crypto() {
  const [text, setText] = useState('');
  const [algorithm, setAlgorithm] = useState('kuznechik');
  const [encrypted, setEncrypted] = useState('');
  const [key, setKey] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleEncrypt = async () => {
    try {
      const response = await api.post('/api/crypto/encrypt', {
        text,
        algorithm,
      });
      setEncrypted(response.data.encrypted);
      setKey(response.data.key || '');
      setError('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Ошибка шифрования');
    }
  };

  const handleDecrypt = async () => {
    try {
      const response = await api.post('/api/crypto/decrypt', {
        encrypted_data: encrypted,
        algorithm,
        key,
      });
      setText(response.data.decrypted);
      setError('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Ошибка расшифрования');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <button
          onClick={() => navigate('/dashboard')}
          className="mb-4 text-blue-600 hover:text-blue-800"
        >
          ← Назад
        </button>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h1 className="text-2xl font-bold mb-6">Шифрование</h1>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Алгоритм
              </label>
              <select
                value={algorithm}
                onChange={(e) => setAlgorithm(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              >
                <option value="kuznechik">Кузнечик</option>
                <option value="rsa">RSA-32768</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Текст
              </label>
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg h-32"
                placeholder="Введите текст для шифрования"
              />
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                {error}
              </div>
            )}

            <div className="flex space-x-4">
              <button
                onClick={handleEncrypt}
                className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700"
              >
                Зашифровать
              </button>
              <button
                onClick={handleDecrypt}
                className="flex-1 bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700"
              >
                Расшифровать
              </button>
            </div>

            {encrypted && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Зашифрованный текст
                </label>
                <textarea
                  value={encrypted}
                  readOnly
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg h-32 bg-gray-50"
                />
              </div>
            )}

            {key && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Ключ
                </label>
                <input
                  type="text"
                  value={key}
                  readOnly
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-50"
                />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Crypto;

