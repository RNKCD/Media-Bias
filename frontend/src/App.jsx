
import { useState } from "react";
import "./App.css";

function App() {
  const [event, setEvent] = useState("");
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searched, setSearched] = useState(false);

  async function handleAnalyze(e) {
    e.preventDefault();

    setLoading(true);
    setError("");
    setArticles([]);
    setSearched(false);

    try {
      const response = await fetch(
        "http://localhost:8000/api/analyze",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ event: event.trim() }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Unable to retrieve articles."
        );
      }

      setArticles(data.articles || []);
      setSearched(true);
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <header className="navbar">
        <h2>MediaLens</h2>
        <span>AI-Powered News Analysis</span>
      </header>

      <main className="main">
        <div className="hero">
          <h1>Understand the News Beyond the Headlines</h1>
          <p>
            Compare how different news outlets report the
            same political event using AI and data analysis.
          </p>
        </div>

        <form className="search-box" onSubmit={handleAnalyze}>
          <input
            type="text"
            placeholder="Enter a political event..."
            value={event}
            onChange={(e) => setEvent(e.target.value)}
            required
          />

          <button type="submit" disabled={loading}>
            {loading ? "Searching..." : "Find News Coverage"}
          </button>
        </form>

        {error && (
          <p className="error-message">{error}</p>
        )}

        {articles.length > 0 && (
          <section className="results">
            <h2>News Coverage Results</h2>
            <p>{articles.length} articles found</p>

            <div className="article-grid">
              {articles.map((article, index) => (
                <div
                  className="article-card"
                  key={article.url || index}
                >
                  <span className="outlet">
                    {article.outlet}
                  </span>

                  <h3>{article.title}</h3>

                  <p>
                    {article.description ||
                      "No description available."}
                  </p>

                  <small>
                    {article.published_at
                      ? new Date(
                          article.published_at
                        ).toLocaleDateString()
                      : "Date unavailable"}
                  </small>

                  {article.url && (
                    <a
                      href={article.url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      Read Original Article
                    </a>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}

        {searched && articles.length === 0 && (
          <p className="search-hint">
            No matching articles were returned.
            Try a different event or search term.
          </p>
        )}

        <section className="features">
          <div className="feature-card">
            <h3>Sentiment Analysis</h3>
            <p>
              Compare emotional tone across news outlets.
            </p>
          </div>

          <div className="feature-card">
            <h3>Political Framing</h3>
            <p>
              Discover differences in reporting perspectives.
            </p>
          </div>

          <div className="feature-card">
            <h3>Coverage Comparison</h3>
            <p>
              Identify differences in what outlets emphasize.
            </p>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
