"""
Improved Document Parser for MOSAR Markdown Documents
Parses markdown files into Document -> Section -> Chunk hierarchy
Version 2: Robust section detection and hierarchy building
"""
import re
import hashlib
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field


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
    """Parse Markdown documents into hierarchical structure - Version 2"""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize parser

        Args:
            chunk_size: Maximum characters per chunk
            chunk_overlap: Overlap between consecutive chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Pattern for markdown headers with embedded numbers and span tags
        # Matches: # <span></span>**2 Title**, ## **2.1 Subtitle**
        self.md_header_with_number = re.compile(
            r'^(#{1,6})\s+(?:<[^>]+>)?(?:</[^>]+>)?\s*[*_]*(\d+(?:\.\d+)*)\s+([^*_\n]+?)[*_]*\s*$',
            re.MULTILINE
        )

        # Pattern for markdown headers (# Title, ## Title, etc.)
        self.md_header_pattern = re.compile(r'^(#{1,6})\s+\*?\*?(.+?)\*?\*?\s*$', re.MULTILINE)

        # Pattern for numbered sections (strict)
        # Matches: "1 Introduction", "1.2 Overview", "2.3.1 Details"
        # Must be at start of line, followed by space and title
        self.numbered_section_pattern = re.compile(
            r'^(\d+(?:\.\d+)*)\s+([A-Z][^\n]{3,100})$',
            re.MULTILINE
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
        # Clean content first
        content = self._clean_content(content)

        sections = self._extract_sections_v2(content, doc_id)

        # Build hierarchy
        sections = self._build_hierarchy(sections)

        chunks = self._create_chunks(sections, doc_id)

        print(f"  Extracted {len(sections)} sections")
        print(f"  Created {len(chunks)} chunks")

        return sections, chunks

    def _clean_content(self, content: str) -> str:
        """Clean markdown content"""
        # Remove page markers
        content = re.sub(r'\{\d+\}[-=]+', '\n', content)

        # Remove image references
        content = re.sub(r'!\[\]\([^)]+\)', '', content)

        # Remove HTML tags
        content = re.sub(r'<[^>]+>', '', content)

        # Clean up excessive whitespace but preserve structure
        content = re.sub(r'\n{4,}', '\n\n\n', content)

        return content

    def _extract_sections_v2(self, content: str, doc_id: str) -> List[Section]:
        """
        Extract sections using improved logic

        Args:
            content: Document content
            doc_id: Document identifier

        Returns:
            List of Section objects
        """
        sections = []

        # Find all potential section headers
        candidates = []

        # FIRST: Find markdown headers with embedded numbers and span tags (HIGHEST PRIORITY)
        # e.g., # <span id="page-11-0"></span>**2 Modular Spacecraft Requirements**
        for match in self.md_header_with_number.finditer(content):
            hashes = match.group(1)
            number = match.group(2)
            title = match.group(3).strip()

            # Clean title from any remaining HTML tags or markdown
            title = re.sub(r'<[^>]+>', '', title)
            title = title.strip('*_').strip()

            if len(title) < 2:
                continue

            level = number.count('.')
            candidates.append({
                'type': 'numbered_md',
                'number': number,
                'title': title,
                'level': level,
                'start_pos': match.start(),
                'end_pos': match.end(),
                'priority': 1  # Highest priority
            })

        # SECOND: Find numbered sections (e.g., "1 Introduction", "2.3 Details")
        for match in self.numbered_section_pattern.finditer(content):
            number = match.group(1)
            title = match.group(2).strip()

            # Skip if title is too short or looks like table content
            if len(title) < 5 or '|' in title or title.isdigit():
                continue

            level = number.count('.')
            candidates.append({
                'type': 'numbered',
                'number': number,
                'title': title,
                'level': level,
                'start_pos': match.start(),
                'end_pos': match.end()
            })

        # Find markdown headers (# Title, ## Title)
        for match in self.md_header_pattern.finditer(content):
            hashes = match.group(1)
            title = match.group(2).strip()

            # Skip if title is too short
            if len(title) < 3:
                continue

            level = len(hashes)
            number = f"H{level}"

            candidates.append({
                'type': 'markdown',
                'number': number,
                'title': title,
                'level': level,
                'start_pos': match.start(),
                'end_pos': match.end()
            })

        # Sort by position in document
        candidates.sort(key=lambda x: x['start_pos'])

        # Deduplicate based on position proximity (within 5 characters)
        # Keep highest priority (numbered_md > numbered > markdown)
        deduped = []
        priority_map = {'numbered_md': 1, 'numbered': 2, 'markdown': 3}

        for cand in candidates:
            # Check if there's an existing candidate at similar position
            duplicate = False
            for existing in deduped:
                if abs(existing['start_pos'] - cand['start_pos']) < 5:
                    # Found duplicate - keep higher priority
                    if priority_map.get(cand['type'], 99) < priority_map.get(existing['type'], 99):
                        deduped.remove(existing)
                        deduped.append(cand)
                    duplicate = True
                    break

            if not duplicate:
                deduped.append(cand)

        # Sort again after deduplication
        deduped.sort(key=lambda x: x['start_pos'])
        candidates = deduped

        # Create sections with content
        for i, cand in enumerate(candidates):
            # Get content between this section and next
            start = cand['end_pos']
            end = candidates[i + 1]['start_pos'] if i + 1 < len(candidates) else len(content)

            section_content = content[start:end].strip()

            # Note: Do NOT skip sections - preserve ALL sections even with no content
            # This ensures complete section hierarchy from table of contents

            section_id = self._generate_section_id(doc_id, cand['number'], i)

            section = Section(
                id=section_id,
                number=cand['number'],
                title=cand['title'],
                level=cand['level'],
                content=section_content,
                parent_number=None  # Will be set in _build_hierarchy
            )

            sections.append(section)

        return sections

    def _build_hierarchy(self, sections: List[Section]) -> List[Section]:
        """
        Build parent-child relationships between sections

        Args:
            sections: Flat list of sections

        Returns:
            Sections with parent_number set
        """
        for i, section in enumerate(sections):
            # Skip markdown headers
            if section.number.startswith('H'):
                continue

            # Find parent by looking backwards for a section with fewer dots
            current_parts = section.number.split('.')

            for j in range(i - 1, -1, -1):
                candidate = sections[j]

                # Skip markdown headers
                if candidate.number.startswith('H'):
                    continue

                candidate_parts = candidate.number.split('.')

                # Check if candidate is parent
                # Parent has one fewer level and matches prefix
                if len(candidate_parts) == len(current_parts) - 1:
                    # Check if all parent parts match
                    if all(current_parts[k] == candidate_parts[k] for k in range(len(candidate_parts))):
                        section.parent_number = candidate.number
                        break

        return sections

    def _generate_section_id(self, doc_id: str, number: str, counter: int) -> str:
        """Generate unique section ID"""
        safe_number = number.replace('.', '_')
        return f"{doc_id}_sec_{safe_number}_{counter}"

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
            if not section.content or len(section.content) < 50:
                continue

            # Split section content into chunks
            chunks = self._split_text_into_chunks(section.content)

            for idx, chunk_text in enumerate(chunks):
                chunk_id = f"{doc_id}_chunk_{chunk_counter}"
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
                sentence_end = self._find_sentence_boundary(text, end)
                if sentence_end > start:
                    end = sentence_end

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start with overlap
            start = end - self.chunk_overlap if end < len(text) else end

        return chunks

    def _find_sentence_boundary(self, text: str, position: int) -> int:
        """Find nearest sentence boundary"""
        window = 100
        search_start = max(0, position - window)
        search_end = min(len(text), position + window)
        search_text = text[search_start:search_end]

        # Look for sentence endings
        for separator in ['. ', '.\n', '! ', '!\n', '? ', '?\n']:
            idx = search_text.rfind(separator)
            if idx != -1:
                return search_start + idx + len(separator)

        return position


def clean_markdown(content: str) -> str:
    """
    Clean markdown content

    Args:
        content: Raw markdown content

    Returns:
        Cleaned content
    """
    # Remove page markers
    content = re.sub(r'\{\d+\}[-=]+', '\n', content)

    # Remove excessive whitespace
    content = re.sub(r'\n{3,}', '\n\n', content)

    # Remove image references
    content = re.sub(r'!\[\]\([^)]+\)', '', content)

    return content.strip()
