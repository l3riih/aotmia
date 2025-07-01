from __future__ import annotations

"""Hierarchical content chunking utilities.

The goal is to split **plain text** documents into hierarchical logical units
(headings → subheadings → paragraphs) while keeping each chunk under a
maximum token (or character) limit so it can be safely sent to an LLM.

This first implementation relies on heuristics and plain text markers. It can
later be replaced by a more sophisticated parser (e.g. using `markdown-it`) or
language-model assisted segmentation.
"""

import re
from typing import List, Dict, Any

TOKEN_APPROX_CHARS = 4  # Rough average char length of a token (English)
DEFAULT_MAX_TOKENS = 4000


class Chunk:
    """Represents a single chunk of text plus metadata."""

    def __init__(self, text: str, hierarchy_level: int, index_in_level: int):
        self.text = text.strip()
        self.hierarchy_level = hierarchy_level
        self.index_in_level = index_in_level

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "hierarchy_level": self.hierarchy_level,
            "index": self.index_in_level,
            "length": len(self.text),
        }

    def __str__(self) -> str:  # noqa: D401
        return f"<Chunk level={self.hierarchy_level} idx={self.index_in_level} len={len(self.text)}>"


# Heading detection (Markdown-style or simple enumerated headings)
_HEADING_RE = re.compile(r"^(#{1,6}|[IVXLCDM]+\.|\d+\.)\s+(.+)$", re.MULTILINE)


def _split_by_heading(text: str) -> List[str]:
    """Splits a text into sections based on heading markers."""
    if not text.strip():
        return []
    positions: list[int] = [m.start() for m in _HEADING_RE.finditer(text)]
    if not positions:
        return [text]
    chunks: list[str] = []
    positions.append(len(text))
    for i in range(len(positions) - 1):
        start = positions[i]
        end = positions[i + 1]
        section = text[start:end].strip()
        if section:
            chunks.append(section)
    return chunks


def _split_by_paragraphs(text: str) -> List[str]:
    paras = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    return paras


def approximate_token_count(text: str) -> int:
    return max(1, len(text) // TOKEN_APPROX_CHARS)


def estimate_tokens(text: str) -> int:
    """Rough token estimation (chars/4 for English)."""
    return len(text) // TOKEN_APPROX_CHARS


def chunk_text_hierarchical(text: str, max_tokens: int = DEFAULT_MAX_TOKENS, overlap_ratio: float = 0.1) -> List[Chunk]:
    """Split text into hierarchical chunks with optional overlap.
    
    Args:
        text: The text to chunk
        max_tokens: Maximum tokens per chunk
        overlap_ratio: Ratio of overlap between consecutive chunks (0.0 to 0.5)
    
    Returns:
        List of Chunk objects with sliding window context
    """
    
    # Validate overlap ratio
    overlap_ratio = max(0.0, min(0.5, overlap_ratio))
    overlap_tokens = int(max_tokens * overlap_ratio)
    
    # 1. Split by headings/sections (detect markdown-like headers)
    sections = _split_by_heading(text)
    
    all_chunks: List[Chunk] = []
    
    for section_idx, section in enumerate(sections):
        # 2. For each section, split by paragraphs if needed
        if estimate_tokens(section) <= max_tokens:
            # Small enough to be a single chunk
            chunk = Chunk(section, hierarchy_level=1, index_in_level=section_idx)
            all_chunks.append(chunk)
        else:
            # Need to split this section further with sliding window
            sub_chunks = chunk_section_with_overlap(
                section, 
                max_tokens - overlap_tokens,  # Adjust for overlap
                overlap_tokens,
                hierarchy_level=2,
                parent_idx=section_idx
            )
            all_chunks.extend(sub_chunks)
    
    return all_chunks


def chunk_section_with_overlap(section: str, max_content_tokens: int, overlap_tokens: int, 
                              hierarchy_level: int, parent_idx: int) -> List[Chunk]:
    """Split a section into smaller chunks with sliding window overlap."""
    
    paragraphs = _split_by_paragraphs(section)
    chunks: List[Chunk] = []
    
    current_text = ""
    previous_tail = ""  # Store tail of previous chunk for overlap
    chunk_idx = 0
    
    for para in paragraphs:
        para_tokens = estimate_tokens(para)
        current_tokens = estimate_tokens(current_text)
        
        # Check if adding this paragraph would exceed limit
        if current_tokens + para_tokens > max_content_tokens and current_text:
            # Create chunk with overlap from previous
            if previous_tail and chunk_idx > 0:
                chunk_text = previous_tail + "\n\n[...]\n\n" + current_text
            else:
                chunk_text = current_text
                
            chunk = Chunk(
                chunk_text,
                hierarchy_level=hierarchy_level,
                index_in_level=chunk_idx
            )
            chunks.append(chunk)
            
            # Store tail for next chunk's overlap
            previous_tail = extract_tail_for_overlap(current_text, overlap_tokens)
            
            # Start new chunk with current paragraph
            current_text = para
            chunk_idx += 1
        else:
            # Add to current chunk
            if current_text:
                current_text += "\n\n" + para
            else:
                current_text = para
    
    # Don't forget the last chunk
    if current_text:
        if previous_tail and chunk_idx > 0:
            chunk_text = previous_tail + "\n\n[...]\n\n" + current_text
        else:
            chunk_text = current_text
            
        chunk = Chunk(
            chunk_text,
            hierarchy_level=hierarchy_level,
            index_in_level=chunk_idx
        )
        chunks.append(chunk)
    
    return chunks


def extract_tail_for_overlap(text: str, target_tokens: int) -> str:
    """Extract the tail portion of text for overlap context."""
    if target_tokens <= 0:
        return ""
        
    # Split into sentences or paragraphs
    sentences = text.split('. ')
    
    # Work backwards to get approximately target_tokens
    tail_text = ""
    tokens_collected = 0
    
    for sentence in reversed(sentences):
        sentence_tokens = estimate_tokens(sentence)
        if tokens_collected + sentence_tokens <= target_tokens:
            if tail_text:
                tail_text = sentence + ". " + tail_text
            else:
                tail_text = sentence
            tokens_collected += sentence_tokens
        else:
            break
    
    # If we couldn't get enough sentences, just take the last N characters
    if tokens_collected < target_tokens // 2:
        char_count = target_tokens * TOKEN_APPROX_CHARS
        tail_text = text[-char_count:] if len(text) > char_count else text
    
    return tail_text.strip() 