# Trigger: Schedule Node

## Overview

The Schedule Trigger node runs a Dify Workflow automatically on a time-based schedule — no human interaction required. You configure a frequency (hourly, daily, weekly, monthly, or a custom cron expression), and Dify executes the workflow at each scheduled time.

This makes it ideal for background jobs, periodic reporting, data synchronisation, and any automation that should happen on a clock rather than in response to a user or external event.

**Important**: Schedule triggers are available in **Workflows only**. They cannot be used in Chatflows.

## When to Use

Use a Schedule Trigger whenever work should happen automatically at regular intervals:

- **Daily reports**: Generate a summary of the previous day's data every morning at 8 AM and email it to stakeholders.
- **Hourly data sync**: Pull updated records from an external API every hour and write them to a database or knowledge base.
- **Weekly digests**: Compile a weekly newsletter or digest from accumulated content and send it every Monday morning.
- **Database cleanup**: Remove expired records, archive old logs, or vacuum stale cache entries on a nightly basis.
- **Health check pings**: Send periodic test requests to external services and alert a Slack channel if any return errors.
- **Scheduled LLM evaluations**: Run a suite of prompts against your LLM nodes on a schedule to track quality over time.
- **Reminder notifications**: Send daily or weekly nudges to users who have pending actions in your system.

Anywhere you would use a cron job, a cloud scheduler (AWS EventBridge, Google Cloud Scheduler), or a scheduled task, a Schedule Trigger workflow can replace the infrastructure with a no-code alternative — while still giving you the full power of LLM nodes, HTTP requests, and code execution within the workflow.

## Limitations

- **Workflow type only**: Schedule triggers cannot be added to Chatflows.
- **No standalone web app**: A workflow with a schedule trigger cannot be published as a shareable web application. It runs only on its configured schedule (or via the API).
- **No MCP server publishing**: Schedule-triggered workflows cannot be exposed as MCP server tools.
- **No user input**: Because no human initiates the run, there are no user-provided variables. Start node variable declarations are not available. Use environment variables, system variables, or data fetched by HTTP Request nodes to drive the workflow's logic.
- **Timezone awareness**: Always set the timezone explicitly. Dify defaults to UTC; if your business operates in a different timezone, set it correctly to avoid off-by-one-hour errors during daylight saving transitions.

## Schedule Configuration

### Frequency Options

| Frequency | Description | Additional Fields |
|---|---|---|
| `hourly` | Runs at the top of every hour | None |
| `daily` | Runs once per day | `time` (HH:MM) |
| `weekly` | Runs once per week | `time`, `day_of_week` |
| `monthly` | Runs once per month | `time`, `day_of_month` |
| `cron` | Full cron expression | `cron_expression` |

### Timezone

