"use client";
import { useEffect, useState, useMemo, useCallback } from 'react';
import apiClient from '@/lib/api';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { Progress } from './ui/progress';
import { toast } from 'sonner';
import { format } from 'date-fns';
import { CheckCircle2, XCircle, Search } from 'lucide-react';
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
}

export default function JobStatusTracker() {
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

  const StatusIndicator = ({ status }: { status: Job['status'] }) => {
    switch (status) {
        case 'complete':
            return <div className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-green-500" /><span>Complete</span></div>;
        case 'failed':
            return <div className="flex items-center gap-2"><XCircle className="h-4 w-4 text-red-500" /><span>Failed</span></div>;
        default:
            return <span className="capitalize">{status}</span>;
    }
  };

  return (
    <div className="space-y-6">
      <FileUpload onNewJobStarted={handleNewJobStarted} />
      
      <Card>
        <CardHeader>
          <CardTitle>File Details</CardTitle>
          <CardDescription>Status of your recent document analysis.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4 mb-4">
              <div className="relative flex-1">
                  <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input 
                      type="search" 
                      placeholder="Search by file name..." 
                      className="pl-8"
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                  />
              </div>
              <Select value={statusFilter} onValueChange={(value: any) => setStatusFilter(value)}>
                  <SelectTrigger className="w-[180px]">
                      <SelectValue placeholder="Filter by status" />
                  </SelectTrigger>
                  <SelectContent>
                      <SelectItem value="all">All Statuses</SelectItem>
                      <SelectItem value="complete">Complete</SelectItem>
                      <SelectItem value="processing">Processing</SelectItem>
                      <SelectItem value="failed">Failed</SelectItem>
                  </SelectContent>
              </Select>
          </div>

          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[40%]">File Name</TableHead>
                  <TableHead className="w-[15%]">Status</TableHead>
                  <TableHead className="w-[25%]">Progress</TableHead>
                  <TableHead className="text-right w-[20%]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {paginatedJobs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} className="h-24 text-center">No jobs to display. Upload a file to get started.</TableCell>
                  </TableRow>
                ) : (
                  paginatedJobs.map((job) => (
                    <TableRow key={job.job_id}>
                      <TableCell className="font-medium">{job.file_name}</TableCell>
                      <TableCell><StatusIndicator status={job.status} /></TableCell>
                      <TableCell>
                          <Progress value={job.status === 'complete' ? 100 : (job.status === 'processing' ? 50 : (job.status === 'failed' ? 100 : 0))} 
                                    className={job.status === 'failed' ? '[&>div]:bg-red-500' : ''} />
                          <span className="text-xs text-muted-foreground mt-1 block">{job.message}</span>
                      </TableCell>
                      <TableCell className="text-right">
                        {job.status === 'complete' && (
                          <div className="flex gap-2 justify-end">
                             <a href={`${apiClient.defaults.baseURL}/jobs/${job.job_id}/results.json`} target="_blank" rel="noopener noreferrer">
                                 <Button variant="outline" size="sm">View JSON</Button>
                             </a>
                             <a href={`${apiClient.defaults.baseURL}/jobs/${job.job_id}/report.pdf`} target="_blank" rel="noopener noreferrer">
                                 <Button variant="default" size="sm">Download PDF</Button>
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
          
          <div className="flex items-center justify-between mt-4">
              <div className="text-sm text-muted-foreground">
                  Showing {paginatedJobs.length} of {filteredJobs.length} jobs.
              </div>
              <div className="flex items-center gap-2">
                    <Select value={String(itemsPerPage)} onValueChange={(value) => setItemsPerPage(Number(value))}>
                        <SelectTrigger className="w-[70px]">
                            <SelectValue placeholder={itemsPerPage} />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="10">10</SelectItem>
                            <SelectItem value="25">25</SelectItem>
                            <SelectItem value="50">50</SelectItem>
                        </SelectContent>
                    </Select>
                    <Button variant="outline" size="sm" onClick={() => setCurrentPage(p => Math.max(1, p - 1))} disabled={currentPage === 1}>
                        Previous
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))} disabled={currentPage === totalPages}>
                        Next
                    </Button>
              </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}