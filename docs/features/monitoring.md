# Monitoring

Dify provides built-in analytics and supports integrations with external observability platforms for detailed trace-level monitoring of workflow executions. Monitoring helps identify performance bottlenecks, control costs, and debug failures in production.

---

## Built-In Analytics Dashboard

Access the analytics dashboard via **Monitoring → Overview** in the Dify sidebar (or the app-specific **Analytics** tab).

### Metrics Available

- **Total Messages:** Count of workflow/chatflow invocations over the selected timeframe.
- **Active Users:** Unique users who sent at least one message (chatflow only).
- **Token Usage:** Total input and output tokens consumed, broken down by LLM node and model.
- **Latency:** Average, p50, p90, and p99 response time per run. High p99 indicates occasional outlier slowdowns.
- **Error Rate:** Percentage of runs that ended in a node error or exception.
- **Cost Estimates:** Approximate cost in USD based on token usage and model pricing.

### Timeframes and Filtering

- Select from preset ranges: Last 24 hours, Last 7 days, Last 30 days.
- Custom date range selection is available.
- Filter by app version (useful after publishing a new version to compare before/after).
- Export raw data as CSV for analysis in external tools.

### Logs View

**Monitoring → Logs** shows individual run records. Each record includes:
- Timestamp and duration.
- Full input and output.
- Node-level trace (expand to see each node's input, output, tokens, and latency).
- Error details if the run failed.
- User identifier (if passed via API).

---

## External Monitoring Integrations

The built-in dashboard is sufficient for overview monitoring. For trace-level observability, cost alerting, and long-term trend analysis, integrate with an external platform.

---

### Langfuse

Langfuse is an open-source LLM observability platform. Every Dify workflow run sends a full trace to Langfuse, including all LLM calls, their inputs/outputs, token counts, and latencies.

**What Langfuse tracks from Dify:**
- Every LLM call as a **span** within a parent trace per workflow run.
- Input messages (system prompt + user prompt) and output text.
- Token usage per call (input tokens, output tokens, total).
- Latency per LLM call and end-to-end run latency.
- Node names and sequence within the trace.
- Error information for failed calls.

**Setup steps:**
1. Create an account at https://cloud.langfuse.com (or self-host Langfuse).
2. Create a new project in the Langfuse dashboard. Note the **Public Key** and **Secret Key**.
3. In Dify, go to **Settings → Monitoring**.
4. Click **Configure** next to Langfuse.
5. Enter:
   - **Public Key:** from Langfuse project settings.
   - **Secret Key:** from Langfuse project settings.
   - **Host:** `https://cloud.langfuse.com` (or your self-hosted URL).
6. Click **Test Connection** to verify credentials are accepted.
7. Click **Enable**. From this point, all new workflow runs send traces to Langfuse.

**Viewing traces in Langfuse:**
- Go to your Langfuse project → **Traces**.
- Each Dify run appears as a trace with a unique trace ID.
- Click a trace to see the full span tree: each LLM call, its prompt, completion, and metrics.
- Use Langfuse's **Sessions** feature to group traces by conversation (chatflow use case).

**Finding the trace ID for a specific run:**
- In Dify Logs, click a run record.
- The Langfuse trace ID is shown in the metadata panel (if monitoring is enabled).
- Use this ID to jump directly to the trace in Langfuse for detailed debugging.

---

### LangSmith

LangSmith is Anthropic/LangChain's observability platform. Similar to Langfuse in capability.

**What LangSmith tracks:**
- Full traces per workflow run including LLM call inputs/outputs.
- Token usage and latency.
- Project-level aggregated metrics.

**Setup steps:**
1. Create an account at https://smith.langchain.com.
2. Create a new project. Note the **API Key** and **Project Name**.
3. In Dify, go to **Settings → Monitoring**.
4. Click **Configure** next to LangSmith.
5. Enter:
   - **API Key:** from LangSmith account settings.
   - **Project Name:** the LangSmith project to send traces to.
6. Click **Enable**.

LangSmith is particularly useful if the team is already using the LangChain ecosystem for other ML tooling.

---

### Arize

Arize is an ML observability and model performance monitoring platform. It is purpose-built for detecting model drift, data quality issues, and distributional shifts — capabilities that go beyond what Langfuse and LangSmith offer.

**What Arize tracks:**
- LLM input/output pairs stored as production data.
- Token usage and latency metrics.
- Embedding drift over time (if embeddings are logged).
- Production vs baseline distribution comparison.

**Setup steps:**
1. Create an account at https://arize.com.
2. Create a space. Note the **API Key** and **Space ID**.
3. In Dify, go to **Settings → Monitoring**.
4. Click **Configure** next to Arize.
5. Enter:
   - **API Key:** from Arize settings.
   - **Space ID:** from Arize space settings.
6. Click **Enable**.

**Best use case:** Long-running production workflows where detecting model behavior drift over weeks/months matters (e.g., customer-facing chatbots, automated classification systems).

---

## Custom Metadata in Traces

When calling the Dify API, you can pass custom metadata that is forwarded to the monitoring platform:

```json
{
  "inputs": { "query": "..." },
  "user": "user-123",
  "metadata": {
    "session_id": "sess-abc",
    "customer_tier": "enterprise",
    "region": "us-west"
  }
}
```

The `metadata` object appears as trace-level tags in Langfuse, enabling filtering by customer, region, or session.

---

## Cost Tracking

- The built-in dashboard provides token usage charts per model and per time period.
- Multiply token counts by model pricing to estimate cost (Dify shows approximate USD costs based on public pricing).
- For precise cost tracking, use Langfuse's **Cost** view, which applies model-specific pricing to each trace automatically.
- Set up Langfuse cost alerts to be notified when spending exceeds a threshold.

---

## Alerting

Dify has no built-in alerting system. For production alert requirements:

1. **Langfuse alerts:** Configure metric alerts in Langfuse (error rate threshold, latency threshold, cost threshold). Langfuse sends email or webhook notifications.
2. **Export to external systems:** Export Dify logs via the API on a schedule, then feed into PagerDuty, Datadog, or Grafana for alerting.
3. **LangSmith alerts:** LangSmith supports rule-based alerts for error rate and latency.

---

## Using Monitoring to Debug Failing Workflows

When a workflow fails in production:

1. Open **Monitoring → Logs** in Dify.
2. Filter by error status and the relevant time window.
3. Click the failing run to open its trace.
4. Expand each node to find the node that produced an error or unexpected output.
5. For LLM nodes: inspect the exact prompt sent and the raw response received.
6. Cross-reference with Langfuse (if configured): the Langfuse trace provides richer metadata and the full span tree with nanosecond timing.
7. Reproduce the failure locally using the same inputs in the Dify workflow editor's debug run mode.
