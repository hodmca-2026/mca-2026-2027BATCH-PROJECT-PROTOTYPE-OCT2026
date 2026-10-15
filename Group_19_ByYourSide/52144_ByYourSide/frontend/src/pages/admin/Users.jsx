import { useEffect, useState } from "react";
import { useAuth } from "../../context/AuthContext";

function Users() {
  const { token, user: currentUser } = useAuth();

  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [updatingId, setUpdatingId] = useState(null);

  const fetchUsers = async () => {
    try {
      const response = await fetch(
        "http://localhost:5000/api/admin/users",
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || "Unable to load users");
      }

      setUsers(data.users);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchUsers();
    }
  }, [token]);

  const handleRoleChange = async (userId, role) => {
    try {
      setUpdatingId(userId);
      setError("");

      const response = await fetch(
        `http://localhost:5000/api/admin/users/${userId}/role`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ role }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || "Unable to update role");
      }

      setUsers((currentUsers) =>
        currentUsers.map((item) =>
          item.id === userId
            ? { ...item, role }
            : item
        )
      );
    } catch (error) {
      setError(error.message);
    } finally {
      setUpdatingId(null);
    }
  };

  return (
    <main className="admin-users-page">
      <div className="admin-page-header">
        <div>
          <h1>Users</h1>
          <p>Manage registered users and their roles.</p>
        </div>

        <div className="admin-user-count">
          Total Users: {users.length}
        </div>
      </div>

      {loading && <p>Loading users...</p>}

      {error && <p className="error-message">{error}</p>}

      {!loading && !error && users.length === 0 && (
        <p>No users found.</p>
      )}

      {!loading && users.length > 0 && (
        <div className="admin-table-container">
          <table className="admin-users-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Email</th>
                <th>Role</th>
                <th>Registered</th>
                <th>Action</th>
              </tr>
            </thead>

            <tbody>
              {users.map((item) => {
                const isCurrentUser =
                  Number(item.id) === Number(currentUser?.id);

                return (
                  <tr key={item.id}>
                    <td>{item.id}</td>

                    <td>{item.name}</td>

                    <td>{item.email}</td>

                    <td>
                      <span className={`role-badge ${item.role}`}>
                        {item.role}
                      </span>
                    </td>

                    <td>
                      {new Date(
                        item.created_at
                      ).toLocaleDateString("en-IN")}
                    </td>

                    <td>
                      {isCurrentUser ? (
                        <span>Current account</span>
                      ) : (
                        <select
                          value={item.role}
                          disabled={updatingId === item.id}
                          onChange={(event) =>
                            handleRoleChange(
                              item.id,
                              event.target.value
                            )
                          }
                        >
                          <option value="user">User</option>
                          <option value="admin">Admin</option>
                        </select>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}

export default Users;