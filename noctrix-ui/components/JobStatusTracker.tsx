"use client";
import { useEffect, useState } from 'react';
import apiClient from '@/lib/api';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { Progress } from './ui/progress';
import { toast } from 'sonner';
import { format } from 'date-fns';
import FileUpload from './FileUpload';

interface Job {
  job_id: string;
  asset_id: number;
  file_name: string;
  status: 'pending' | 'processing' | 'complete' | 'failed';
  message: string;
}

export default function JobStatusTracker() {
  const [jobs, setJobs] = useState<Job[]>([]);

  // Function to start a processing job
  const startProcessing = async (assetId: number) => {
    try {
      const response = await apiClient.post(`/process/${assetId}`);
      toast.success(`Processing started for asset #${assetId}`);
      // Add the new job to the top of our list
      setJobs(prevJobs => [response.data, ...prevJobs]);
    } catch (error: any) {
      console.error('Failed to start processing:', error);
      toast.error(error.response?.data?.detail || 'Failed to start processing.');
    }
  };

  // Effect to poll for status updates on pending/processing jobs
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
    }, 5000); // Poll every 5 seconds

    return () => clearInterval(interval);
  }, [jobs]);

  return (
    <div className="space-y-6">
      <FileUpload onUploadSuccess={startProcessing} />
      
      <Card>
        <CardHeader>
          <CardTitle>Processing Jobs</CardTitle>
          <CardDescription>Status of your recent document analysis jobs.</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>File Name</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-[200px]">Progress</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {jobs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-center">No jobs to display. Upload a file to get started.</TableCell>
                </TableRow>
              ) : (
                jobs.map((job) => (
                  <TableRow key={job.job_id}>
                    <TableCell className="font-medium">{job.file_name}</TableCell>
                    <TableCell>{job.status}</TableCell>
                    <TableCell>
                        <Progress value={job.status === 'complete' ? 100 : (job.status === 'processing' ? 50 : 0)} />
                        <span className="text-xs text-muted-foreground mt-1 block">{job.message}</span>
                    </TableCell>
                    <TableCell>
                      {job.status === 'complete' && (
                        <div className="flex gap-2">
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
        </CardContent>
      </Card>
    </div>
  );
}