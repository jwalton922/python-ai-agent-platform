# 🚀 Execute Enhanced Workflow - Step by Step Guide

## ✅ Working Example Ready to Execute

I've created a working enhanced workflow using your **actual agents**:
- **File Agent**: `8bb72460-0221-4d9c-874b-0c2c241e0a00`
- **Email Agent**: `a214418f-9621-4c25-ac4a-c5e9d0f4a46a`

## 📋 Step 1: Upload the Workflow

```bash
curl -X POST http://localhost:8000/api/workflows-enhanced/ \
  -H "Content-Type: application/json" \
  -d @examples/working_file_email_workflow.json
```

**Expected Response:**
```json
{
  "id": "working-file-email-workflow",
  "name": "Working File and Email Workflow",
  "status": "idle",
  ...
}
```

## 🎯 Step 2: Execute the Workflow

### Option A: Basic Execution
```bash
curl -X POST http://localhost:8000/api/workflows-enhanced/working-file-email-workflow/execute \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "directory_path": ".",
      "recipient_email": "josh.walton@capitalone.com"
    },
    "debug": true
  }'
```

### Option B: Test with Different Directory
```bash
curl -X POST http://localhost:8000/api/workflows-enhanced/working-file-email-workflow/execute \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "directory_path": "/path/to/your/files",
      "recipient_email": "your-email@example.com"
    },
    "debug": true
  }'
```

### Option C: Dry Run (Test Without Execution)
```bash
curl -X POST http://localhost:8000/api/workflows-enhanced/working-file-email-workflow/execute \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "directory_path": ".",
      "recipient_email": "test@example.com"
    },
    "dry_run": true,
    "debug": true
  }'
```

## 📊 Expected Execution Flow

1. **File Agent Node** (`file_agent_node`):
   - Scans the specified directory
   - Reads text files (.txt, .md, .log)
   - Outputs file contents

2. **Email Agent Node** (`email_agent_node`):
   - Receives file contents from File Agent
   - Sends email with file contents
   - Returns delivery status

## 🔧 Troubleshooting Common Issues

### Issue 1: "Required variable missing"
**Error:** `Input validation failed: Required variable 'directory_path' is missing`

**Solution:** Make sure both required variables are provided:
```json
{
  "input": {
    "directory_path": ".",
    "recipient_email": "your@email.com"
  }
}
```

### Issue 2: "Invalid email format"
**Error:** `Variable 'recipient_email' must match email pattern`

**Solution:** Use a valid email format:
```json
{
  "recipient_email": "valid.email@domain.com"
}
```

### Issue 3: "Agent not found"
**Error:** `Agent 'xxx' not found`

**Solution:** The workflow uses your actual agent IDs, so this shouldn't happen. If it does, check:
```bash
curl http://localhost:8000/api/agents/
```

### Issue 4: "Directory not found"
**Error:** File system errors

**Solution:** Use an existing directory path:
```json
{
  "directory_path": "/Users/jwalton/Documents"
}
```

## 🎮 Test Individual Nodes

### Test File Agent Node Only
```bash
curl -X POST http://localhost:8000/api/workflows-enhanced/working-file-email-workflow/nodes/file_agent_node/execute \
  -H "Content-Type: application/json" \
  -d '{
    "directory": "."
  }'
```

### Test Email Agent Node Only  
```bash
curl -X POST http://localhost:8000/api/workflows-enhanced/working-file-email-workflow/nodes/email_agent_node/execute \
  -H "Content-Type: application/json" \
  -d '{
    "email_content": "Test email content",
    "to_email": "test@example.com"
  }'
```

## 📈 Monitor Execution

### Check Execution Status
```bash
curl http://localhost:8000/api/workflows-enhanced/working-file-email-workflow/executions
```

### Get Specific Execution Details
```bash
curl http://localhost:8000/api/workflows-enhanced/executions/{execution_id}
```

## 🎯 Quick Start Commands

**Copy and paste these commands in order:**

```bash
# 1. Upload workflow
curl -X POST http://localhost:8000/api/workflows-enhanced/ \
  -H "Content-Type: application/json" \
  -d @examples/working_file_email_workflow.json

# 2. Execute workflow (replace email!)
curl -X POST http://localhost:8000/api/workflows-enhanced/working-file-email-workflow/execute \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "directory_path": ".",
      "recipient_email": "YOUR_EMAIL_HERE@example.com"
    },
    "debug": true
  }'
```

## ✅ Success Response Example

```json
{
  "execution_id": "exec_1234567890",
  "workflow_id": "working-file-email-workflow",
  "status": "completed",
  "output": {
    "sent_status": "delivered",
    "email_id": "msg_abc123"
  },
  "node_results": {
    "file_agent_node": {
      "found_files": ["file1.txt", "file2.md"],
      "file_data": "Contents of the files..."
    },
    "email_agent_node": {
      "sent_status": "delivered",
      "email_id": "msg_abc123"
    }
  },
  "started_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:30:45Z",
  "tokens_used": 342,
  "cost_usd": 0.045,
  "api_calls_made": 3
}
```

## 🔍 Debug Information

When `"debug": true` is used, you'll get additional information:
- **Node execution details**
- **Variable resolution logs**
- **Data mapping transformations**
- **Agent call traces**
- **Error details** (if any)

This workflow is **ready to execute** and should work with your current setup! 🎉