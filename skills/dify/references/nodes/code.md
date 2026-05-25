# Code Node

## Overview

The Code node executes Python 3 or JavaScript (Node.js) code in a sandboxed environment. Use it for data transformation, computation, or logic that LLMs cannot do reliably or deterministically. Unlike the LLM node, the Code node produces exact, reproducible results — it is the right tool whenever the task has a definitive correct answer.

## When to Use

Choose the Code node over an LLM node when the task is:

- **JSON parsing and transformation** — extracting fields from an HTTP response body, reshaping nested objects, flattening arrays
- **Mathematical calculations** — arithmetic, statistics, unit conversions
- **String manipulation and formatting** — regex operations, padding, case conversion, building formatted output strings
- **Data validation** — checking that required fields exist, values are in range, formats match a pattern
- **Combining or restructuring variables from multiple nodes** — merging data from two upstream branches into a single object
- **HMAC signature verification** — computing or verifying message authentication codes for webhook security
- **Date and time calculations** — computing durations, formatting timestamps, converting timezones
- **Base64 encoding/decoding** — handling binary data in text-safe format

If the task requires language understanding, judgment, or natural language generation, use an LLM node instead.

## Node Type Reference

From the Dify node type reference:

- **type**: `code`
- **Execution Type**: EXECUTABLE
- **code_language**: `python3` or `javascript`
- **Error handling**: supports `error_strategy: fail-branch` or `default-value`
- **Source handles**: `source` (default) or `success-branch` / `fail-branch` (with error strategy)

## Sandbox Restrictions

CRITICAL — these are hard limits enforced by the Dify sandbox. Violating them causes the node to fail at runtime:

- **No network access** — `import requests`, `urllib.request`, `fetch`, and `axios` are blocked. The code cannot make HTTP calls; use an HTTP Request node for that.
- **No filesystem access** — `open()`, `os.path`, `readFile`, `writeFile`, and all file I/O are blocked.
- **No subprocess execution** — `subprocess`, `os.system`, `exec`, `spawn` are blocked.
- **No importing external packages** unless they are on the allowlist (see Available Python Libraries below).
- **Execution timeout: 10 seconds** — code that runs longer than 10 seconds is killed. For heavy processing, restructure the algorithm.
- **Memory limit applies** — avoid loading large data sets into memory.

Design your code to work within these constraints. If you need an external library not on the allowlist, reconsider the approach or request the library be added to the Dify sandbox configuration.

## Available Python Libraries

The following standard library and common modules are available in the Python 3 sandbox:

`json`, `math`, `re`, `datetime`, `hashlib`, `hmac`, `base64`, `random`, `string`, `collections`, `itertools`, `functools`, `operator`, `copy`, `uuid`, `urllib.parse`

All Python built-ins (`len`, `range`, `sorted`, `zip`, `map`, `filter`, `enumerate`, `isinstance`, `type`, `str`, `int`, `float`, `list`, `dict`, `set`, `tuple`, etc.) are available.

## Required Function Signature

The code must define a function named exactly `main`. The function parameters must match the declared input variables by name and type annotation. The return value must be a `dict` whose keys match the declared output variables.

```python
def main(arg1: str, arg2: int) -> dict:
    # Your logic here
    result = arg1.upper()
    return {
        "processed": result,
        "count": arg2 * 2
    }
```

Rules:
- The function **must** be named `main` (case-sensitive).
- Parameter names must exactly match the `inputs` variable names declared in the node YAML.
- Type annotations (`str`, `int`, `float`, `bool`, `list`, `dict`) are required.
- The return value **must** be a `dict`.
- Every key in the returned dict must be declared in the node's `outputs` section.
- Do not use `print()` for output — return values only.

## Complete YAML Example

A Code node that cleans and truncates input text:

```yaml
- data:
    code: |
      import json
      import re

      def main(text: str, max_length: int) -> dict:
          # Clean and truncate text
          cleaned = re.sub(r'\s+', ' ', text.strip())
          truncated = cleaned[:max_length] if len(cleaned) > max_length else cleaned
          word_count = len(truncated.split())
          return {
              "clean_text": truncated,
              "word_count": word_count,
              "was_truncated": len(cleaned) > max_length
          }
    code_language: python3
    desc: ''
    inputs:
      text:
        type: string
        value: '{{#start.raw_text#}}'
      max_length:
        type: number
        value: '{{#start.limit#}}'
    outputs:
      clean_text:
        type: string
      word_count:
        type: number
      was_truncated:
        type: boolean
    selected: false
    title: Clean Text
    type: code
  height: 54
  id: '1732001000010'
  position:
    x: 380
    y: 282
  positionAbsolute:
    x: 380
    y: 282
  selected: false
  sourcePosition: right
  targetPosition: left
  type: custom
  width: 244
```

