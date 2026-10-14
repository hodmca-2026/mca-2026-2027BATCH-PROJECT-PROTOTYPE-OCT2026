import { createContext, useContext, useState, useCallback } from "react";

const UserContext = createContext(null);

export function UserProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("bazaaro_token"));
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem("bazaaro_user");
    return raw ? JSON.parse(raw) : null;
  });

  const login = useCallback((newToken, newUser) => {
    localStorage.setItem("bazaaro_token", newToken);
    localStorage.setItem("bazaaro_user", JSON.stringify(newUser));
    setToken(newToken);
    setUser(newUser);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("bazaaro_token");
    localStorage.removeItem("bazaaro_user");
    setToken(null);
    setUser(null);
  }, []);

  return (
    <UserContext.Provider value={{ token, user, login, logout, isAuthenticated: !!token }}>
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  return useContext(UserContext);
}
