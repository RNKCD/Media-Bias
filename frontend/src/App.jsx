
import { useState } from "react";
import "./App.css";

function App() {
  const [event, setEvent] = useState("");
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searched, setSearched] = useState(false);
  const [nlpResults, setNlpResults] = useState([]);
  const [sentimentResults, setSentimentResults] = useState([]);
  const [sentimentLoading, setSentimentLoading] = useState(false);
  const [selectedEventId, setSelectedEventId] = useState(null);
  const [emotionResults, setEmotionResults] = useState([]);
const [emotionLoading, setEmotionLoading] = useState(false);

  async function handleAnalyze(e) {
    e.preventDefault();

    setLoading(true);
    setError("");
    setArticles([]);
    setSearched(false);
    setSelectedEventId(null);
    setNlpResults([]);
    setSentimentResults([]);
    setEmotionResults([]);

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
      console.log("Analyze API response:", data);

      setSelectedEventId(data.event_id ?? null);
      setNlpResults([]);
      setSentimentResults([]);

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


  
async function loadNlpResults() {
  if (selectedEventId == null) {
    setError("Please search for an event first.");
    return;
  }

  try {
    const response = await fetch(
      `http://localhost:8000/api/nlp/results?event_id=${selectedEventId}`
    );

    if (!response.ok) {
      throw new Error("Unable to load NLP results");
    }

    const data = await response.json();
    setNlpResults(data.results || []);
  } catch (error) {
    console.error(error);
    setError(error.message);
  }
}

  


async function loadSentimentResults() {
  if (selectedEventId == null) {
    setError("Please search for an event first.");
    return;
  }

  setSentimentLoading(true);

  try {
    const response = await fetch(
      `http://localhost:8000/api/sentiment/results?event_id=${selectedEventId}`
    );

    if (!response.ok) {
      throw new Error("Failed to load sentiment results");
    }

    const data = await response.json();
    setSentimentResults(data.results || []);
  } catch (error) {
    console.error(error);
    setError(error.message);
  } finally {
    setSentimentLoading(false);
  }
}
 

async function loadEmotionResults() {
  if (selectedEventId == null) {
    setError("Please search for an event first.");
    return;
  }

  setEmotionLoading(true);

  try {
    const response = await fetch(
      `http://localhost:8000/api/emotion/results?event_id=${selectedEventId}`
    );

    if (!response.ok) {
      throw new Error("Failed to load emotion results");
    }

    const data = await response.json();
    setEmotionResults(data.results || []);
  } catch (error) {
    console.error("Emotion API error:", error);
    setError(error.message);
  } finally {
    setEmotionLoading(false);
  }
}



const outletComparison = Object.values(
  sentimentResults.reduce((groups, article) => {
    const outlet = article.outlet;

    if (!groups[outlet]) {
      groups[outlet] = {
        outlet,
        total: 0,
        sentimentSum: 0,
        scored: 0
      };
    }

    groups[outlet].total += 1;

    if (typeof article.sentiment_score === "number") {
      groups[outlet].sentimentSum += article.sentiment_score;
      groups[outlet].scored += 1;
    }

    return groups;
  }, {})
).map((group) => ({
  outlet: group.outlet,
  total: group.total,
  averageSentiment: group.scored
    ? group.sentimentSum / group.scored
    : null
}));


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

<section className="nlp-section">
  <h2>AI Text Analysis</h2>
  <p>Explore extracted keywords and named entities.</p>

  <button type="button" onClick={loadNlpResults}>
    Load NLP Results
  </button>



  <div className="nlp-grid">
    {nlpResults.map((result) => (
      <div className="nlp-card" key={result.article_id}>
        <span className="outlet">{result.outlet}</span>
        <h3>{result.title}</h3>

        <p>Word Count: {result.word_count}</p>

        <h4>Top Keywords</h4>
        <div className="tag-list">
          {(result.keywords || []).slice(0, 8).map((keyword) => (
            <span className="tag" key={keyword.word}>
              {keyword.word} ({keyword.frequency})
            </span>
          ))}
        </div>

        <h4>Named Entities</h4>
        <div className="tag-list">
          {(result.entities || []).slice(0, 8).map((entity, index) => (
            <span className="tag" key={index}>
              {entity.text} ({entity.label})
            </span>
          ))}
        </div>
      </div>
    ))}
  </div>
</section>


<section className="sentiment-section">
  <div className="sentiment-header">
    <div>
      <h2>Sentiment Analysis</h2>
      <p>
        Compare the emotional tone of news headlines
        and available article text.
      </p>
    </div>

    <button
      type="button"
      onClick={loadSentimentResults}
      disabled={sentimentLoading}
    >
      {sentimentLoading ? "Loading..." : "Load Sentiment Results"}
    </button>
  </div>

  {sentimentResults.length > 0 && (
    <div className="sentiment-table-wrapper">
      <table className="sentiment-table">
        <thead>
          <tr>
            <th>News Outlet</th>
            <th>Article</th>
            <th>Sentiment</th>
            <th>Overall Score</th>
            <th>Headline</th>
            <th>Article Text</th>
          </tr>
        </thead>

        <tbody>
          {sentimentResults.map((article) => (
            <tr key={article.article_id}>
              <td>{article.outlet}</td>

              <td className="article-title">
                {article.title}
              </td>

              <td>
                <span
                  className={`sentiment-badge ${
                    article.sentiment_label
                  }`}
                >
                  {article.sentiment_label}
                </span>
              </td>

              <td>
                {article.sentiment_score?.toFixed(3) ?? "N/A"}
              </td>

              <td>
                {article.headline_sentiment?.toFixed(3) ?? "N/A"}
              </td>

              <td>
                {article.body_sentiment?.toFixed(3) ?? "N/A"}
                <small className="text-source">
                  {article.text_source === "description"
                    ? "Description only"
                    : article.text_source === "full_text"
                    ? "Full text"
                    : "Unavailable"}
                </small>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )}

  {!sentimentLoading && sentimentResults.length === 0 && (
    <p className="sentiment-empty">
      Click "Load Sentiment Results" to view your analysis.
    </p>
  )}
</section>


<section className="emotion-section">
  <div className="emotion-header">
    <div>
      <h2>Emotion Analysis</h2>
      <p>
        Explore model-predicted emotions in news coverage
        for the selected event.
      </p>
    </div>

    <button
      type="button"
      onClick={loadEmotionResults}
      disabled={emotionLoading}
    >
      {emotionLoading ? "Loading..." : "Load Emotion Results"}
    </button>
  </div>

  {emotionResults.length > 0 && (
    <div className="emotion-grid">
      {emotionResults.map((article) => {
        const scores = Object.entries(
          article.emotion_scores || {}
        ).sort((a, b) => b[1] - a[1]);

        return (
          <div className="emotion-card" key={article.article_id}>
            <span className="emotion-outlet">
              {article.outlet}
            </span>

            <h3>{article.title}</h3>

            <p>
              Dominant emotion:
              <strong className="emotion-label">
                {article.emotion_label}
              </strong>
            </p>

            <div className="emotion-bars">
              {scores.map(([emotion, score]) => (
                <div className="emotion-bar-row" key={emotion}>
                  <span>{emotion}</span>

                  <div className="emotion-bar-track">
                    <div
                      className="emotion-bar-fill"
                      style={{
                        width: `${Math.max(
                          0,
                          Math.min(100, score * 100)
                        )}%`
                      }}
                    />
                  </div>

                  <span>{(score * 100).toFixed(1)}%</span>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  )}
</section>


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
