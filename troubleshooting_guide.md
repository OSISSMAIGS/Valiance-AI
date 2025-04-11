# Troubleshooting Guide - cPanel SIGTERM (Signal 15) Issues

This guide will help you diagnose and resolve the issue where your application is being terminated with signal 15 (SIGTERM) on cPanel.

## Understanding the Problem

Signal 15 (SIGTERM) is a termination signal sent to a process to request its termination. When you see:

```
[UID:1081][1646988] Child process with pid: 1649055 was killed by signal: 15, core dumped: no
```

This means your application was forcibly terminated by the system. The most common reasons include:

1. **Memory usage exceeding limits**: cPanel environments typically have memory limits (often around 512MB-1GB).
2. **CPU usage exceeding limits**: Extended high CPU usage can trigger process termination.
3. **Timeout limits**: Long-running processes may be terminated based on timeout settings.
4. **Manual intervention**: Server administrators may terminate processes.

## Diagnostic Tests

Follow these steps to diagnose the issue:

### Step 1: Install Required Dependencies

Ensure you have all dependencies installed:

```bash
pip install -r requirements.txt
```

### Step 2: Run the Resource Monitoring Test

This test will help identify memory, CPU, and other resource usage patterns:

```bash
python test_app_resources.py
```

The output will provide information about:
- Memory usage baseline
- MongoDB connection performance
- Gemini API memory usage
- Tuning data file size and memory impact
- Potential memory leaks
- CPU usage patterns

Pay special attention to these test results:
- `test_memory_usage_baseline`: Should show memory usage under 512MB
- `test_tuning_data_loading`: The tuning data file (51MB) may be contributing to memory issues
- `test_memory_leak_simulation`: Will show if memory increases over time

### Step 3: Monitor Live Resource Usage

To run the resource monitor while simulating typical application usage:

```bash
# Start your application in one terminal
python main.py

# In another terminal window, monitor your application's resource usage
python monitor_resource_usage.py --process main.py --interval 2 --duration 300
```

This will generate a log file `resource_monitor.log` with detailed resource metrics.

### Step 4: Implement the Optimized Version

We have created an optimized version of your application in `cpanel_deploy.py` with these improvements:

1. Added signal handlers to catch and log termination signals
2. Optimized MongoDB connection parameters
3. Added memory management with garbage collection
4. Limited the number of tuning examples used in each request
5. Added better error handling and logging
6. Implemented appropriate resource limits

To deploy this optimized version:

```bash
# Update the passenger_wsgi.py to use cpanel_deploy.py
# (It should already be configured to look for this file)

# Restart your application on cPanel
```

## Common Solutions

Based on your application analysis, here are the likely causes and solutions:

1. **Large tuning data file (51MB)**:
   - The file is loaded entirely into memory
   - SOLUTION: Limit the number of examples used as implemented in `cpanel_deploy.py`

2. **Memory leaks in API calls**:
   - SOLUTION: Added force garbage collection after each API call

3. **MongoDB connection issues**:
   - SOLUTION: Optimized connection parameters and added better error handling

4. **Missing signal handling**:
   - SOLUTION: Added signal handlers to log termination events

5. **Resource limits in cPanel**:
   - SOLUTION: Contact your hosting provider to inquire about increasing limits
   - Typically you can increase memory limits in cPanel under "Resources" or similar section

## Monitoring on cPanel

To monitor your application on cPanel:

1. Enable SSH access if available
2. Use cPanel's "Process Manager" to view resource usage
3. Check error logs in cPanel's "Error Log" section
4. Use the cPanel "Resource Usage" to monitor overall usage

## Additional Tips

- Consider breaking up large JSON files into smaller chunks
- Implement caching mechanisms to reduce API calls
- Use background processing for resource-intensive tasks
- Set appropriate timeouts for external API calls
- Implement rate limiting for user requests

If issues persist after implementing these solutions, contact your hosting provider for assistance with resource allocation or consider upgrading your hosting plan. 