"use client";

import { useState, useEffect } from 'react';
import apiClient from '@/lib/api';
import { toast } from 'sonner';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface AnalyticsSummary {
    total_users: number;
    files_processed_last_7d: number;
    login_success: number;
    login_failed: number;
}

interface UsagePoint {
    bucket: string;
    jobs_count: number;
    logins_count: number;
}

export default function AnalyticsDashboard() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [usageData, setUsageData] = useState<UsagePoint[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const summaryRes = await apiClient.get('/admin/analytics/summary');
        setSummary(summaryRes.data);
        const usageRes = await apiClient.get('/admin/analytics/usage_over_time?days=30');
        setUsageData(usageRes.data.points);
      } catch (error) {
        toast.error('Failed to fetch analytics data.');
        console.error(error);
      }
    };
    fetchData();
  }, []);

  return (
    <div className="space-y-6">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
                <CardHeader><CardTitle>Total Users</CardTitle></CardHeader>
                <CardContent><div className="text-2xl font-bold">{summary?.total_users ?? '...'}</div></CardContent>
            </Card>
            <Card>
                <CardHeader><CardTitle>Files Processed (7d)</CardTitle></CardHeader>
                <CardContent><div className="text-2xl font-bold">{summary?.files_processed_last_7d ?? '...'}</div></CardContent>
            </Card>
            <Card>
                <CardHeader><CardTitle>Successful Logins</CardTitle></CardHeader>
                <CardContent><div className="text-2xl font-bold">{summary?.login_success ?? '...'}</div></CardContent>
            </Card>
            <Card>
                <CardHeader><CardTitle>Failed Logins</CardTitle></CardHeader>
                <CardContent><div className="text-2xl font-bold">{summary?.login_failed ?? '...'}</div></CardContent>
            </Card>
        </div>

        <Card>
            <CardHeader>
                <CardTitle>Usage Over Time (Last 30 Days)</CardTitle>
            </CardHeader>
            <CardContent className="h-[350px]">
                 <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={usageData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="bucket" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Line type="monotone" dataKey="jobs_count" name="Files Processed" stroke="#8884d8" />
                        <Line type="monotone" dataKey="logins_count" name="Logins" stroke="#82ca9d" />
                    </LineChart>
                </ResponsiveContainer>
            </CardContent>
        </Card>
    </div>
  );
}