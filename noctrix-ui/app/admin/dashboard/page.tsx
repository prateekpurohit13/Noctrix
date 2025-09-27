"use client";

import ProtectedPage from "@/components/ProtectedPage";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { ThemeSwitcher } from "@/components/ThemeSwitcher";
import UserManagement from "@/components/admin/UserManagement";
import AnalyticsDashboard from "@/components/admin/AnalyticsDashboard"; 

function DashboardLayout({ children }: { children: React.ReactNode }) {
    const { user, logout } = useAuth();
    return (
        <div className="flex min-h-screen flex-col">
            <header className="sticky top-0 z-10 flex h-16 items-center justify-between border-b bg-background px-4">
                <div className="flex items-center gap-6">
                    <h1 className="text-xl font-semibold">Noctrix</h1>
                    <nav className="flex items-center gap-4 text-sm font-medium">
                        <Link href="/analyst/dashboard" className="text-muted-foreground hover:text-foreground">Analyst View</Link>
                        {user?.role === 'Admin' && (
                             <Link href="/admin/dashboard" className="text-foreground">Admin Dashboard</Link>
                        )}
                    </nav>
                </div>
                <div className="flex items-center gap-4">
                    <span>Welcome, {user?.username} ({user?.role})</span>
                    <ThemeSwitcher />
                    <Button variant="outline" onClick={logout}>Logout</Button>
                </div>
            </header>
            <main className="flex-1 p-6">
                {children}
            </main>
        </div>
    )
}

export default function AdminDashboardPage() {
  return (
    <ProtectedPage allowedRoles={["Admin"]}>
      <DashboardLayout>
          <div className="space-y-4 mb-6">
            <h2 className="text-2xl font-bold">Admin Dashboard</h2>
            <p className="text-muted-foreground">Manage users and monitor system analytics.</p>
          </div>
          
          <div className="space-y-8">
              <AnalyticsDashboard />
              <UserManagement />
          </div>

      </DashboardLayout>
    </ProtectedPage>
  );
}