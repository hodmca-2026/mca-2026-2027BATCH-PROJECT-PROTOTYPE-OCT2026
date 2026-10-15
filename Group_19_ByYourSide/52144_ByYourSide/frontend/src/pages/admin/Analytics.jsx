import { useEffect, useState } from "react";
import { useAuth } from "../../context/AuthContext";

function Analytics() {
  const { token } = useAuth();

  const [analytics, setAnalytics] = useState({
    totalAssessments: 0,
    predictions: [],
    dailyAssessments: [],
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const response = await fetch(
          "http://localhost:5000/api/admin/analytics",
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        const data = await response.json();

        if (!response.ok) {
          throw new Error(
            data.message || "Unable to load analytics"
          );
        }

        setAnalytics(data);
      } catch (error) {
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    if (token) {
      fetchAnalytics();
    }
  }, [token]);

  return (
    <main className="admin-analytics-page">
      <div className="admin-page-header">
        <div>
          <h1>Analytics</h1>
          <p>Overview of assessment activity and model outputs.</p>
        </div>
      </div>

      {loading && <p>Loading analytics...</p>}

      {error && <p className="error-message">{error}</p>}

      {!loading && !error && (
        <>
          <section className="analytics-stats">
            <div className="analytics-card">
              <span>Total Assessments</span>
              <strong>{analytics.totalAssessments}</strong>
            </div>
          </section>

          <section className="analytics-section">
            <h2>Prediction Distribution</h2>

            {analytics.predictions.length === 0 ? (
              <p>No prediction data available.</p>
            ) : (
              <div className="analytics-grid">
                {analytics.predictions.map((item) => (
                  <div
                    className="analytics-card"
                    key={item.prediction}
                  >
                    <span>{item.prediction}</span>
                    <strong>{item.count}</strong>
                  </div>
                ))}
              </div>
            )}
          </section>

          <section className="analytics-section">
            <h2>Daily Assessments</h2>

            {analytics.dailyAssessments.length === 0 ? (
              <p>No daily assessment data available.</p>
            ) : (
              <div className="admin-table-container">
                <table className="admin-analytics-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Assessments</th>
                    </tr>
                  </thead>

                  <tbody>
                    {analytics.dailyAssessments.map((item) => (
                      <tr key={item.date}>
                        <td>
                          {new Date(item.date).toLocaleDateString(
                            "en-IN"
                          )}
                        </td>
                        <td>{item.count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      )}
    </main>
  );
}

export default Analytics;