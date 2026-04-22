# test_summarizer.py — Unit tests for the EVTC summarizer helper module
# Tests: build_summary_prompt, extract_json_from_response, summarize, save_summary

import os  # File path operations for test assertions
import json  # JSON parsing for verifying saved files
import pytest  # Test framework for exception assertions

from helpers.summarizer import (  # Functions under test
    SUMMARY_FIELDS,  # Default field list constant
    build_summary_prompt,  # Prompt builder
    extract_json_from_response,  # JSON extractor
    summarize,  # Rule-based summarizer
    save_summary,  # File writer
)


class TestBuildSummaryPrompt:
    """Tests for the build_summary_prompt() function."""

    def test_prompt_contains_transcript(self):
        """Verify the generated prompt includes the transcript text."""
        transcript = 'This is a test meeting transcript about project updates.'  # Sample text
        prompt = build_summary_prompt(transcript)  # Build prompt with default fields
        assert transcript in prompt  # Transcript text must appear in the prompt

    def test_prompt_contains_default_fields(self):
        """Verify all default SUMMARY_FIELDS appear in the prompt."""
        prompt = build_summary_prompt('Some transcript text.')  # Build with defaults
        for field in SUMMARY_FIELDS:  # Check each expected field
            assert field in prompt  # Field name must be in the prompt

    def test_prompt_uses_custom_fields(self):
        """Verify custom fields are used when provided."""
        custom_fields = ['topic', 'decisions']  # Custom field list
        prompt = build_summary_prompt('Transcript.', fields=custom_fields)  # Build with custom
        assert 'topic' in prompt  # Custom field must appear
        assert 'decisions' in prompt  # Custom field must appear
        # Default fields not in custom list should not appear (unless in transcript text)
        # We check the fields section specifically
        assert '- topic' in prompt  # Must appear as formatted list item
        assert '- decisions' in prompt  # Must appear as formatted list item

    def test_prompt_returns_string(self):
        """Verify build_summary_prompt returns a string."""
        result = build_summary_prompt('Test.')  # Call the function
        assert isinstance(result, str)  # Must return a string

    def test_prompt_is_nonempty(self):
        """Verify the prompt is not empty."""
        result = build_summary_prompt('Test transcript.')  # Build prompt
        assert len(result) > 0  # Must not be empty


class TestExtractJsonFromResponse:
    """Tests for the extract_json_from_response() function."""

    def test_clean_json_response(self):
        """Verify parsing of a clean JSON string."""
        raw = '{"subject": "Test Meeting", "action_items": []}'  # Clean JSON
        result = extract_json_from_response(raw)  # Parse it
        assert result['subject'] == 'Test Meeting'  # Must parse correctly
        assert result['action_items'] == []  # Must parse list

    def test_markdown_wrapped_json(self):
        """Verify parsing of JSON wrapped in markdown code fences."""
        raw = 'Here is the summary:\n```json\n{"subject": "Budget Review", "action_items": ["Review Q3"]}\n```'  # Fenced JSON
        result = extract_json_from_response(raw)  # Parse from markdown
        assert result['subject'] == 'Budget Review'  # Must extract correctly
        assert len(result['action_items']) == 1  # Must have one item

    def test_json_with_preamble(self):
        """Verify parsing of JSON embedded in surrounding text."""
        raw = 'Sure, here is the result: {"subject": "Sprint Planning"} Hope this helps!'  # JSON in text
        result = extract_json_from_response(raw)  # Parse from mixed text
        assert result['subject'] == 'Sprint Planning'  # Must extract correctly

    def test_invalid_text_raises_value_error(self):
        """Verify ValueError is raised when no valid JSON is found."""
        with pytest.raises(ValueError):  # Must raise ValueError
            extract_json_from_response('This has no JSON at all.')  # No JSON content

    def test_empty_string_raises_value_error(self):
        """Verify ValueError is raised for empty string input."""
        with pytest.raises(ValueError):  # Must raise ValueError
            extract_json_from_response('')  # Empty input

    def test_code_fence_without_json_label(self):
        """Verify parsing of code fence without the json language label."""
        raw = '```\n{"subject": "Unlabeled Fence"}\n```'  # Code fence without json label
        result = extract_json_from_response(raw)  # Parse it
        assert result['subject'] == 'Unlabeled Fence'  # Must extract correctly


