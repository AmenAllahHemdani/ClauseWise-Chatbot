import re
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter





def split_by_numbers(text: str) -> List[str]:
    """
    Split the text by line-start clause numbers and lettered sub-clauses like (a).
    """
    if not text or not isinstance(text, str):
        return []

    pattern = r'\n(?:\d+(?:\.\d+)?(?:\s*-?\s*(?:\d+(?:\.\d+)?)?)?|\([a-z]\))'
    chunks = re.split(pattern, text)

    return [c.strip() for c in chunks if c.strip()]



def split_by_section(text: str) -> List[str]:
    """
    Split the text by sections.
    """
    if not text or not isinstance(text, str):
        return []

    pattern = r'(?i)\n\bsection\s+\d+\b'
    chunks = re.split(pattern, text)
    return [c.strip() for c in chunks if c.strip()]




def split_text(
    text: str,
    chunk_size: int = 200,
    chunk_overlap: int = 50,
    separators: List[str] = None
) -> List[str]:

    if not text or not isinstance(text, str):
        raise ValueError("Input 'text' must be a non-empty string")

    if separators is None:
        separators = ["\n\n", "\n", ". ", " ", ""]

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=separators,
        add_start_index=True,
    )

    chunks = text_splitter.split_text(text)

    return [chunk.strip() for chunk in chunks if chunk.strip()]




def find_numbers_count(text: str) -> int:
    """
    Find the section numbers in the text.
    """
    if not text or not isinstance(text, str):
        return 0

    pattern = r'\d+(?:\.\d+)?(?:\s*-?\s*(?:\d+(?:\.\d+)?)?)?'
    return len(re.findall(pattern, text))




def find_section_count(text: str) -> int:
    """
    Find the section numbers in the text.
    """
    if not text or not isinstance(text, str):
        return 0

    pattern = r'(?i)\bsection\s+\d+\b'
    return len(re.findall(pattern, text))