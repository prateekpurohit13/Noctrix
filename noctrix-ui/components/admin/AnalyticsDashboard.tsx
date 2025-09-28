"use client";
import { useState, useEffect } from 'react';
import apiClient from '@/lib/api';
import { toast } from 'sonner';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Users, FileText, CheckCircle, XCircle, TrendingUp, Activity } from 'lucide-react';

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

export default function EnhancedAnalyticsDashboard() {
    const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
    const [usageData, setUsageData] = useState<UsagePoint[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setIsLoading(true);
                const [summaryRes, usageRes] = await Promise.all([
                    apiClient.get('/admin/analytics/summary'),
                    apiClient.get('/admin/analytics/usage_over_time?days=30')
                ]);
                
                setSummary(summaryRes.data);
                setUsageData(usageRes.data.points);
            } catch (error) {
                toast.error('Failed to fetch analytics data.');
                console.error(error);
            } finally {
                setIsLoading(false);
            }
        };

        fetchData();
    }, []);

    const formatTooltipValue = (value: number, name: string) => {
        return [value, name === 'jobs_count' ? 'Files Processed' : 'Logins'];
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center gap-2 mb-6">
                <div className="p-2 rounded-md bg-primary/10">
                    <Activity className="h-5 w-5 text-primary" />
                </div>
                <div>
                    <h3 className="text-lg font-semibold">System Analytics</h3>
                    <p className="text-sm text-muted-foreground">
                        Overview of system usage and performance metrics
                    </p>
                </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card className="border-l-4 border-l-blue-500">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Total Users</CardTitle>
                        <Users className="h-4 w-4 text-blue-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            {isLoading ? (
                                <div className="w-16 h-6 bg-muted animate-pulse rounded" />
                            ) : (
                                summary?.total_users ?? '0'
                            )}
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">Registered accounts</p>
                    </CardContent>
                </Card>

                <Card className="border-l-4 border-l-green-500">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Files Processed</CardTitle>
                        <FileText className="h-4 w-4 text-green-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            {isLoading ? (
                                <div className="w-16 h-6 bg-muted animate-pulse rounded" />
                            ) : (
                                summary?.files_processed_last_7d ?? '0'
                            )}
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">Last 7 days</p>
                    </CardContent>
                </Card>

                <Card className="border-l-4 border-l-emerald-500">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Successful Logins</CardTitle>
                        <CheckCircle className="h-4 w-4 text-emerald-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            {isLoading ? (
                                <div className="w-16 h-6 bg-muted animate-pulse rounded" />
                            ) : (
                                summary?.login_success ?? '0'
                            )}
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">Authentication attempts</p>
                    </CardContent>
                </Card>

                <Card className="border-l-4 border-l-red-500">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Failed Logins</CardTitle>
                        <XCircle className="h-4 w-4 text-red-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            {isLoading ? (
                                <div className="w-16 h-6 bg-muted animate-pulse rounded" />
                            ) : (
                                summary?.login_failed ?? '0'
                            )}
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">Security alerts</p>
                    </CardContent>
                </Card>
            </div>

            <Card>
                <CardHeader>
                    <div className="flex items-center gap-2">
                        <TrendingUp className="h-5 w-5 text-primary" />
                        <div>
                            <CardTitle>Usage Trends</CardTitle>
                            <CardDescription>System activity over the last 30 days</CardDescription>
                        </div>
                    </div>
                </CardHeader>
                <CardContent>
                    <div className="h-[400px] w-full">
                        {isLoading ? (
                            <div className="h-full w-full bg-muted animate-pulse rounded" />
                        ) : (
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={usageData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                                    <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                                    <XAxis 
                                        dataKey="bucket" 
                                        tick={{ fontSize: 12 }}
                                        tickLine={{ stroke: '#666' }}
                                    />
                                    <YAxis 
                                        tick={{ fontSize: 12 }}
                                        tickLine={{ stroke: '#666' }}
                                    />
                                    <Tooltip 
                                        formatter={formatTooltipValue}
                                        contentStyle={{ 
                                            backgroundColor: 'hsl(var(--card))', 
                                            border: '1px solid hsl(var(--border))',
                                            borderRadius: '8px',
                                            boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                                        }}
                                    />
                                    <Legend />
                                    <Line 
                                        type="monotone" 
                                        dataKey="jobs_count" 
                                        name="Files Processed" 
                                        stroke="#10b981" 
                                        strokeWidth={2}
                                        dot={{ fill: '#10b981', strokeWidth: 2, r: 4 }}
                                        activeDot={{ r: 6, stroke: '#10b981', strokeWidth: 2 }}
                                    />
                                    <Line 
                                        type="monotone" 
                                        dataKey="logins_count" 
                                        name="Logins" 
                                        stroke="#3b82f6" 
                                        strokeWidth={2}
                                        dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
                                        activeDot={{ r: 6, stroke: '#3b82f6', strokeWidth: 2 }}
                                    />
                                </LineChart>
                            </ResponsiveContainer>
                        )}
                    </div>
                    
                    {!isLoading && usageData.length === 0 && (
                        <div className="flex flex-col items-center justify-center h-[400px] text-center">
                            <TrendingUp className="h-12 w-12 text-muted-foreground mb-4" />
                            <p className="text-muted-foreground">No usage data available</p>
                            <p className="text-sm text-muted-foreground mt-1">Data will appear once users start using the system</p>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}