class TestSummarize:
    """Tests for the summarize() function."""

    def test_empty_transcript_returns_error(self):
        """Verify summarize returns error for empty transcript."""
        result = summarize('')  # Empty transcript
        assert result['success'] is False  # Must fail
        assert 'Empty transcript' in result['error']  # Error mentions empty input

    def test_whitespace_only_transcript_returns_error(self):
        """Verify summarize returns error for whitespace-only transcript."""
        result = summarize('   \n\t  ')  # Only whitespace
        assert result['success'] is False  # Must fail
        assert 'Empty transcript' in result['error']  # Error mentions empty input

    def test_valid_transcript_returns_summary(self):
        """Verify summarize returns a valid summary dict for real text."""
        transcript = 'We will review the Q3 budget next week. John should prepare the slides.'  # Sample text
        result = summarize(transcript)  # Summarize it
        assert result['success'] is True  # Must succeed
        assert isinstance(result['summary'], dict)  # Summary must be a dict

    def test_summary_contains_expected_keys(self):
        """Verify the summary dict contains all SUMMARY_FIELDS keys."""
        transcript = 'The team will implement the new feature by Friday. Action: deploy staging.'  # Sample
        result = summarize(transcript)  # Summarize it
        assert result['success'] is True  # Must succeed
        for field in SUMMARY_FIELDS:  # Check each expected field
            assert field in result['summary']  # Field must be present in summary

    def test_action_items_extracted(self):
        """Verify action-like lines are detected in the transcript."""
        transcript = 'Alice will complete the report.\nBob should review the code by Monday.'  # Action keywords
        result = summarize(transcript)  # Summarize it
        assert result['success'] is True  # Must succeed
        assert len(result['summary']['action_items']) > 0  # Should find action items

    def test_result_dict_structure(self):
        """Verify summarize returns dict with expected keys."""
        result = summarize('')  # Any call
        assert 'success' in result  # Must have success key
        assert 'summary' in result  # Must have summary key
        assert 'error' in result  # Must have error key


class TestSaveSummary:
    """Tests for the save_summary() function."""

    def test_writes_valid_json_file(self, tmp_dir):
        """Verify save_summary writes a valid JSON file to disk."""
        summary = {'subject': 'Test', 'action_items': ['Do stuff']}  # Sample summary
        output_path = os.path.join(tmp_dir, 'summary.json')  # Output path
        result = save_summary(summary, output_path)  # Write it
        assert result['success'] is True  # Must succeed
        assert os.path.exists(output_path)  # File must exist
        with open(output_path, 'r', encoding='utf-8') as f:  # Read it back
            loaded = json.load(f)  # Parse JSON
        assert loaded['subject'] == 'Test'  # Content must match
        assert loaded['action_items'] == ['Do stuff']  # List must match

    def test_creates_parent_directory(self, tmp_dir):
        """Verify save_summary creates parent directories if needed."""
        nested_path = os.path.join(tmp_dir, 'sub', 'dir', 'summary.json')  # Nested path
        result = save_summary({'subject': 'Nested'}, nested_path)  # Write to nested path
        assert result['success'] is True  # Must succeed
        assert os.path.exists(nested_path)  # File must exist in nested dir

    def test_result_dict_structure(self, tmp_dir):
        """Verify save_summary returns dict with expected keys."""
        output_path = os.path.join(tmp_dir, 'summary.json')  # Output path
        result = save_summary({}, output_path)  # Any call
        assert 'success' in result  # Must have success key
        assert 'error' in result  # Must have error key

    def test_write_failure_returns_error(self):
        """Verify save_summary returns error when write fails."""
        result = save_summary({'test': True}, '/proc/nonexistent/summary.json')  # Invalid path
        assert result['success'] is False  # Must fail
        assert result['error'] is not None  # Error must be set
