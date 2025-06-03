import { useState } from 'react';
import './App.css';

function App() {
  // State variables for user input, submitted query, answer, context (sources), and loading state
  const [query, setQuery] = useState('');
  const [submittedQuery, setSubmittedQuery] = useState('');
  const [answer, setAnswer] = useState('');
  const [context, setContext] = useState([]);
  const [loading, setLoading] = useState(false);

  // Function to handle the "Ask" button click
  const handleAsk = async () => {
    setLoading(true);         // Set loading state to true while waiting for response
    setAnswer('');            // Clear previous answer
    setContext([]);           // Clear previous context/sources
    setSubmittedQuery(query); // Store the current query as the submitted query

    try {
      // Send POST request to backend with the user's query and request up to 5 sources
      const response = await fetch('http://localhost:8000/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query, top_k: 5 }),
      });

      // Parse the JSON response and update answer and context state
      const data = await response.json();
      setAnswer(data.answer);
      setContext(data.context);
    } catch (err) {
      // If there's an error, show an error message
      setAnswer('Something went wrong while fetching the answer.');
    } finally {
      // Always unset loading state when done
      setLoading(false);
    }
  };

  // Main render
  return (
    <div className="page-outer">
      {/* Header with main title */}
      <header className="header-container">
        <h1 className="main-title">
          Visa Developer AI Helper Chat
        </h1>
      </header>
      {/* Centered chat UI container */}
      <div className="center-outer">
        <div className="chat-container">
          {/* Input row: textarea for query and Ask button */}
          <div className="input-row">
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)} // Update query state on input
              placeholder="Ask a question about Visa's codebase..."
              rows={4}
              className="chat-input"
            />
            <button onClick={handleAsk} disabled={loading} className="chat-button">
              {loading ? 'Asking...' : 'Ask'}
            </button>
          </div>

          {/* Display the answer and sources if an answer is present */}
          {answer && (
            <div className="chat-response">
              {/* Show the user's submitted query */}
              <div className="chat-bubble user">You: {submittedQuery}</div>
              {/* Show the AI's answer and, if available, the sources */}
              <div className="chat-bubble bot">
                AI Helper: {answer}
                {(() => {
                  // Filter out invalid sources (empty or "#")
                  const validSources = context.filter(doc => doc.source && doc.source !== '#');
                  // Only display the sources section if there are valid sources
                  return (
                    validSources.length > 0 && (
                      <div style={{ marginTop: '1rem' }}>
                        <strong>Sources:</strong>
                        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                          {/* Render each valid source as a numbered link */}
                          {validSources.map((doc, idx) => (
                            <li key={idx} style={{ marginBottom: '0.25rem' }}>
                              <a
                                href={doc.source}
                                target="_blank"
                                rel="noopener noreferrer"
                                style={{ color: '#90cdf4', textDecoration: 'underline' }}
                              >
                                Source {idx + 1}
                              </a>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )
                  );
                })()}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;