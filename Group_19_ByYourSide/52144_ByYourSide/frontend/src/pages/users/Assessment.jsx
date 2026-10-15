 import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

function Assessment() {
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const { token } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!text.trim()) return

    setLoading(true)
    setError('')

    try {
      const response = await fetch('http://localhost:5000/api/assessment', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          text: text.trim(),
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.message || 'Unable to process assessment')
      }

      sessionStorage.setItem(
        'assessmentResult',
        JSON.stringify({
          text: text.trim(),
          prediction: data.prediction,
        })
      )

      navigate('/result')
    } catch (error) {
      setError(error.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="assessment-page">
      <section className="assessment-header">
        <span className="auth-label">Check-in</span>

        <h1>What have you noticed?</h1>

        <p>
          Share what you have observed about someone you care about.
          You can describe changes in their behaviour, communication,
          emotions, or daily activities.
        </p>
      </section>

      <section className="assessment-card">
        <form onSubmit={handleSubmit}>
          <div className="form-field">
            <label htmlFor="observations">
              Tell us what you have noticed
            </label>

            <textarea
              id="observations"
              name="observations"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="For example: They have become more isolated recently and seem less interested in things they usually enjoy..."
              rows="8"
              required
              disabled={loading}
            />
          </div>

          <div className="assessment-note">
            <span>ⓘ</span>

            <p>
              Share observations in your own words. ByYourSide provides
              awareness and supportive guidance based on the information
              provided. It is not a medical diagnosis.
            </p>
          </div>

          {error && (
            <p className="assessment-error">
              {error}
            </p>
          )}

          <div className="assessment-actions">
            <Link
              to="/dashboard"
              className="button button-secondary"
            >
              Back
            </Link>

            <button
              type="submit"
              className="button button-primary"
              disabled={!text.trim() || loading}
            >
              {loading ? 'Processing...' : 'Continue'}
            </button>
          </div>
        </form>
      </section>
    </main>
  )
}

export default Assessment