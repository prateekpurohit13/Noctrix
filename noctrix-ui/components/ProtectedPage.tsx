"use client";

import { useAuth } from "@/contexts/AuthContext";
import { useRouter } from "next/navigation";
import { useEffect, ReactNode } from "react";
export default function ProtectedPage({
  children,
  allowedRoles,
}: {
  children: ReactNode;
  allowedRoles?: string[];
}) {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) {
      return;
    }
    if (!user) {
      router.push("/login");
      return;
    }
    if (allowedRoles && !allowedRoles.includes(user.role)) {
      router.push("/analyst/dashboard"); 
    }
  }, [user, isLoading, router, allowedRoles]);
  if (isLoading || !user || (allowedRoles && !allowedRoles.includes(user.role))) {
    return <div className="flex h-screen items-center justify-center">Loading...</div>;
  }

  return <>{children}</>;
}