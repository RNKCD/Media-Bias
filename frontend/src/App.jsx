
import { useState } from "react";
import "./App.css";

function App() {
  const [event, setEvent] = useState("");


  async function handleAnalyze(e) {
    e.preventDefault();
  
    try {
      const response = await fetch("http://localhost:8000/api/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ event }),
      });
  
      if (!response.ok) {
        throw new Error("Backend request failed");
      }
  
      const data = await response.json();
      alert(data.message);
  
    } catch (error) {
      console.error(error);
      alert("Unable to connect to MediaLens backend.");
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

          <button type="submit">Analyze Event</button>
        </form>

        <section className="features">
          <div className="feature-card">
            <h3>Sentiment Analysis</h3>
            <p>Compare emotional tone across news outlets.</p>
          </div>

          <div className="feature-card">
            <h3>Political Framing</h3>
            <p>Discover differences in reporting perspectives.</p>
          </div>

          <div className="feature-card">
            <h3>Coverage Comparison</h3>
            <p>Identify differences in what outlets emphasize.</p>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
