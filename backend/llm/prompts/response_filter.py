"""
Response filtering utilities to provide ChatGPT-like clean responses

Extracted from Local-LLM project (backend/local_llm_staging/backend/response_filter.py).

This module provides utilities for filtering thinking/reasoning content from
model responses, particularly useful for reasoning models like Deepseek R1.
"""

import re
from typing import Optional


def filter_thinking_content(content: str, _recursion_depth: int = 0) -> str:
    """
    Filter out thinking/reasoning content from model responses to provide
    ChatGPT-like clean responses.
    
    Reasoning models (like Deepseek R1) often output their thinking process
    before the actual answer. This function detects and removes common
    thinking patterns while preserving the actual answer.
    
    Extracted from Local-LLM project.
    
    Args:
        content: Raw model response that may contain thinking content
        _recursion_depth: Internal parameter to prevent infinite recursion
        
    Returns:
        Cleaned response with thinking content removed
    """
    if not content:
        return content
    
    # Prevent infinite recursion
    if _recursion_depth > 2:
        return content
    
    # Patterns that indicate thinking/reasoning (more specific)
    thinking_patterns = [
        r'^(Alright|Okay),?\s+(the user|they|I)',
        r'^(Let me|I need to|I should|I\'ll|I will)\s+(think|consider|figure|determine)',
        r'^(Looking|Checking|Considering)\s+(back|at|the)',
        r'^(The user|They|This|That)\s+(just|must|probably|likely)\s+',
        r'^(First|Second|Third|Next|Then|After that),?\s+(I|let me|I\'ll)',
        r'^(Keeping|Making|Ensuring)\s+it\s+',
        r'^I\'m\s+(going|trying)\s+to\s+',
    ]
    
    # Patterns that indicate the start of actual answer
    answer_markers = [
        r'^(Hello|Hi|Hey|Greetings)',
        r'^(The|A|An|In|For|To|When|Where|What|How|Why)\s+[A-Z]',
        r'^[A-Z][a-z]+\s+(is|are|was|were|can|will|should|would|means|refers)',
        r'^(Here\'s|Here is|Here are)',
        r'^(Let me|I\'ll)\s+(explain|tell|show|help|answer)',
        r'^[A-Z][a-z]+,\s+',  # Direct address like "Paris,"
    ]
    
    # Preserve newlines and structure - split by paragraphs first
    paragraphs = content.split('\n\n')
    
    # Process each paragraph separately to preserve structure
    cleaned_paragraphs = []
    found_answer_start = False
    
    for paragraph in paragraphs:
        if not paragraph.strip():
            # Preserve empty lines for structure
            if found_answer_start:
                cleaned_paragraphs.append('')
            continue
        
        # Split paragraph into sentences for analysis
        sentences = re.split(r'([.!?]\s+)', paragraph)
        sentences = [sentences[i] + (sentences[i+1] if i+1 < len(sentences) else '') 
                     for i in range(0, len(sentences), 2) if sentences[i].strip()]
        
        if not sentences:
            if found_answer_start:
                cleaned_paragraphs.append(paragraph)
            continue
        
        paragraph_cleaned_sentences = []
        paragraph_has_answer = False
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Check if this sentence is thinking content
            is_thinking = False
            for pattern in thinking_patterns:
                if re.match(pattern, sentence, re.IGNORECASE):
                    is_thinking = True
                    break
            
            # Check if this sentence starts the actual answer
            is_answer_start = False
            for pattern in answer_markers:
                if re.match(pattern, sentence, re.IGNORECASE):
                    is_answer_start = True
                    paragraph_has_answer = True
                    found_answer_start = True
                    break
            
            # Once we find the answer start, include everything
            if found_answer_start:
                paragraph_cleaned_sentences.append(sentence)
            elif is_answer_start:
                paragraph_cleaned_sentences.append(sentence)
                paragraph_has_answer = True
                found_answer_start = True
            elif not is_thinking and not found_answer_start:
                # Not thinking and haven't found answer yet - might be answer
                if len(sentence) > 10:  # Substantial content
                    paragraph_cleaned_sentences.append(sentence)
                    paragraph_has_answer = True
                    found_answer_start = True
        
        # If paragraph has answer content, add it (preserving structure)
        if found_answer_start or paragraph_has_answer:
            cleaned_paragraph = ' '.join(paragraph_cleaned_sentences).strip()
            if cleaned_paragraph:
                cleaned_paragraphs.append(cleaned_paragraph)
    
    # Join paragraphs with double newlines to preserve structure
    result = '\n\n'.join(cleaned_paragraphs).strip()
    
    # If we removed everything or result is too short, try extraction method
    # Pass recursion depth to prevent infinite loops
    if not result or (len(result) < len(content) * 0.2 and len(content) > 50):
        return extract_final_answer(content, None, _recursion_depth + 1)
    
    # Additional cleanup: remove common thinking prefixes from remaining text
    thinking_prefixes = [
        r'^Alright,?\s+',
        r'^Okay,?\s+',
        r'^So,?\s+',
        r'^Now,?\s+',
    ]
    
    for prefix in thinking_prefixes:
        result = re.sub(prefix, '', result, flags=re.IGNORECASE)
    
    return result.strip()


def extract_final_answer(content: str, model_id: Optional[str] = None, _recursion_depth: int = 0) -> str:
    """
    Extract the final answer from a response, handling various formats.
    
    This is a more aggressive filter that tries to find the actual answer
    portion of the response, especially for reasoning models.
    
    Extracted from Local-LLM project.
    
    Args:
        content: Raw model response
        model_id: Optional model ID to apply model-specific extraction
        _recursion_depth: Internal parameter to prevent infinite recursion
        
    Returns:
        Extracted final answer
    """
    if not content:
        return content
    
    # Prevent infinite recursion - don't call back to filter_thinking_content
    if _recursion_depth > 2:
        return content
    
    # For Deepseek R1 and similar reasoning models, look for answer after thinking
    # Common pattern: thinking sentences, then a clear answer marker
    
    # Try to find answer after common separators
    separators = [
        r'\n\n+',  # Double newlines
        r'\.\s+(Hello|Hi|The|Here\'s|Here is)',
        r'\.\s+[A-Z][a-z]+ (is|are|was|were)',
    ]
    
    for sep in separators:
        parts = re.split(sep, content, maxsplit=1)
        if len(parts) > 1:
            # Found a separator, take the part after it
            potential_answer = parts[-1].strip()
            if len(potential_answer) > 20:  # Reasonable answer length
                return potential_answer
    
    # Fallback: return original content instead of calling filter_thinking_content
    # This breaks the circular recursion
    return content
