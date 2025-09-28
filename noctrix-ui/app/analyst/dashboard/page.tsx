"use client";
import ProtectedPage from "@/components/ProtectedPage";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ThemeSwitcher } from "@/components/ThemeSwitcher";
import JobStatusTracker from "@/components/JobStatusTracker";
import { FileText, BarChart3, Clock } from "lucide-react";
import { useState } from "react";

function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const handleLogout = async () => {
    setIsLoggingOut(true);
    try {
    await logout();
    } finally {
    setIsLoggingOut(false);
    }
  };

  return (
    <div className="flex min-h-screen">
      <div className="w-64 h-screen flex flex-col border-r bg-background p-6 fixed left-0 top-0">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-black dark:text-teal-400">Noctrix</h1>
          <p className="text-sm text-muted-foreground mt-1">Automatic File Cleansing and Analysis</p>
        </div>
                
        <nav className="space-y-2 flex-1">
          <div className="flex items-center gap-3 px-3 py-2 rounded-md bg-primary/10 text-primary">
            <BarChart3 className="h-4 w-4" />
            <span className="font-medium">Dashboard</span>
          </div>
          <div className="flex items-center gap-3 px-3 py-2 rounded-md text-muted-foreground">
            <FileText className="h-4 w-4" />
            <span>Documents</span>
          </div>
        </nav>
                
        <div className="p-4 border rounded-md bg-card flex flex-col gap-4 mt-auto">
          <div>
          <div className="text-sm text-muted-foreground mb-2">Account <br /></div>
          <div className="font-medium">{user?.username}</div>
          <Badge variant="default" className="mt-1 bg-cyan-500 hover:bg-cyan-600">{user?.role}</Badge>
          </div>
          <Button
          variant="outline"
          onClick={handleLogout}
          className="cursor-pointer transition-transform duration-200 active:scale-95 bg-black text-white dark:bg-teal-500 dark:text-black border-none hover:bg-gray-900 dark:hover:bg-teal-600"
          disabled={isLoggingOut}
          >
          {isLoggingOut ? "Signing Out..." : "Logout"}
          </Button>
        </div>
      </div>
    
      <div className="flex-1 flex flex-col ml-64 h-screen overflow-y-auto">
        <header className="border-b bg-background px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-black dark:text-teal-400">Analyst Dashboard</h2>
              <p className="text-muted-foreground mt-1">
                Upload and process your documents. Track analysis progress below.
              </p>
            </div>
            <div className="fixed top-4 right-4 z-50">
              <ThemeSwitcher />
            </div>
          </div>
        </header>
                
        <main className="flex-1 p-6 bg-background">
          {children}
        </main>
      </div>
    </div>
  );
}

export default function AnalystDashboardPage() {
  return (
    <ProtectedPage>
      <DashboardLayout>
        <div className="max-w-7xl mx-auto">
          <JobStatusTracker />
        </div>
      </DashboardLayout>
    </ProtectedPage>
  );
}