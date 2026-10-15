import ThemeToggle from "./ThemeToggle";

function Navbar() {
  return (
    <header className="navbar">
      <div className="container navbar-inner">
        <a href="#" className="brand">
          <span className="brand-mark">♡</span>
          <span>ByYourSide</span>
        </a>

        <nav className="nav-links" aria-label="Main navigation">
          <a href="#how-it-works">How it works</a>
          <a href="#support">Support</a>
          <a href="#about">About</a>
        </nav>

        <div className="nav-actions">
          <ThemeToggle />

          <a href="/register" className="button button-primary">
            Get Started
          </a>
        </div>
      </div>
    </header>
  );
}

export default Navbar;
