import { Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

function UserLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="app">
      <div className="user-header">
        <span>Welcome, {user?.name}</span>

        <button onClick={handleLogout}>
          Logout
        </button>
      </div>

      <Outlet />
    </div>
  )
}

export default UserLayout