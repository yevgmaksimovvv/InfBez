import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

function Documents() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    // Загрузка документов
    setLoading(false);
  }, []);

  const handleExportPDF = async (docId) => {
    try {
      const response = await api.get(`/api/documents/${docId}/pdf`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `document_${docId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Ошибка экспорта PDF:', err);
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
          <h1 className="text-2xl font-bold mb-6">Документы</h1>

          {loading ? (
            <div>Загрузка...</div>
          ) : documents.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              Нет документов
            </div>
          ) : (
            <div className="space-y-4">
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition"
                >
                  <h3 className="font-semibold mb-2">Документ #{doc.id}</h3>
                  <p className="text-gray-600 mb-4">{doc.original_text.substring(0, 100)}...</p>
                  <button
                    onClick={() => handleExportPDF(doc.id)}
                    className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
                  >
                    Экспорт в PDF
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Documents;

