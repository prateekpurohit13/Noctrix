"use client";

import ProtectedPage from "@/components/ProtectedPage";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";

function DashboardLayout({ children }: { children: React.ReactNode }) {
    const { user, logout } = useAuth();
    return (
        <div className="flex min-h-screen flex-col">
            <header className="sticky top-0 z-10 flex h-16 items-center justify-between border-b bg-background px-4">
                <h1 className="text-xl font-semibold">AI Document Analysis</h1>
                <div className="flex items-center gap-4">
                    <span>Welcome, {user?.username} ({user?.role})</span>
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
        <h2 className="text-2xl font-bold mb-4">Analyst Dashboard</h2>
        <p className="mb-6">Upload and process your documents here.</p>
        <div className="p-8 border-2 border-dashed rounded-lg">
            <p className="text-center text-gray-500">File Upload and Job Status components will go here.</p>
        </div>
      </DashboardLayout>
    </ProtectedPage>
  );
}