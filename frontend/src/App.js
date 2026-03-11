import React, { useState } from 'react';
import './App.css';

function App() {
  const [file, setFile] = useState(null);
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && !['text/csv', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'].includes(selectedFile.type)) {
      setError('Please select a CSV or XLSX file');
      setFile(null);
      return;
    }
    setFile(selectedFile);
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file || !email) {
      setError('Please select a file and enter an email address');
      return;
    }

    setLoading(true);
    setError('');
    setMessage('');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('email', email);

    try {
      const response = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        setMessage('Summary generated and sent successfully!');
        setFile(null);
        setEmail('');
        // Reset file input
        document.getElementById('file-input').value = '';
      } else {
        setError(data.detail || 'An error occurred');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Sales Insight Automator</h1>
        <p>Upload your sales data and get AI-generated insights delivered to your inbox</p>
      </header>

      <main className="App-main">
        <form onSubmit={handleSubmit} className="upload-form">
          <div className="form-group">
            <label htmlFor="file-input">Select CSV or XLSX file:</label>
            <input
              id="file-input"
              type="file"
              accept=".csv,.xlsx"
              onChange={handleFileChange}
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="email">Email address:</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your.email@example.com"
              disabled={loading}
              required
            />
          </div>

          <button type="submit" disabled={loading || !file || !email}>
            {loading ? 'Processing...' : 'Generate & Send Summary'}
          </button>
        </form>

        {loading && (
          <div className="loading">
            <div className="spinner"></div>
            <p>Analyzing your data and generating insights...</p>
          </div>
        )}

        {message && <div className="success">{message}</div>}
        {error && <div className="error">{error}</div>}
      </main>
    </div>
  );
}

export default App;