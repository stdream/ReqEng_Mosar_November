"""
Document Parser V3 - Complete Section Hierarchy Preservation
Ensures ALL sections from table of contents are captured, even with no content
"""
import re
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
    """Parse Markdown documents - V3: Complete hierarchy preservation"""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Pattern for markdown headers with embedded numbers
        # Matches: # **2 Title**, ## **2.1 Subtitle**, # <span></span>**2 Title**
        self.md_header_with_number = re.compile(
            r'^(#{1,6})\s+(?:<[^>]+>)?(?:</[^>]+>)?\s*[*_]*(\d+(?:\.\d+)*)\s+([^*_\n]+?)[*_]*\s*$',
            re.MULTILINE
        )

        # Pattern for standalone numbered sections
        self.standalone_number = re.compile(
            r'^(\d+(?:\.\d+)*)\s+([A-Z][^\n]{3,100})$',
            re.MULTILINE
        )

        # Pattern for markdown headers without numbers
        self.md_header_plain = re.compile(
            r'^(#{1,6})\s+(?:<[^>]+>)?[*_]*(.+?)[*_]*\s*(?:</[^>]+>)?\s*$',
            re.MULTILINE
        )

    def parse_document(
        self,
        content: str,
        doc_id: str,
        doc_title: str
    ) -> Tuple[List[Section], List[Chunk]]:
        """Parse document into sections and chunks"""
        content = self._clean_content(content)
        sections = self._extract_all_sections(content, doc_id)
        sections = self._build_hierarchy(sections)
        sections = self._assign_content(sections, content)
        chunks = self._create_chunks(sections, doc_id)

        print(f"  Extracted {len(sections)} sections")
        print(f"  Created {len(chunks)} chunks")

        return sections, chunks

    def _clean_content(self, content: str) -> str:
        """Clean markdown content"""
        content = re.sub(r'\{\d+\}[-=]+', '\n', content)
        content = re.sub(r'!\[\]\([^)]+\)', '', content)
        content = re.sub(r'\n{4,}', '\n\n\n', content)
        return content

    def _extract_all_sections(self, content: str, doc_id: str) -> List[Section]:
        """Extract ALL section headers, regardless of content length"""
        candidates = []

        # 1. Find markdown headers with embedded numbers: # **2.1 Title**
        for match in self.md_header_with_number.finditer(content):
            hashes = match.group(1)
            number = match.group(2)
            title = match.group(3).strip()

            # Clean title from HTML tags
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

        # 2. Find standalone numbered sections: 2.1 Title
        for match in self.standalone_number.finditer(content):
            number = match.group(1)
            title = match.group(2).strip()

            if '|' in title or len(title) < 5:
                continue

            level = number.count('.')

            # Avoid duplicates
            if not any(c['number'] == number and c['start_pos'] == match.start()
                      for c in candidates):
                candidates.append({
                    'type': 'numbered',
                    'number': number,
                    'title': title,
                    'level': level,
                    'start_pos': match.start(),
                    'end_pos': match.end(),
                    'priority': 2
                })

        # 3. Find plain markdown headers (as fallback): # Title
        for match in self.md_header_plain.finditer(content):
            hashes = match.group(1)
            title = match.group(2).strip()

            # Clean title
            title = re.sub(r'<[^>]+>', '', title)
            title = title.strip('*_').strip()

            if len(title) < 3:
                continue

            # Skip if this position already has a numbered section
            if any(abs(c['start_pos'] - match.start()) < 10 for c in candidates):
                continue

            level = len(hashes)
            number = f"H{level}"

            candidates.append({
                'type': 'markdown',
                'number': number,
                'title': title,
                'level': level,
                'start_pos': match.start(),
                'end_pos': match.end(),
                'priority': 3  # Lowest priority
            })

        # Sort by position
        candidates.sort(key=lambda x: (x['start_pos'], x['priority']))

        # Remove duplicates (same position, keep highest priority)
        unique_candidates = []
        last_pos = -100
        for cand in candidates:
            if cand['start_pos'] - last_pos > 5:  # At least 5 chars apart
                unique_candidates.append(cand)
                last_pos = cand['start_pos']

        # Create Section objects (ALL of them, no skipping)
        sections = []
        for i, cand in enumerate(unique_candidates):
            section_id = self._generate_section_id(doc_id, cand['number'], i)

            section = Section(
                id=section_id,
                number=cand['number'],
                title=cand['title'],
                level=cand['level'],
                content='',  # Will be filled later
                parent_number=None  # Will be set in _build_hierarchy
            )
            sections.append(section)

        return sections

    def _build_hierarchy(self, sections: List[Section]) -> List[Section]:
        """Build parent-child relationships"""
        for i, section in enumerate(sections):
            if section.number.startswith('H'):
                continue

            current_parts = section.number.split('.')

            # Find parent
            for j in range(i - 1, -1, -1):
                candidate = sections[j]

                if candidate.number.startswith('H'):
                    continue

                candidate_parts = candidate.number.split('.')

                # Check if candidate is immediate parent
                if len(candidate_parts) == len(current_parts) - 1:
                    # Verify prefix match
                    if all(current_parts[k] == candidate_parts[k]
                          for k in range(len(candidate_parts))):
                        section.parent_number = candidate.number
                        break

        return sections

    def _assign_content(self, sections: List[Section], content: str) -> List[Section]:
        """Assign content to sections based on position"""
        # Create position map
        section_positions = []
        for section in sections:
            # Find section header in content
            # Search for the section number in the text
            patterns = [
                rf'#{{{1,6}}}\s+[*_]*{re.escape(section.number)}\s+{re.escape(section.title)}',
                rf'^{re.escape(section.number)}\s+{re.escape(section.title)}',
            ]

            pos = -1
            for pattern in patterns:
                matches = list(re.finditer(pattern, content, re.MULTILINE))
                if matches:
                    pos = matches[0].end()
                    break

            section_positions.append((section, pos))

        # Sort by position
        section_positions.sort(key=lambda x: x[1] if x[1] >= 0 else float('inf'))

        # Assign content ranges
        for i, (section, start_pos) in enumerate(section_positions):
            if start_pos < 0:
                section.content = ''
                continue

            # Find end position (next section or end of doc)
            if i + 1 < len(section_positions):
                next_pos = section_positions[i + 1][1]
                end_pos = next_pos if next_pos > start_pos else len(content)
            else:
                end_pos = len(content)

            section.content = content[start_pos:end_pos].strip()

        return sections

    def _generate_section_id(self, doc_id: str, number: str, counter: int) -> str:
        """Generate unique section ID"""
        safe_number = number.replace('.', '_')
        return f"{doc_id}_sec_{safe_number}_{counter}"

    def _create_chunks(self, sections: List[Section], doc_id: str) -> List[Chunk]:
        """Create chunks from sections"""
        all_chunks = []
        chunk_counter = 0

        for section in sections:
            # Skip sections with very short content
            if not section.content or len(section.content) < 50:
                continue

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
        """Split text into overlapping chunks"""
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            if end < len(text):
                sentence_end = self._find_sentence_boundary(text, end)
                if sentence_end > start:
                    end = sentence_end

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end - self.chunk_overlap if end < len(text) else end

        return chunks

    def _find_sentence_boundary(self, text: str, position: int) -> int:
        """Find nearest sentence boundary"""
        window = 100
        search_start = max(0, position - window)
        search_end = min(len(text), position + window)
        search_text = text[search_start:search_end]

        for separator in ['. ', '.\n', '! ', '!\n', '? ', '?\n']:
            idx = search_text.rfind(separator)
            if idx != -1:
                return search_start + idx + len(separator)

        return position


def clean_markdown(content: str) -> str:
    """Clean markdown content"""
    content = re.sub(r'\{\d+\}[-=]+', '\n', content)
    content = re.sub(r'\n{3,}', '\n\n', content)
    content = re.sub(r'!\[\]\([^)]+\)', '', content)
    return content.strip()
