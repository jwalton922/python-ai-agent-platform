# Performance Tuning Guide

## Issue: Long-Running LLM Calls Block Other Requests

### Problem Description
When the chat endpoint makes long-running LLM calls (30-60+ seconds), other API requests like activity polling get blocked and cannot be processed. This happens even though the code properly uses `async/await`.

### Root Cause
The default uvicorn configuration runs with a **single worker process**. While async operations don't block the thread, a single event loop can still become saturated when handling long-running async operations, preventing it from processing other incoming requests efficiently.

### Solution: Use Multiple Worker Processes

#### Development Mode (with auto-reload)
```bash
# Default mode - single worker with auto-reload
python run_unified.py

# Or explicitly set reload mode
RELOAD=true python run_unified.py
```
**Note:** Auto-reload mode only supports single worker for file watching.

#### Production Mode (multiple workers)
```bash
# Run with 4 workers (default)
python run_production.py

# Or customize number of workers
WORKERS=8 python run_production.py

# Or use the unified script in production mode
RELOAD=false WORKERS=4 python run_unified.py
```

### Configuration Options

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `WORKERS` | 4 | Number of worker processes (production only) |
| `RELOAD` | true | Enable auto-reload (forces single worker) |
| `HOST` | 0.0.0.0 | Server host binding |
| `PORT` | 8000 | Server port |

### Performance Recommendations

1. **For Development**: Use single worker with reload for convenience
   ```bash
   python run_unified.py  # Auto-reload enabled
   ```

2. **For Production**: Use multiple workers without reload
   ```bash
   python run_production.py  # 4 workers, no reload
   ```

3. **For Heavy LLM Workloads**: Increase worker count
   ```bash
   WORKERS=8 python run_production.py
   ```

### How Multiple Workers Help

- Each worker process has its own event loop
- Long-running requests in one worker don't block others
- Requests are distributed across workers by the OS
- Better CPU utilization on multi-core systems

### Additional Optimizations

1. **Use Background Tasks**: For very long operations, consider using background task queues (Celery, RQ)
2. **Implement Request Timeouts**: Add timeouts to prevent indefinite blocking
3. **Use Connection Pooling**: For database and API connections
4. **Consider Async LLM Streaming**: Stream responses instead of waiting for complete generation

### Monitoring

Check worker status:
```bash
# See active worker processes
ps aux | grep uvicorn

# Monitor CPU usage per worker
htop  # or top
```

### Testing the Fix

1. Start the server with multiple workers:
   ```bash
   WORKERS=4 RELOAD=false python run_unified.py
   ```

2. Make a long-running chat request:
   ```bash
   curl -X POST http://localhost:8000/api/chat \
     -H "Content-Type: application/json" \
     -d '{"agent_id": "your-agent-id", "message": "complex request"}'
   ```

3. While that's running, test that other endpoints still respond:
   ```bash
   curl http://localhost:8000/api/activities
   curl http://localhost:8000/health
   ```

With multiple workers, these requests should respond immediately even while the chat request is processing.