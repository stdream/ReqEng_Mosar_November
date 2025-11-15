"""
Document Parser for MOSAR Markdown Documents
Parses markdown files into Document -> Section -> Chunk hierarchy
"""
import re
import hashlib
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Section:
    """Represents a document section"""
    id: str
    number: str
    title: str
    level: int
    content: str
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    parent_number: Optional[str] = None


@dataclass
class Chunk:
    """Represents a text chunk"""
    id: str
    text: str
    section_id: str
    order: int


class MarkdownDocumentParser:
    """Parse Markdown documents into hierarchical structure"""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize parser

        Args:
            chunk_size: Maximum characters per chunk
            chunk_overlap: Overlap between consecutive chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Pattern to match markdown headers
        # Matches: # Title, ## Title, ### Title, etc.
        self.header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)

        # Pattern to match numbered sections
        # Matches: 1., 1.1, 2.3.4, etc.
        self.section_number_pattern = re.compile(
            r'^(\d+(?:\.\d+)*\.?)\s+(.+)$'
        )

    def parse_document(
        self,
        content: str,
        doc_id: str,
        doc_title: str
    ) -> Tuple[List[Section], List[Chunk]]:
        """
        Parse document content into sections and chunks

        Args:
            content: Document content (markdown)
            doc_id: Document identifier
            doc_title: Document title

        Returns:
            Tuple of (sections list, chunks list)
        """
        sections = self._extract_sections(content, doc_id)
        chunks = self._create_chunks(sections, doc_id)

        print(f"  Extracted {len(sections)} sections")
        print(f"  Created {len(chunks)} chunks")

        return sections, chunks

    def _extract_sections(self, content: str, doc_id: str) -> List[Section]:
        """
        Extract hierarchical sections from content

        Args:
            content: Document content
            doc_id: Document identifier

        Returns:
            List of Section objects
        """
        sections = []
        lines = content.split('\n')

        current_section = None
        section_content = []
        section_counter = 0

        for line in lines:
            # Check if line is a header or numbered section
            section_match = self._match_section_header(line)

            if section_match:
                # Save previous section
                if current_section:
                    current_section.content = '\n'.join(section_content).strip()
                    sections.append(current_section)

                # Start new section
                number, title, level = section_match
                section_id = self._generate_section_id(doc_id, number, section_counter)

                current_section = Section(
                    id=section_id,
                    number=number,
                    title=title,
                    level=level,
                    content='',
                    parent_number=self._get_parent_number(number)
                )
                section_content = []
                section_counter += 1
            else:
                # Add to current section content
                if current_section:
                    section_content.append(line)

        # Save last section
        if current_section:
            current_section.content = '\n'.join(section_content).strip()
            sections.append(current_section)

        return sections

    def _match_section_header(self, line: str) -> Optional[Tuple[str, str, int]]:
        """
        Match section header patterns

        Args:
            line: Line of text

        Returns:
            Tuple of (number, title, level) or None
        """
        # Try numbered section pattern (e.g., "1.2.3 Title")
        match = self.section_number_pattern.match(line.strip())
        if match:
            number = match.group(1)
            title = match.group(2).strip()
            level = number.count('.') if '.' in number else 0
            return (number, title, level)

        # Try markdown header pattern (e.g., "## Title")
        match = self.header_pattern.match(line.strip())
        if match:
            hashes = match.group(1)
            title = match.group(2).strip()
            level = len(hashes)
            # Generate a pseudo section number based on header level
            number = f"H{level}"
            return (number, title, level)

        return None

    def _get_parent_number(self, section_number: str) -> Optional[str]:
        """
        Get parent section number

        Args:
            section_number: Current section number (e.g., "2.3.1")

        Returns:
            Parent section number (e.g., "2.3") or None
        """
        if section_number.startswith('H'):
            return None

        parts = section_number.rstrip('.').split('.')
        if len(parts) <= 1:
            return None

        return '.'.join(parts[:-1])

    def _generate_section_id(self, doc_id: str, number: str, counter: int) -> str:
        """
        Generate unique section ID

        Args:
            doc_id: Document ID
            number: Section number
            counter: Section counter

        Returns:
            Unique section ID
        """
        return f"{doc_id}_section_{number.replace('.', '_')}_{counter}"

    def _create_chunks(self, sections: List[Section], doc_id: str) -> List[Chunk]:
        """
        Create chunks from sections

        Args:
            sections: List of sections
            doc_id: Document ID

        Returns:
            List of Chunk objects
        """
        all_chunks = []
        chunk_counter = 0

        for section in sections:
            if not section.content:
                continue

            # Split section content into chunks
            chunks = self._split_text_into_chunks(section.content)

            for idx, chunk_text in enumerate(chunks):
                chunk_id = self._generate_chunk_id(doc_id, section.id, chunk_counter)
                chunk = Chunk(
                    id=chunk_id,
                    text=chunk_text,
                    section_id=section.id,
                    order=idx
                )
                all_chunks.append(chunk)
                chunk_counter += 1

        return all_chunks

    def _split_text_into_chunks(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks

        Args:
            text: Text to split

        Returns:
            List of text chunks
        """
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings
                sentence_end = self._find_sentence_boundary(text, end)
                if sentence_end > start:
                    end = sentence_end

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start position with overlap
            start = end - self.chunk_overlap if end < len(text) else end

        return chunks

    def _find_sentence_boundary(self, text: str, position: int) -> int:
        """
        Find nearest sentence boundary near position

        Args:
            text: Text to search
            position: Target position

        Returns:
            Position of sentence boundary
        """
        # Look for sentence endings within a window
        window = 100
        search_start = max(0, position - window)
        search_end = min(len(text), position + window)
        search_text = text[search_start:search_end]

        # Find sentence endings (., !, ?, etc.)
        for separator in ['. ', '.\n', '! ', '!\n', '? ', '?\n']:
            idx = search_text.rfind(separator)
            if idx != -1:
                return search_start + idx + len(separator)

        # If no sentence boundary found, return original position
        return position

    def _generate_chunk_id(self, doc_id: str, section_id: str, counter: int) -> str:
        """
        Generate unique chunk ID

        Args:
            doc_id: Document ID
            section_id: Section ID
            counter: Chunk counter

        Returns:
            Unique chunk ID
        """
        return f"{doc_id}_chunk_{counter}"


def extract_page_markers(content: str) -> Dict[int, int]:
    """
    Extract page markers from document content

    Args:
        content: Document content with page markers like {0}----, {1}----

    Returns:
        Dictionary mapping page number to character position
    """
    page_markers = {}
    pattern = re.compile(r'\{(\d+)\}[-]+')

    for match in pattern.finditer(content):
        page_num = int(match.group(1))
        position = match.start()
        page_markers[page_num] = position

    return page_markers


def clean_markdown(content: str) -> str:
    """
    Clean markdown content

    Args:
        content: Raw markdown content

    Returns:
        Cleaned content
    """
    # Remove page markers
    content = re.sub(r'\{\d+\}[-]+', '', content)

    # Remove excessive whitespace
    content = re.sub(r'\n{3,}', '\n\n', content)

    # Remove image references
    content = re.sub(r'!\[\]\([^)]+\)', '', content)

    return content.strip()
