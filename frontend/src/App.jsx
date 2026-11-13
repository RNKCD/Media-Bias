
import { useEffect, useState } from "react";
import "./App.css";

const FALLBACK_OUTLETS = [
  "CNN", "Reuters", "Fox News", "BBC News", "Associated Press",
  "The Guardian", "NBC News", "ABC News", "Al Jazeera", "The Hill",
];
const FALLBACK_DEFAULTS = ["CNN", "Reuters", "Fox News"];

function App() {
  const [event, setEvent] = useState("");
  const [availableOutlets, setAvailableOutlets] = useState(FALLBACK_OUTLETS);
  const [maxOutlets, setMaxOutlets] = useState(15);
  const [selectedOutlets, setSelectedOutlets] = useState(FALLBACK_DEFAULTS);
  const [customOutlets, setCustomOutlets] = useState([]);
  const [customInput, setCustomInput] = useState("");

  useEffect(() => {
    fetch("http://localhost:8000/api/outlets")
      .then((res) => (res.ok ? res.json() : Promise.reject()))
      .then((data) => {
        setAvailableOutlets(data.outlets || FALLBACK_OUTLETS);
        setSelectedOutlets(data.defaults || FALLBACK_DEFAULTS);
        if (data.max) setMaxOutlets(data.max);
      })
      .catch(() => {});
  }, []);

  const totalSelected = selectedOutlets.length + customOutlets.length;

  function toggleOutlet(name) {
    setSelectedOutlets((current) =>
      current.includes(name)
        ? current.filter((o) => o !== name)
        : [...current, name]
    );
  }

  function addCustomOutlet() {
    const value = customInput.trim();
    if (!value) return;

    if (!value.includes(".") || /\s/.test(value)) {
      setError("Enter an outlet website like politico.com");
      return;
    }

    const normalized = value
      .toLowerCase()
      .replace(/^https?:\/\//, "")
      .replace(/^www\./, "")
      .split("/")[0];

    if (!customOutlets.includes(normalized)) {
      setCustomOutlets((current) => [...current, normalized]);
    }
    setCustomInput("");
    setError("");
  }

  function removeCustomOutlet(domain) {
    setCustomOutlets((current) => current.filter((d) => d !== domain));
  }

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
  // Outlets actually searched for the current results (from the backend).
  const [searchedOutlets, setSearchedOutlets] = useState([]);

  function outletParams(params = new URLSearchParams()) {
    searchedOutlets.forEach((outlet) => params.append("outlets", outlet));
    return params;
  }

  async function handleAnalyze(e) {
    e.preventDefault();

    if (totalSelected === 0) {
      setError("Select or add at least one news outlet.");
      return;
    }

    if (totalSelected > maxOutlets) {
      setError(`Please select at most ${maxOutlets} outlets.`);
      return;
    }

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
          body: JSON.stringify({
            event: event.trim(),
            outlets: selectedOutlets,
            custom_outlets: customOutlets,
          }),
        }
      );

      const data = await response.json();
      console.log("Analyze API response:", data);

      setSelectedEventId(data.event_id ?? null);
      setSearchedOutlets(data.searched_outlets || []);
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
      `http://localhost:8000/api/nlp/results?${outletParams(
        new URLSearchParams({ event_id: String(selectedEventId) })
      ).toString()}`
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
      `http://localhost:8000/api/sentiment/results?${outletParams(
        new URLSearchParams({ event_id: String(selectedEventId) })
      ).toString()}`
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
    const params = new URLSearchParams({
      event_id: String(selectedEventId)
    });

    // Only the outlets that were actually searched
    outletParams(params);

    const response = await fetch(
      `http://localhost:8000/api/emotion/results?${params.toString()}`
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

        <section className="outlet-picker">
          <div className="outlet-picker-header">
            <h3>News Outlets</h3>
            <span>
              {totalSelected} selected (max {maxOutlets})
            </span>
          </div>

          <div className="outlet-options">
            {availableOutlets.map((name) => (
              <label
                key={name}
                className={`outlet-chip ${
                  selectedOutlets.includes(name) ? "selected" : ""
                }`}
              >
                <input
                  type="checkbox"
                  checked={selectedOutlets.includes(name)}
                  onChange={() => toggleOutlet(name)}
                />
                {name}
              </label>
            ))}

            {customOutlets.map((domain) => (
              <span key={domain} className="outlet-chip selected custom">
                {domain}
                <button
                  type="button"
                  aria-label={`Remove ${domain}`}
                  onClick={() => removeCustomOutlet(domain)}
                >
                  ×
                </button>
              </span>
            ))}
          </div>

          <div className="custom-outlet">
            <input
              type="text"
              placeholder="Add your own outlet, e.g. politico.com"
              value={customInput}
              onChange={(e) => setCustomInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  addCustomOutlet();
                }
              }}
            />
            <button type="button" onClick={addCustomOutlet}>
              Add Outlet
            </button>
          </div>
        </section>

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
