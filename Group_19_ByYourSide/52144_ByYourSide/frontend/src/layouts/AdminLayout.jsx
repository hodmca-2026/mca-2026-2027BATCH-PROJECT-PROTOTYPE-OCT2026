
import { Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./AdminLayout.css";

export default function AdminLayout() {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <div className="app admin-layout">
      <header className="admin-header">
        <div>
          <span className="admin-header-label">
            BYYOUR SIDE · ADMINISTRATION
          </span>
          <h2>Admin Panel</h2>
        </div>

        <button
          type="button"
          className="button button-secondary admin-logout-btn"
          onClick={handleLogout}
        >
          Logout
        </button>
      </header>

      <main className="admin-content">
        <Outlet />
      </main>
    </div>
  );
}
