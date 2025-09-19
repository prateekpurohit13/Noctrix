class ProcessingError(Exception):
    # Base exception for errors during input file processing.
    pass

class UnsupportedFileTypeError(ProcessingError):
    # Raised when a file type is not supported by the processor.
    pass