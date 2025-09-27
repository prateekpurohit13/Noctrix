"use client";
import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { toast } from 'sonner';
import apiClient from '@/lib/api';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { X, UploadCloud, File as FileIcon } from 'lucide-react';

interface FileUploadProps {
  onNewJobStarted: (job: any) => void;
}

export default function FileUpload({ onNewJobStarted }: FileUploadProps) {
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

  const { getRootProps, getInputProps, open } = useDropzone({
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

  return (
    <Card>
      <CardHeader>
        <CardTitle>Upload Document</CardTitle>
        <CardDescription>Select one or more files to prepare them for analysis.</CardDescription>
      </CardHeader>
      <CardContent>
        <div {...getRootProps({ className: 'outline-none' })}>
          <input {...getInputProps()} />        
          <div className="flex flex-col items-center justify-center w-full p-6 border-2 border-dashed rounded-md">
             {stagedFiles.length === 0 ? (
                 <div className="text-center">
                    <UploadCloud className="w-10 h-10 mx-auto mb-4 text-muted-foreground" />
                    <p className="mb-2 text-sm text-muted-foreground">
                        <span className="font-semibold">Drag & drop files here</span>
                    </p>
                 </div>
             ) : (
                <div className="w-full">
                    <h3 className="text-sm font-medium mb-2">Staged Files:</h3>
                    <ul className="space-y-2">
                        {stagedFiles.map((file, index) => (
                            <li key={index} className="flex items-center justify-between p-2 rounded-md bg-muted/50">
                                <div className="flex items-center gap-2 overflow-hidden">
                                    <FileIcon className="h-4 w-4 flex-shrink-0 text-muted-foreground" />
                                    <span className="text-sm font-medium truncate">{file.name}</span>
                                </div>
                                <Button variant="ghost" size="icon" className="h-6 w-6 flex-shrink-0" onClick={() => handleRemoveFile(file)} disabled={isProcessing}>
                                    <X className="h-4 w-4" />
                                </Button>
                            </li>
                        ))}
                    </ul>
                </div>
             )}
          </div>
          
          <div className="flex justify-end gap-2 mt-4">
              <Button variant="outline" onClick={open} disabled={isProcessing}>
                  Browse Files
              </Button>
              {stagedFiles.length > 0 && (
                <Button onClick={handleProcessFiles} disabled={isProcessing}>
                    {isProcessing ? `Processing...` : `Start Analysis (${stagedFiles.length})`}
                </Button>
              )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}