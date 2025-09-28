"use client";
import { useEffect, useState, useMemo, useCallback } from 'react';
import apiClient from '@/lib/api';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { Progress } from './ui/progress';
import { Badge } from './ui/badge';
import { toast } from 'sonner';
import { format } from 'date-fns';
import { CheckCircle2, XCircle, Search, Clock, FileText, Download, Eye, Filter } from 'lucide-react';
import { Input } from './ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import FileUpload from './FileUpload';
import { useAuth } from '@/contexts/AuthContext';

interface Job {
  job_id: string;
  asset_id: number;
  file_name: string;
  status: 'pending' | 'processing' | 'complete' | 'failed';
  message: string;
  created_at?: string;
}

export default function EnhancedJobStatusTracker() {
  const { user } = useAuth();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'complete' | 'processing' | 'failed'>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);

  useEffect(() => {
    if (user?.username) {
      const userJobsStorageKey = `active_jobs_${user.username}`;
      try {
        const savedJobs = localStorage.getItem(userJobsStorageKey);
        if (savedJobs) {
          setJobs(JSON.parse(savedJobs));
        } else {
          setJobs([]);
        }
      } catch (error) {
        console.error("Failed to load jobs from localStorage", error);
        localStorage.removeItem(userJobsStorageKey);
      }
    } else {
      setJobs([]);
    }
  }, [user]);

  useEffect(() => {
    if (user?.username) {
      const userJobsStorageKey = `active_jobs_${user.username}`;
      try {
        localStorage.setItem(userJobsStorageKey, JSON.stringify(jobs));
      } catch (error) {
        console.error("Failed to save jobs to localStorage", error);
      }
    }
  }, [jobs, user]);

  const filteredJobs = useMemo(() => {
    return jobs
      .filter(job => 
        job.file_name.toLowerCase().includes(searchTerm.toLowerCase())
      )
      .filter(job => 
        statusFilter === 'all' ? true : job.status === statusFilter
      );
  }, [jobs, searchTerm, statusFilter]);

  const paginatedJobs = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    return filteredJobs.slice(startIndex, endIndex);
  }, [filteredJobs, currentPage, itemsPerPage]);

  const totalPages = Math.ceil(filteredJobs.length / itemsPerPage);

  const handleNewJobStarted = useCallback((newJob: Job) => {
    setJobs(prevJobs => [newJob, ...prevJobs]);
  }, []);

  useEffect(() => {
    const interval = setInterval(async () => {
      const jobsToUpdate = jobs.filter(j => j.status === 'pending' || j.status === 'processing');
      if (jobsToUpdate.length > 0) {
        for (const job of jobsToUpdate) {
          try {
            const response = await apiClient.get(`/jobs/${job.job_id}/status`);
            setJobs(prevJobs => prevJobs.map(j => j.job_id === job.job_id ? response.data : j));
          } catch (error) {
            console.error(`Failed to get status for job ${job.job_id}`, error);
          }
        }
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [jobs]);

  const getStatusBadge = (status: Job['status']) => {
    const variants = {
      complete: { variant: "default" as const, icon: CheckCircle2, className: "bg-green-500 hover:bg-green-600" },
      failed: { variant: "destructive" as const, icon: XCircle, className: "" },
      processing: { variant: "secondary" as const, icon: Clock, className: "bg-blue-500 hover:bg-blue-600 text-white" },
      pending: { variant: "outline" as const, icon: Clock, className: "" }
    };
    
    const config = variants[status];
    const Icon = config.icon;
    
    return (
      <Badge variant={config.variant} className={`gap-1.5 ${config.className}`}>
        <Icon className="h-3 w-3" />
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
  };

  const getProgressValue = (status: Job['status']) => {
    switch (status) {
      case 'complete': return 100;
      case 'processing': return 60;
      case 'failed': return 100;
      default: return 20;
    }
  };

  const stats = useMemo(() => {
    const total = jobs.length;
    const active = jobs.filter(j => j.status === 'processing' || j.status === 'pending').length;
    const completed = jobs.filter(j => j.status === 'complete').length;
    const successRate = total > 0 ? Math.round((completed / total) * 100) : 0;
    
    return { total, active, completed, successRate };
  }, [jobs]);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="border-l-4 border-l-blue-500">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Documents</CardTitle>
            <FileText className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-black dark:text-teal-400">{stats.total}</div>
            <p className="text-xs text-muted-foreground">Documents processed</p>
          </CardContent>
        </Card>
        
        <Card className="border-l-4 border-l-red-500">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Jobs</CardTitle>
            <Clock className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-black dark:text-teal-400">{stats.active}</div>
            <p className="text-xs text-muted-foreground">Currently processing</p>
          </CardContent>
        </Card>
        
        <Card className="border-l-4 border-l-green-500">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-black dark:text-teal-400">{stats.successRate}%</div>
            <p className="text-xs text-muted-foreground">Analysis completion</p>
          </CardContent>
        </Card>
      </div>
      <FileUpload onNewJobStarted={handleNewJobStarted} />
      
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Document Analysis Status
              </CardTitle>
              <CardDescription>Track the progress of your document analysis jobs</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4 mb-6">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input 
                type="search" 
                placeholder="Search files..." 
                className="pl-9"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <Select value={statusFilter} onValueChange={(value: any) => setStatusFilter(value)}>
              <SelectTrigger className="w-[160px]">
                <Filter className="h-4 w-4 mr-2" />
                <SelectValue placeholder="All Statuses" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="complete">Complete</SelectItem>
                <SelectItem value="processing">Processing</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="border rounded-lg overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/50">
                  <TableHead className="font-semibold">File Name</TableHead>
                  <TableHead className="font-semibold">Status</TableHead>
                  <TableHead className="font-semibold">Progress</TableHead>
                  <TableHead className="text-right font-semibold">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {paginatedJobs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} className="h-32 text-center">
                      <div className="flex flex-col items-center gap-2">
                        <FileText className="h-8 w-8 text-muted-foreground" />
                        <p className="text-muted-foreground">
                          {filteredJobs.length === 0 && jobs.length > 0 
                            ? "No files match your search criteria"
                            : "No files uploaded yet. Upload a document to get started."
                          }
                        </p>
                      </div>
                    </TableCell>
                  </TableRow>
                ) : (
                  paginatedJobs.map((job) => (
                    <TableRow key={job.job_id} className="hover:bg-muted/30">
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <div className="p-2 rounded-md bg-primary/10">
                            <FileText className="h-4 w-4 text-primary" />
                          </div>
                          <div>
                            <div className="font-medium">{job.file_name}</div>
                            <div className="text-xs text-muted-foreground">ID: {job.job_id.substring(0, 8)}...</div>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        {getStatusBadge(job.status)}
                      </TableCell>
                      <TableCell className="min-w-[200px]">
                        <div className="space-y-2">
                          <Progress 
                            value={getProgressValue(job.status)} 
                            className={`h-2 [&>div]:bg-teal-500 ${job.status === 'failed' ? '[&>div]:bg-red-500' : ''}`} 
                          />
                          <span className="text-xs text-muted-foreground">{job.message}</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        {job.status === 'complete' && (
                          <div className="flex gap-2 justify-end">
                            <a href={`${apiClient.defaults.baseURL}/jobs/${job.job_id}/results.json`} target="_blank" rel="noopener noreferrer">
                              <Button variant="outline" size="sm" className="gap-1">
                                <Eye className="h-3 w-3" />
                                JSON
                              </Button>
                            </a>
                            <a href={`${apiClient.defaults.baseURL}/jobs/${job.job_id}/report.pdf`} target="_blank" rel="noopener noreferrer">
                              <Button size="sm" className="gap-1 bg-black text-white dark:bg-teal-500 dark:text-black border-none hover:bg-gray-900 dark:hover:bg-teal-600">
                                <Download className="h-3 w-3" />
                                PDF
                              </Button>
                            </a>
                          </div>
                        )}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
          
          <div className="flex items-center justify-between mt-6 pt-4 border-t">
            <div className="text-sm text-muted-foreground">
              Showing {paginatedJobs.length === 0 ? 0 : (currentPage - 1) * itemsPerPage + 1} to{' '}
              {Math.min(currentPage * itemsPerPage, filteredJobs.length)} of {filteredJobs.length} jobs
            </div>
            <div className="flex items-center gap-2">
              <Select value={String(itemsPerPage)} onValueChange={(value) => {
                setItemsPerPage(Number(value));
                setCurrentPage(1);
              }}>
                <SelectTrigger className="w-[70px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="10">10</SelectItem>
                  <SelectItem value="25">25</SelectItem>
                  <SelectItem value="50">50</SelectItem>
                </SelectContent>
              </Select>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))} 
                disabled={currentPage === 1 || filteredJobs.length === 0}
              >
                Previous
              </Button>
              <span className="text-sm text-muted-foreground px-2">
                {filteredJobs.length === 0 ? 0 : currentPage} of {Math.max(1, totalPages)}
              </span>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))} 
                disabled={currentPage === totalPages || filteredJobs.length === 0}
              >
                Next
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}