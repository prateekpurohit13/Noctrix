"use client";
import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { toast } from 'sonner';
import apiClient from '@/lib/api';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { X, UploadCloud, FileText, Plus, Zap } from 'lucide-react';
import { cn } from '@/lib/utils';

interface FileUploadProps {
  onNewJobStarted: (job: any) => void;
}

export default function EnhancedFileUpload({ onNewJobStarted }: FileUploadProps) {
  const [stagedFiles, setStagedFiles] = useState<File[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    setStagedFiles(currentFiles => {
      const newFiles = acceptedFiles.filter(
        newFile => !currentFiles.some(existingFile => 
          existingFile.name === newFile.name && existingFile.size === newFile.size
        )
      );
      if (newFiles.length < acceptedFiles.length) {
        toast.info("Duplicate file(s) were ignored.");
      }
      return [...currentFiles, ...newFiles];
    });
  }, []);

  const { getRootProps, getInputProps, open, isDragActive } = useDropzone({
    onDrop,
    noClick: true,
    noKeyboard: true,
    accept: {
      'application/pdf': ['.pdf'],
      'image/*': ['.jpeg', '.png', '.jpg'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
      'application/zip': ['.zip'],
    },
  });

  const handleRemoveFile = (fileToRemove: File) => {
    setStagedFiles(currentFiles => currentFiles.filter(file => file !== fileToRemove));
  };
  
  const handleProcessFiles = async () => {
    if (stagedFiles.length === 0) {
      toast.warning("Please select at least one file to process.");
      return;
    }
    setIsProcessing(true);
    toast.info(`Starting analysis for ${stagedFiles.length} file(s)...`);

    for (const file of stagedFiles) {
      try {
        const formData = new FormData();
        formData.append('file', file);
        const uploadResponse = await apiClient.post('/upload', formData);
        const assetId = uploadResponse.data.asset_id;
        toast.success(`"${file.name}" uploaded successfully.`);
        const processResponse = await apiClient.post(`/process/${assetId}`);
        onNewJobStarted(processResponse.data);

      } catch (error: any) {
        console.error(`Failed to process file "${file.name}":`, error);
        toast.error(`Failed to start processing for "${file.name}".`);
      }
    }
    
    setStagedFiles([]);
    setIsProcessing(false);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <Card className="border-2 border-dashed border-muted-foreground/25 bg-gradient-to-br from-background to-muted/30">
      <CardHeader>
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-md bg-primary/10">
            <UploadCloud className="h-5 w-5 text-primary" />
          </div>
          <div>
            <CardTitle className="text-lg">Upload Documents</CardTitle>
            <CardDescription>
              Select files for AI analysis. Supports PDF, images, Excel, PowerPoint, and ZIP files.
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div 
          {...getRootProps({ className: 'outline-none' })}
          className={cn(
            "relative overflow-hidden",
            isDragActive && "ring-2 ring-primary ring-offset-2"
          )}
        >
          <input {...getInputProps()} />

          <div className={cn(
            "border-2 border-dashed rounded-lg p-8 transition-all duration-200",
            isDragActive ? "border-primary bg-primary/5" : "border-muted-foreground/25",
            stagedFiles.length === 0 ? "text-center" : ""
          )}>
            {stagedFiles.length === 0 ? (
              <div className="space-y-4">
                <div className="mx-auto w-16 h-16 bg-muted rounded-full flex items-center justify-center">
                  <UploadCloud className="w-8 h-8 text-muted-foreground" />
                </div>
                <div>
                  <p className="text-lg font-medium mb-2 dark:text-teal-400">
                    {isDragActive ? "Drop files here" : "Drag & drop files here"}
                  </p>
                  <p className="text-sm text-muted-foreground mb-4">
                    PDF, Images, Excel, PowerPoint, ZIP files supported
                  </p>
                  <Button onClick={open} variant="outline" className="gap-2">
                    <Plus className="h-4 w-4" />
                    Browse Files
                  </Button>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="font-medium">Ready for Analysis ({stagedFiles.length} files)</h4>
                  <Button onClick={open} variant="outline" size="sm" className="gap-2">
                    <Plus className="h-4 w-4" />
                    Add More
                  </Button>
                </div>
                
                <div className="grid gap-3 max-h-40 overflow-y-auto">
                  {stagedFiles.map((file, index) => (
                    <div key={index} className="flex items-center justify-between p-3 rounded-md border bg-background">
                      <div className="flex items-center gap-3 min-w-0 flex-1">
                        <div className="p-2 rounded bg-primary/10">
                          <FileText className="h-4 w-4 text-primary" />
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="font-medium text-sm truncate">{file.name}</p>
                          <p className="text-xs text-muted-foreground">{formatFileSize(file.size)}</p>
                        </div>
                      </div>
                      <Button 
                        variant="ghost" 
                        size="sm"
                        onClick={() => handleRemoveFile(file)} 
                        disabled={isProcessing}
                        className="text-muted-foreground hover:text-destructive"
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {stagedFiles.length > 0 && (
          <div className="mt-6 flex justify-end">
            <Button 
              onClick={handleProcessFiles} 
              disabled={isProcessing}
              className="gap-2 px-6 bg-black text-white dark:bg-teal-500 dark:text-black border-none hover:bg-gray-900 dark:hover:bg-teal-600"
            >
              {isProcessing ? (
                <>
                  <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Zap className="h-4 w-4" />
                  Start Analysis ({stagedFiles.length})
                </>
              )}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}