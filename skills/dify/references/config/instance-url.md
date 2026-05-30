# Instance URL Configuration

## Overview

Dify can run as a cloud service or as a self-hosted deployment. The base URL of the REST API differs between these two modes. All reference documentation in this skill uses the placeholder `https://<your-dify-domain>/v1` to represent the base URL — never the hardcoded cloud URL — because this plugin is designed for use with self-hosted instances.

---

## This Project's Instance

The Dify instance used in this project is self-hosted at:

```
https://app-human04s.tsunagi.ai/v1
```

This is **not** the Dify Cloud URL (`https://api.dify.ai/v1`). Using the cloud URL in HTTP nodes or in API calls made to this instance will fail silently.

---

## URL Comparison

| Deployment type | Base URL |
|---|---|
| Dify Cloud (default) | `https://api.dify.ai/v1` |
| **This project (self-hosted)** | `https://app-human04s.tsunagi.ai/v1` |
| Generic self-hosted placeholder | `https://<your-dify-domain>/v1` |

---

## How to Reference the Base URL in Generated DSL

When a workflow contains HTTP nodes that call the Dify API (meta-workflows, child-workflow invocation, knowledge base querying), the base URL must be stored as an environment variable — never hardcoded in the YAML.

**Step 1 — Add the environment variable in Dify:**

Go to **Workspace Settings → Environment Variables** and add:

```
DIFY_BASE_URL = https://app-human04s.tsunagi.ai/v1
```

**Step 2 — Reference it in HTTP node URL fields:**

```yaml
url: "{{#env.DIFY_BASE_URL#}}/workflows/run"
```

This approach works for any deployment: cloud users set `DIFY_BASE_URL` to `https://api.dify.ai/v1`; self-hosted users set it to their own domain.

---

## Webhook URL Format

When a workflow uses a Webhook Trigger node, Dify generates a unique URL for that workflow. The format for this instance is:

```
https://app-human04s.tsunagi.ai/webhooks/{unique_id}
```

The `{unique_id}` is displayed in the Trigger-Webhook node's configuration panel after the workflow is saved.

---

## Studio / Import URL

To import a generated DSL file into this Dify instance, go to:

```
https://app-human04s.tsunagi.ai
```

Click **Create App** → **Import DSL** and upload the generated YAML file.

---

## Pre-Deployment Checklist

Before importing any generated DSL that contains HTTP nodes calling the Dify API:

- [ ] Confirm the base URL of the target Dify instance
- [ ] Set `DIFY_BASE_URL` in **Workspace Settings → Environment Variables** to the correct base URL
- [ ] Verify that all HTTP node URL fields use `{{#env.DIFY_BASE_URL#}}` rather than a hardcoded domain
- [ ] Confirm the App API Key for any target app is stored as an environment variable (e.g., `DIFY_APP_API_KEY`) — never embedded directly in the YAML
