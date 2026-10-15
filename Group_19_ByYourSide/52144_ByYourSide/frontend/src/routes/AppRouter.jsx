import { BrowserRouter, Route, Routes } from "react-router-dom";

import PublicLayout from "../layouts/PublicLayout";
import UserLayout from "../layouts/UserLayout";
import AdminLayout from "../layouts/AdminLayout";

import Home from "../pages/public/Home";
import Login from "../pages/auth/Login";
import Register from "../pages/auth/Register";

import Dashboard from "../pages/users/Dashboard";
import Assessment from "../pages/users/Assessment";
import Result from "../pages/users/Result";
import History from "../pages/users/History";

import AdminDashboard from "../pages/admin/AdminDashboard";
import Users from "../pages/admin/Users";
import Assessments from "../pages/admin/Assessments";
import Analytics from "../pages/admin/Analytics";
import ProtectedRoute from "./ProtectedRoute";

import AdminRoute from "./AdminRoute";

function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<PublicLayout />}>
          <Route path="/" element={<Home />} />
        </Route>

        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        <Route element={<ProtectedRoute />}>
          <Route element={<UserLayout />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/assessment" element={<Assessment />} />
            <Route path="/result" element={<Result />} />
            <Route path="/result/:id" element={<Result />} />
            <Route path="/history" element={<History />} />
          </Route>
        </Route>

        <Route element={<AdminRoute />}>
          <Route element={<AdminLayout />}>
            <Route path="/admin" element={<AdminDashboard />} />
            <Route path="/admin/users" element={<Users />} />
            <Route path="/admin/assessments" element={<Assessments />} />
            <Route path="/admin/analytics" element={<Analytics />} />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default AppRouter;
