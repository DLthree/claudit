# Results Format Specification

This document describes the JSON schema used for manual result sets (e.g. code-audit or search results) produced by tools such as the VS Code Manual Result Set Extension.

---

## Top-Level Structure

The file is a single JSON object with two top-level properties:

| Property   | Type   | Required | Description |
|-----------|--------|----------|-------------|
| `metadata` | object | Yes      | Provenance and tool information for the result set. |
| `results`  | array  | Yes      | List of individual findings or result entries.     |

---

## `metadata` Object

Describes who/what produced the result set and when.

| Field       | Type   | Required | Description |
|-------------|--------|----------|-------------|
| `author`    | string | Yes      | Human-readable label for the result set (e.g. "Manual Result Set" or a query name). |
| `timestamp` | string | Yes      | ISO 8601 date-time when the result set was created (e.g. `YYYY-MM-DDTHH:mm:ss.sssZ`). |
| `tool`      | string | Yes      | Name of the tool or extension that generated the results. |
| `version`   | string | Yes      | Version of the tool or result format (e.g. semantic version). |

---

## `results` Array

Each element is an object representing one finding or hit. All fields below are strings or numbers unless noted.

| Field         | Type   | Required | Description |
|---------------|--------|----------|-------------|
| `ID`          | string | Yes      | Unique identifier for this result within the result set (often numeric as string, e.g. `"1"`, `"2"`). |
| `description` | string | Yes      | Short summary of the finding: what code or pattern was found (e.g. a code snippet or one-line description). |
| `notes`       | string | Yes      | Additional context, interpretation, or commentary (e.g. "dead code", "many callers", "unclear how..."). |
| `category`    | string | Yes      | Classification of the result (e.g. "Manual" for manually added findings). |
| `severity`    | string | Yes      | Severity or importance level (e.g. `"info"`, `"warning"`, `"error"`). |
| `filename`    | string | Yes      | Path to the source file, typically relative to the project or repository root. |
| `linenum`     | number | Yes      | 1-based line number in `filename` where the finding applies. |
| `col_start`   | number | Yes      | 1-based column index of the start of the highlighted span. |
| `col_end`     | number | Yes      | 1-based column index of the end of the highlighted span. |
| `function`    | string | Yes      | Name of the function (or scope) containing this location; may be empty if unknown. |
| `color`       | string | No       | Optional RGBA color for UI highlighting (e.g. `"rgba(150, 0, 255, 0.3)"`). Omitted if no color is set. |

---

## Schema Summary (JSON)

```json
{
  "metadata": {
    "author": "<string>",
    "timestamp": "<ISO 8601 string>",
    "tool": "<string>",
    "version": "<string>"
  },
  "results": [
    {
      "ID": "<string>",
      "description": "<string>",
      "notes": "<string>",
      "category": "<string>",
      "severity": "<string>",
      "filename": "<string>",
      "linenum": <number>,
      "col_start": <number>,
      "col_end": <number>,
      "function": "<string>",
      "color": "<string>"
    }
  ]
}
```

---

## Notes

- **Locations:** The `filename`, `linenum`, `col_start`, and `col_end` fields together define a source span that tools can use for navigation and highlighting.
- **IDs:** Result IDs are unique within a single file; they are not guaranteed globally unique across multiple result files.
- **Colors:** When present, `color` is intended for editor or UI highlighting (e.g. in a list or minimap). The format is CSS `rgba(r, g, b, a)`.
