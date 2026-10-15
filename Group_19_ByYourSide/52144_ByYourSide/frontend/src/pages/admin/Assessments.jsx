import { useEffect, useState } from "react";
import { useAuth } from "../../context/AuthContext";

function Assessments() {
  const { token } = useAuth();

  const [assessments, setAssessments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchAssessments = async () => {
      try {
        const response = await fetch(
          "http://localhost:5000/api/admin/assessments",
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        const data = await response.json();

        if (!response.ok) {
          throw new Error(
            data.message || "Unable to load assessments"
          );
        }

        setAssessments(data.assessments);
      } catch (error) {
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    if (token) {
      fetchAssessments();
    }
  }, [token]);

  return (
    <main className="admin-assessments-page">
      <div className="admin-page-header">
        <div>
          <h1>Assessments</h1>
          <p>View assessment records submitted by users.</p>
        </div>

        <div className="admin-user-count">
          Total Assessments: {assessments.length}
        </div>
      </div>

      {loading && <p>Loading assessments...</p>}

      {error && <p className="error-message">{error}</p>}

      {!loading && !error && assessments.length === 0 && (
        <p>No assessments found.</p>
      )}

      {!loading && !error && assessments.length > 0 && (
        <div className="admin-table-container">
          <table className="admin-assessments-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>User</th>
                <th>Email</th>
                <th>Text</th>
                <th>Prediction</th>
                <th>Date</th>
              </tr>
            </thead>

            <tbody>
              {assessments.map((assessment) => (
                <tr key={assessment.id}>
                  <td>{assessment.id}</td>

                  <td>{assessment.user_name}</td>

                  <td>{assessment.email}</td>

                  <td className="assessment-text">
                    {assessment.text}
                  </td>

                  <td>
                    <span
                      className={`prediction-badge ${assessment.prediction}`}
                    >
                      {assessment.prediction}
                    </span>
                  </td>

                  <td>
                    {new Date(
                      assessment.created_at
                    ).toLocaleDateString("en-IN")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}

export default Assessments;