function Hero() {
  return (
    <section className="hero-section">
      <div className="container hero-content">
        <div className="hero-copy">
          <span className="eyebrow">A little care can go a long way</span>

          <h1>
            Be there.
            <br />
            <span>Start with noticing.</span>
          </h1>

          <p className="hero-description">
            ByYourSide helps you understand concerning changes you notice
            in someone you care about and find a thoughtful way to respond.
          </p>

          <div className="hero-actions">
            <a href="#get-started" className="button button-primary button-large">
              Start a check-in
              <span>→</span>
            </a>

            <a
              href="#how-it-works"
              className="button button-secondary button-large"
            >
              How it works
            </a>
          </div>

          <p className="hero-note">
            Simple guidance. No diagnosis. No judgment.
          </p>
        </div>

        <div className="hero-visual" aria-hidden="true">
          <div className="hero-glow"></div>

          <div className="hero-card hero-card-main">
            <div className="heart-icon">♡</div>

            <span className="small-label">Sometimes</span>

            <h3>
              Someone you care about
              <br />
              may not say they need help.
            </h3>

            <div className="hero-card-line"></div>

            <p>
              You noticed something changed.
              <br />
              That's a good place to start.
            </p>
          </div>

          <div className="floating-card floating-card-top">
            <span>👀</span>

            <div>
              <strong>Notice</strong>
              <small>What has changed?</small>
            </div>
          </div>

          <div className="floating-card floating-card-bottom">
            <span>🤝</span>

            <div>
              <strong>Respond</strong>
              <small>With care</small>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

export default Hero