## Input and Output Variable Types

**Input variable types** (in `inputs` section):
- `string` — text
- `number` — integer or float
- `boolean` — true/false
- `object` — JSON object
- `array_string`, `array_number`, `array_object`, `array_boolean` — typed arrays

**Output variable types** (in `outputs` section, using Dify SegmentType):
- `string`, `number`, `boolean`, `object`
- `array_string`, `array_number`, `array_object`, `array_boolean`
- `children`: optional nested structure definition for `object` types

## Output Variable Access

Downstream nodes reference Code node outputs using:

```
{{#1732001000010.clean_text#}}
{{#1732001000010.word_count#}}
{{#1732001000010.was_truncated#}}
```

Replace `1732001000010` with the actual `id` of your Code node.

## Error Handling

Configure `error_strategy` for production workflows:

```yaml
error_strategy: fail-branch
```

With `fail-branch`, the node exposes two source handles: `success-branch` and `fail-branch`. Connect the fail branch to a recovery LLM node or a variable-aggregator. The following error variables are available on the fail path:

- `{{#node_id.error_message#}}` — human-readable error description
- `{{#node_id.error_type#}}` — error type string

Without `error_strategy`, any exception terminates the entire workflow.

## JavaScript Mode

Set `code_language: javascript` to use Node.js instead of Python. The function must be named `main` and accept a single destructured object argument:

```javascript
async function main({text, maxLength}) {
    const cleaned = text.trim().replace(/\s+/g, ' ');
    const truncated = cleaned.slice(0, maxLength);
    return {
        clean_text: truncated,
        word_count: cleaned.split(' ').length,
        was_truncated: cleaned.length > maxLength
    };
}
```

JavaScript sandbox restrictions are equivalent to Python: no network access, no filesystem, no external packages beyond the Node.js standard library.

## Common Pattern Examples

### JSON Parsing from HTTP Response

Use after an HTTP Request node to extract fields from the response body (which is always a string):

```python
import json

def main(response_body: str) -> dict:
    data = json.loads(response_body)
    return {
        "user_id": data["user"]["id"],
        "email": data["user"]["email"],
        "is_active": data["user"]["status"] == "active"
    }
```

### HMAC Signature Verification

Verify webhook authenticity using a shared secret:

```python
import hmac
import hashlib
import base64

def main(payload: str, secret: str, received_signature: str) -> dict:
    computed = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    is_valid = hmac.compare_digest(computed, received_signature)
    return {
        "is_valid": is_valid,
        "computed_signature": computed
    }
```

### Data Reshaping (combining multiple upstream values)

Merge data from multiple upstream nodes into a structured object:

```python
import json

def main(llm_text: str, http_body: str, user_id: str) -> dict:
    api_data = json.loads(http_body)
    result = {
        "user_id": user_id,
        "ai_summary": llm_text.strip(),
        "api_status": api_data.get("status", "unknown"),
        "combined_score": len(llm_text) + api_data.get("score", 0)
    }
    return {
        "merged_result": json.dumps(result),
        "success": True
    }
```

## Common Mistakes

- **Function not named `main`**: Naming it `process`, `run`, or anything else causes a runtime error.
- **Parameter name mismatch**: If the input variable is declared as `raw_text` but the function parameter is `text`, the call fails. Names must match exactly.
- **Returning a non-dict**: Returning a string, list, or number instead of a `dict` causes a schema validation error.
- **Using restricted libraries**: Attempting `import requests` or `import numpy` will fail silently or raise an ImportError at runtime.
- **Output key not declared**: Returning a key in the dict that is not declared in the `outputs` section is ignored or causes an error.
- **Exceeding the 10-second timeout**: Loops with many iterations or recursive algorithms can time out. Profile and optimize before deploying.
- **Forgetting to parse JSON**: The HTTP Request node body output is always a `string`. You must call `json.loads()` before accessing fields.
