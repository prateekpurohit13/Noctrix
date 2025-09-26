"use client";
import { useEffect, useState } from "react";
import { isLoggedIn, getUsername, getUserRole, logoutUser } from "@/lib/auth";

export default function Dashboard() {
  const [username, setUsername] = useState("");
  const [role, setRole] = useState("");

  useEffect(() => {
    if (!isLoggedIn()) {
      window.location.href = "/login";
    } else {
      setUsername(getUsername());
      setRole(getUserRole());
    }
  }, []);

  const handleLogout = () => {
    logoutUser();
    window.location.href = "/login";
  };

  return (
    <div className="p-8 min-h-screen bg-gray-50">
      <h1 className="text-3xl font-bold mb-2">Welcome, {username}!</h1>
      <p className="mb-4">Role: {role}</p>
      <button
        onClick={handleLogout}
        className="bg-red-500 text-white px-4 py-2 rounded mb-6"
      >
        Logout
      </button>

      {role === "admin" && (
        <div className="mt-6 p-4 border rounded bg-gray-100">
          <h3 className="text-lg font-bold mb-2">Admin Panel</h3>
          <ul className="list-disc list-inside">
            <li>User Management</li>
            <li>Usage Analytics</li>
            <li>Settings & Preferences</li>
          </ul>
        </div>
      )}
    </div>
  );
}
