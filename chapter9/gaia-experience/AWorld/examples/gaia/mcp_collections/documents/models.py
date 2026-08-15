from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """Metadata extracted from document processing."""

    file_name: str = Field(description="Original file name")
    file_size: int = Field(description="File size in bytes")
    file_type: str = Field(description="Document file type/extension")
    absolute_path: str = Field(description="Absolute path to the document file")
    page_count: int | None = Field(default=None, description="Number of pages in document")
    processing_time: float = Field(
        description="Time taken to process the document in seconds", deprecated=True, exclude=True
    )
    extracted_images: list[str] = Field(default_factory=list, description="Paths to extracted image files")
    extracted_media: list[dict[str, str]] = Field(
        default_factory=list, description="list of extracted media files with type and path"
    )
    output_format: str = Field(description="Format of the extracted content")
    llm_enhanced: bool = Field(default=False, description="Whether LLM enhancement was used", exclude=True)
    ocr_applied: bool = Field(default=False, description="Whether OCR was applied", exclude=True)
    extracted_text_file_path: str | None = Field(
        default=None, description="Absolute path to the extracted text file (if applicable)"
    )
