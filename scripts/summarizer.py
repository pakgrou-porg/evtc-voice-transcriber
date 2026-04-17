# summarizer.py — Generates a structured JSON summary from a raw transcript
# Part of the EVTC (Easy Voice Transcription Caller) module for Agent Zero
# Uses the A0 LLM context to extract meeting details from the stitched transcript text

import json   # Used to serialize the structured summary output as JSON
import re     # Used to extract and clean speaker labels and timestamps from transcript
import os     # Used for file path operations when writing output files


# Define the expected output structure keys for the meeting summary JSON
SUMMARY_FIELDS = [
    'subject',         # The main topic or title of the meeting
    'action_items',    # List of tasks assigned to specific people with owners
    'detailed_topics', # Full breakdown of subjects discussed during the meeting
    'resourcing',      # Mentions of budget, staff, tools, or other resources discussed
    'commitments',     # Promises or agreements made by participants
]


def build_summary_prompt(transcript: str, fields: list = None) -> str:
    # Build the LLM prompt that requests a structured JSON summary from the transcript
    # transcript: the full stitched transcript text
    # fields: list of summary field names to include (defaults to all SUMMARY_FIELDS)
    # Returns a formatted prompt string ready to send to an LLM

    if fields is None:  # Use all default fields if none specified
        fields = SUMMARY_FIELDS  # Fall back to the global default field list

    # Format the field list as a bulleted list for inclusion in the prompt
    fields_text = '\n'.join(f'- {f}' for f in fields)  # One field per line with dash prefix

    # Build the prompt with clear instructions and the transcript embedded
    prompt = f"""You are a meeting analyst. Analyze the following transcript and extract key information.

Return a JSON object with these fields:
{fields_text}

Rules:
- 'action_items': list of strings in format "[Owner]: [task description]"
- 'detailed_topics': list of strings, one per major topic discussed
- 'resourcing': list of strings for budget/staff/tool mentions, empty list if none
- 'commitments': list of strings for explicit promises made, empty list if none
- 'subject': single string summarizing the main meeting topic
- Return ONLY valid JSON, no markdown, no explanation

Transcript:
{transcript}

JSON Summary:"""

    return prompt  # Return the fully built prompt string


def extract_json_from_response(response_text: str) -> dict:
    # Parse JSON from an LLM response, handling cases where the model adds extra text
    # response_text: raw string from the LLM (may include markdown or preamble)
    # Returns a parsed dict, or raises ValueError if no valid JSON is found

    # First try direct JSON parsing (ideal case — model returned clean JSON)
    try:
        return json.loads(response_text.strip())  # Direct parse of clean JSON response
    except json.JSONDecodeError:
        pass  # Fall through to extraction attempt if direct parse fails

    # Attempt to extract JSON from inside markdown code fences (```json ... ```)
    match = re.search(r'```(?:json)?\s*({.*?})\s*```', response_text, re.DOTALL)  # Match fenced block
    if match:  # If a fenced JSON block was found
        return json.loads(match.group(1))  # Parse the JSON inside the code fence

    # Attempt to extract a raw JSON object from anywhere in the response
    match = re.search(r'({.*})', response_text, re.DOTALL)  # Match any {...} block
    if match:  # If a JSON-like block was found
        return json.loads(match.group(1))  # Parse the extracted JSON object

    raise ValueError(f'No valid JSON found in response: {response_text[:200]}')  # Fail with context


def summarize(transcript: str, fields: list = None) -> dict:
    # Generate a structured JSON summary from a transcript using a simple rule-based extractor
    # This is a fallback summarizer that works without an LLM call (for testing/offline use)
    # transcript: the full stitched transcript text
    # fields: optional list of specific fields to include in the output
    # Returns a dict with 'success' bool, 'summary' dict, and 'error' str if failed

    result = {'success': False, 'summary': {}, 'error': None}  # Initialize result dict

    if not transcript or not transcript.strip():  # Validate that transcript is not empty
        result['error'] = 'Empty transcript provided — cannot generate summary'  # Empty input error
        return result  # Return failure early

    # Build a minimal summary by extracting lines that look like action items
    lines = transcript.split('\n')  # Split transcript into individual lines

    # Find lines containing action-indicator words like 'will', 'should', 'must', 'action'
    action_keywords = ['will ', 'should ', 'must ', 'action:', 'todo:', 'to do:', 'task:']  # Common patterns
    action_items = []  # List to accumulate candidate action items
    for line in lines:  # Iterate over each transcript line
        line_lower = line.lower()  # Lowercase for case-insensitive matching
        if any(kw in line_lower for kw in action_keywords):  # Check for any action keyword
            clean = line.strip()  # Remove leading/trailing whitespace
            if len(clean) > 15:  # Ignore very short lines (likely noise)
                action_items.append(clean)  # Add the line as a candidate action item

    # Extract the first non-empty line as a rough subject estimate
    subject = next((l.strip() for l in lines if len(l.strip()) > 20), 'Meeting Transcript')  # Default fallback

    # Build the structured summary dictionary with all required fields
    summary = {
        'subject': subject,                   # First meaningful line as subject
        'action_items': action_items[:10],    # Cap at 10 action items to keep output concise
        'detailed_topics': [],                # Requires LLM for accurate topic extraction
        'resourcing': [],                     # Requires LLM for resource mention detection
        'commitments': [],                    # Requires LLM for commitment identification
    }

    result['success'] = True    # Mark summarization as successful
    result['summary'] = summary  # Store the structured summary
    return result               # Return success result


def save_summary(summary: dict, output_path: str) -> dict:
    # Write the structured summary dictionary to a JSON file on disk
    # summary: the dict produced by summarize()
    # output_path: absolute path where the JSON file should be written
    # Returns a dict with 'success' bool and 'error' str if failed

    result = {'success': False, 'error': None}  # Initialize result dict

    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)  # Ensure output directory exists
        with open(output_path, 'w', encoding='utf-8') as f:  # Open file for writing with UTF-8 encoding
            json.dump(summary, f, indent=2, ensure_ascii=False)  # Write formatted JSON with 2-space indent
        result['success'] = True  # Mark file write as successful
        return result  # Return success result
    except Exception as e:
        result['error'] = f'Failed to write summary file: {str(e)}'  # Include OS error details
        return result  # Return failure result
