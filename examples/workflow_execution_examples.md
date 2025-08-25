# Enhanced Workflow Execution Examples

## Simple Text Processing Workflow

### Upload Workflow
```bash
curl -X POST http://localhost:8000/api/workflows-enhanced/ \
  -H "Content-Type: application/json" \
  -d @examples/simple_executable_workflow.json
```

### Execute Workflow
```bash
curl -X POST http://localhost:8000/api/workflows-enhanced/simple-executable-workflow/execute \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "input_text": "This is a sample text for analysis. It contains multiple sentences and should provide good data for sentiment analysis and summarization."
    },
    "debug": true,
    "dry_run": false
  }'
```

### Expected Response
```json
{
  "execution_id": "exec_123456789",
  "workflow_id": "simple-executable-workflow",
  "status": "completed",
  "output": {
    "analysis_report": "Text Analysis Report:\nSummary: Sample text discussing analysis with multiple sentences\nWord Count: 23\nSentiment: neutral"
  },
  "node_results": {
    "text_processor": {
      "text_summary": "Sample text discussing analysis with multiple sentences",
      "word_count": 23,
      "text_sentiment": "neutral"
    },
    "result_formatter": {
      "analysis_report": "Text Analysis Report:\nSummary: Sample text discussing analysis with multiple sentences\nWord Count: 23\nSentiment: neutral"
    }
  },
  "started_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:30:15Z",
  "tokens_used": 245,
  "cost_usd": 0.023,
  "api_calls_made": 2
}
```

## File and Email Processing Workflow

### Upload Workflow
```bash
curl -X POST http://localhost:8000/api/workflows-enhanced/ \
  -H "Content-Type: application/json" \
  -d @examples/file_email_workflow.json
```

### Execute Workflow
```bash
curl -X POST http://localhost:8000/api/workflows-enhanced/file-email-workflow/execute \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "directory_path": "/path/to/your/text/files",
      "file_extensions": [".txt", ".md", ".log"],
      "recipient_email": "josh.walton@capitalone.com",
      "report_date": "2024-01-15"
    },
    "debug": true,
    "dry_run": false
  }'
```

### Alternative Test Input (Minimal)
```bash
curl -X POST http://localhost:8000/api/workflows-enhanced/file-email-workflow/execute \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "directory_path": ".",
      "recipient_email": "test@example.com"
    }
  }'
```

## Execution Options

### Dry Run (Test Without Execution)
```json
{
  "input": {
    "input_text": "Test text"
  },
  "dry_run": true,
  "debug": true
}
```

### With Runtime Overrides
```json
{
  "input": {
    "input_text": "Test text"
  },
  "overrides": {
    "global": {
      "max_execution_time": 60000,
      "max_total_tokens": 1000
    },
    "nodes": {
      "text_processor": {
        "timeout": 30000,
        "instructions_append": "Be extra detailed in your analysis."
      }
    }
  }
}
```

### With Checkpoint Resume
```json
{
  "input": {
    "input_text": "Test text"
  },
  "checkpoint_id": "checkpoint_abc123"
}
```

## Variable Requirements

### Simple Workflow Variables
- **input_text** (required): String between 1-5000 characters

### File-Email Workflow Variables  
- **directory_path** (required): Valid file system path
- **recipient_email** (required): Valid email address format
- **file_extensions** (optional): Array of file extensions (defaults to [".txt", ".md", ".log"])
- **report_date** (optional): Date string for report

## Common Error Scenarios and Fixes

### Missing Required Input
```json
// ❌ Error Response
{
  "detail": "Input validation failed: Required variable 'input_text' is missing"
}

// ✅ Correct Request
{
  "input": {
    "input_text": "Your text here"
  }
}
```

### Invalid Email Format
```json
// ❌ Error Response  
{
  "detail": "Input validation failed: Variable 'recipient_email' must match email pattern"
}

// ✅ Correct Request
{
  "input": {
    "recipient_email": "valid@example.com"
  }
}
```

### Agent Not Found
```json
// ❌ Error Response
{
  "detail": "Agent 'file-agent' not found"
}

// ✅ Solution: Update agent_id in workflow or create the required agent
```

## Testing Node Individually

You can test individual nodes before executing the full workflow:

```bash
curl -X POST http://localhost:8000/api/workflows-enhanced/simple-executable-workflow/nodes/text_processor/execute \
  -H "Content-Type: application/json" \
  -d '{
    "text_to_analyze": "Test text for individual node execution"
  }'
```

## Workflow Validation

Validate your workflow before execution:

```bash
curl -X POST http://localhost:8000/api/workflows-enhanced/validate \
  -H "Content-Type: application/json" \
  -d @examples/simple_executable_workflow.json
```

## Debugging Tips

1. **Use debug: true** - Provides detailed execution information
2. **Start with dry_run: true** - Validates without executing
3. **Test individual nodes** - Isolate issues to specific components  
4. **Check variable validation** - Ensure all required inputs are provided
5. **Verify agent IDs** - Make sure referenced agents exist in the system