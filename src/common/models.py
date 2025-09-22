import uuid
from pydantic import BaseModel, Field, conint
from typing import List, Dict, Optional, Any, Literal, Union
from enum import Enum
import networkx as nx

class ContentType(str, Enum):
    POLICY = "policy"
    CONFIGURATION = "configuration"
    LOG = "log"
    REPORT = "report"
    DIAGRAM = "diagram"
    TABLE = "table"
    UNKNOWN = "unknown"

class Language(str, Enum):
    EN = "en"
    UNKNOWN = "unknown"

#Document Structure Models
class Position(BaseModel):
    page_num: int = Field(..., ge=0, description="Page number (0-indexed).")
    x1: float = Field(..., description="X-coordinate of the top-left corner.")
    y1: float = Field(..., description="Y-coordinate of the top-left corner.")
    x2: float = Field(..., description="X-coordinate of the bottom-right corner.")
    y2: float = Field(..., description="Y-coordinate of the bottom-right corner.")

class Element(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the element.")
    type: str = Field(..., description="Type of element (e.g., 'text', 'heading', 'table', 'image').")
    text_content: Optional[str] = Field(None, description="Extracted text content of the element.")
    position: Optional[Position] = Field(None, description="Positional information of the element.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional element-specific metadata (e.g., font size, color).")

class TextElement(Element):
    type: Literal["text", "heading", "list_item", "paragraph"] = "text"

class TableCell(BaseModel):
    row: int = Field(..., ge=0)
    col: int = Field(..., ge=0)
    text_content: str
    position: Optional[Position] = None

class TableElement(Element):
    type: Literal["table"] = "table"
    rows: List[List[TableCell]] = Field(..., description="2D list of TableCell objects.")
    caption: Optional[str] = Field(None, description="Table caption.")

class ImageElement(Element):
    type: Literal["image"] = "image"
    image_path: Optional[str] = Field(None, description="Path to the extracted image file (if saved separately).")
    description: Optional[str] = Field(None, description="Description derived from OCR or surrounding text.")

#Main Document Object Model
class DocumentObjectModel(BaseModel):
    file_name: str = Field(..., description="Original name of the input file.")
    file_hash: str = Field(..., description="SHA256 hash of the original file content for integrity check.")
    processed_timestamp: str = Field(..., description="Timestamp of when the document was processed (ISO format).")
    detected_content_type: ContentType = Field(ContentType.UNKNOWN, description="Automatically detected purpose/type of the document.")
    detected_language: Language = Field(Language.UNKNOWN, description="Automatically detected primary language of the document.")
    page_count: int = Field(..., ge=1, description="Total number of pages in the document.")
    sections: List[Union[TextElement, TableElement, ImageElement, Element]] = Field([], description="A list of structured elements.")
    initial_metadata: Dict[str, Any] = Field(default_factory=dict, description="General metadata from input processing.")

class EntityType(str, Enum):
    PERSON = "Person"
    ORGANIZATION = "Organization"
    LOCATION = "Location"
    DATE_TIME = "Date/Time"
    IP_ADDRESS = "IP Address"
    HOSTNAME = "Hostname"
    EMAIL = "Email Address"
    PHONE_NUMBER = "Phone Number"
    CREDENTIAL = "Credential"
    POLICY_STATEMENT = "Policy Statement"
    VULNERABILITY = "Vulnerability"
    SYSTEM_NAME = "System Name"
    PROJECT_CODE = "Project Code"
    OTHER_PII = "Other PII"
    GENERIC = "Generic"

class AnonymizationStrategy(str, Enum):
    REDACT = "Redact"
    REPLACE_WITH_TYPE = "Replace with Type"
    REPLACE_WITH_TOKEN = "Replace with Token"
    SYNTHESIZE = "Synthesize"
    PRESERVE = "Preserve"

class IdentifiedEntity(BaseModel):
    text: str = Field(..., description="The actual text of the entity.")
    entity_type: EntityType = Field(..., description="The classified type of the entity.")
    start_char: int = Field(..., description="The starting character index in the full text.")
    end_char: int = Field(..., description="The ending character index in the full text.")
    anonymization_strategy: AnonymizationStrategy = Field(..., description="The suggested anonymization strategy.")
    context: Optional[str] = Field(None, description="A brief context of where the entity was found.")

class EnrichedDocument(BaseModel):
    original_dom: DocumentObjectModel
    full_text: str = Field(..., description="A clean, concatenated version of all text from the document.")
    identified_entities: List[IdentifiedEntity]

    class Config:
        arbitrary_types_allowed = True
    
    semantic_graph: Optional[nx.Graph] = Field(None, description="A networkx graph of entities and their relationships.")