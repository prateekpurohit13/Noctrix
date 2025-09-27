"use client";

import ProtectedPage from "@/components/ProtectedPage";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { ThemeSwitcher } from "@/components/ThemeSwitcher";
import JobStatusTracker from "@/components/JobStatusTracker";

function DashboardLayout({ children }: { children: React.ReactNode }) {
    const { user, logout } = useAuth();
    return (
        <div className="flex min-h-screen flex-col">
            <header className="sticky top-0 z-10 flex h-16 items-center justify-between border-b bg-background px-4">
                <h1 className="text-xl font-semibold">AI Document Analysis</h1>
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

export default function AnalystDashboardPage() {
  return (
    <ProtectedPage>
      <DashboardLayout>
        <div className="space-y-4">
            <h2 className="text-2xl font-bold">Analyst Dashboard</h2>
            <p className="text-muted-foreground">
                Upload and process your documents here. The status of your jobs will appear below.
            </p>
        </div>
        <div className="mt-6">
            <JobStatusTracker />
        </div>
      </DashboardLayout>
    </ProtectedPage>
  );
}