Use standard IANA timezone identifiers such as `UTC`, `America/New_York`, `Europe/London`, `Asia/Shanghai`, `Asia/Tokyo`. A full list is available at [iana.org/time-zones](https://www.iana.org/time-zones).

## YAML Configuration

```yaml
- data:
    desc: ''
    selected: false
    title: Schedule Trigger
    type: trigger-schedule
    schedule:
      frequency: daily     # hourly, daily, weekly, monthly, cron
      time: '09:00'        # HH:MM in 24-hour format
      timezone: 'UTC'      # IANA timezone identifier
      # For weekly schedules, add:
      # day_of_week: monday   # monday, tuesday, ..., sunday
      # For monthly schedules, add:
      # day_of_month: 1       # 1–31
      # For custom cron schedules, replace all above with:
      # cron_expression: '0 9 * * 1'   # 9am every Monday
  height: 54
  id: '1732001000002'
  position:
    x: 80
    y: 282
  positionAbsolute:
    x: 80
    y: 282
  selected: false
  sourcePosition: right
  targetPosition: left
  type: custom
  width: 244
```

### Example: Weekly Schedule

```yaml
schedule:
  frequency: weekly
  time: '08:30'
  timezone: 'America/New_York'
  day_of_week: monday
```

### Example: Monthly Schedule

```yaml
schedule:
  frequency: monthly
  time: '00:00'
  timezone: 'UTC'
  day_of_month: 1
```

### Example: Custom Cron

```yaml
schedule:
  frequency: cron
  cron_expression: '30 8 * * 1-5'   # 8:30 AM, Monday through Friday
  timezone: 'Europe/London'
```

## Available Variables

Because no user initiates a scheduled run, there are no user-provided inputs. Instead, use the following sources for data in your workflow:

### System Variables

These are always available in any workflow execution:

| Variable | Description |
|---|---|
| `{{#sys.timestamp#}}` | Unix timestamp (seconds) of when this run started |
| `{{#sys.workflow_run_id#}}` | Unique identifier for this specific execution instance |
| `{{#sys.workflow_id#}}` | The workflow definition ID (stable across runs) |
| `{{#sys.app_id#}}` | The Dify application ID |

Use `{{#sys.timestamp#}}` to compute relative date ranges (e.g., "fetch all records created in the last 24 hours") and `{{#sys.workflow_run_id#}}` to correlate logs across systems.

### Environment Variables

Store configuration values as Dify Environment Variables and reference them with:

```
{{#env.variable_name#}}
```

Examples:
- `{{#env.api_endpoint#}}` — the URL of an external API to call
- `{{#env.report_recipients#}}` — comma-separated email addresses for report delivery
- `{{#env.lookback_hours#}}` — how many hours back to fetch data (allows changing the window without editing the workflow)

Environment variables are set in the Dify app settings panel and are not visible in the DSL YAML, which keeps secrets out of version control.

### Data Fetched Mid-Workflow

Often, scheduled workflows begin with an HTTP Request node that fetches the data needed for this run:

1. **HTTP Request node** → calls your API with `{{#sys.timestamp#}}` as a query parameter.
2. **Code node** → parses the JSON response and computes derived values.
3. **LLM node** → generates a summary or analysis.
4. **HTTP Request node** → posts results to Slack, email API, or database.

This pattern avoids the need for any user-supplied input entirely.

## Cron Expression Reference

Dify uses standard five-field cron syntax:

```
┌──── minute (0–59)
│  ┌─── hour (0–23)
│  │  ┌── day of month (1–31)
│  │  │  ┌─ month (1–12)
│  │  │  │  ┌ day of week (0–7, Sunday is 0 or 7)
│  │  │  │  │
*  *  *  *  *
```

| Schedule | Cron Expression | Notes |
|---|---|---|
| Every minute | `* * * * *` | Use sparingly — high frequency |
| Every hour | `0 * * * *` | At :00 of every hour |
| 9 AM daily | `0 9 * * *` | 9:00 AM every day |
| 9 AM weekdays | `0 9 * * 1-5` | Monday through Friday |
| 9 AM Monday | `0 9 * * 1` | Weekly on Monday |
| Midnight Sunday | `0 0 * * 0` | Start of every week |
| 1st of month | `0 0 1 * *` | Monthly at midnight |
| Every 15 minutes | `*/15 * * * *` | Frequent polling |
| 8:30 AM daily | `30 8 * * *` | Non-zero minute example |
| Twice daily | `0 9,17 * * *` | 9 AM and 5 PM |

### Tips

- Use `*/N` for "every N units" (e.g., `*/6` in the hour field means every 6 hours).
- Use comma-separated values for multiple specific values (e.g., `1,15` in the day-of-month field means the 1st and 15th).
- Use ranges with `-` (e.g., `1-5` for Monday through Friday).
- Always validate cron expressions with a tool like [crontab.guru](https://crontab.guru) before deploying.

## Key Considerations

1. **Idempotency**: Design scheduled workflows to be safe to run more than once for the same time period. If Dify retries a failed run or you manually trigger a test run, the workflow should not create duplicate records or send duplicate notifications.

2. **Execution time vs. schedule interval**: If your workflow takes 10 minutes to run and you schedule it every 5 minutes, runs will overlap. Either ensure the workflow is stateless and overlap is safe, or schedule it less frequently than its worst-case execution time.

3. **Error handling**: Add error handling to HTTP Request nodes and Code nodes. A scheduled workflow has no user watching it — failures are silent unless you explicitly route error branches to a notification step (e.g., a Slack alert or email).

4. **Logging**: Use `{{#sys.workflow_run_id#}}` in any external logs or database writes your workflow produces. This makes it straightforward to trace a specific run when debugging.

5. **Environment-based configuration**: Avoid hard-coding dates, endpoints, or thresholds in the workflow. Use environment variables so you can change behaviour without editing and republishing the workflow.
