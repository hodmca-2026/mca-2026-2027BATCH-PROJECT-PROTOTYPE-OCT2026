import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

function History() {
  const { token } = useAuth();
  const navigate = useNavigate();

  const [assessments, setAssessments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const response = await fetch(
          "http://localhost:5000/api/assessment/history",
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          },
        );

        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.message || "Unable to load assessment history");
        }

        setAssessments(data.assessments);
      } catch (error) {
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, [token]);

  const formatDate = (date) => {
    return new Date(date).toLocaleString("en-IN", {
      dateStyle: "medium",
      timeStyle: "short",
    });
  };

  return (
    <main className="history-page">
      <section className="history-header">
        <span className="auth-label">Your history</span>

        <h1>Previous check-ins</h1>

        <p>
          Review the observations you previously submitted and the patterns
          identified from them.
        </p>
      </section>

      {loading && (
        <section className="history-state">
          <p>Loading your check-ins...</p>
        </section>
      )}

      {error && (
        <section className="history-state history-error">
          <p>{error}</p>
        </section>
      )}

      {!loading && !error && assessments.length === 0 && (
        <section className="history-empty">
          <span className="result-label">No check-ins yet</span>

          <h2>Start your first check-in</h2>

          <p>
            Share an observation about someone you care about to receive
            awareness and supportive guidance.
          </p>

          <Link to="/assessment" className="button button-primary">
            Start a check-in
          </Link>
        </section>
      )}

      {!loading && !error && assessments.length > 0 && (
        <section className="history-list">
          {assessments.map((assessment) => (
            <article className="history-card" key={assessment.id}>
              <div className="history-card-header">
                <div>
                  <span className="history-card-label">Observed pattern</span>

                  <h2>{assessment.prediction}</h2>
                </div>

                <span className="history-date">
                  {formatDate(assessment.created_at)}
                </span>
              </div>

              <div className="history-observation">
                <span className="history-card-label">Your observation</span>

                <p>{assessment.text}</p>
                <button
                  className="history-view-button"
                  onClick={() => navigate(`/result/${assessment.id}`)}
                >
                  View details →
                </button>
              </div>
            </article>
          ))}
        </section>
      )}

      <section className="history-actions">
        <Link to="/assessment" className="button button-primary">
          New check-in
        </Link>

        <Link to="/dashboard" className="button button-secondary">
          Back to dashboard
        </Link>
      </section>
    </main>
  );
}

export default History;
