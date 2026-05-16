---
description: Run verdict audit on current diff and report findings inline
---

Run verdict on the current repository's diff and report all findings.

Steps:
1. Determine the current working directory (use workspace directory from environment_details)
2. Call verdict.check_diff (MCP) or run `verdict run` (terminal) on this directory
3. Parse the Scorecard output (JSON format with verdict, findings, summary)
4. If verdict is LIED or SUSPICIOUS, list every finding with file:line citations
5. If verdict is PASS, report "Verdict: PASS - no issues detected"

Do not write code. Do not suggest fixes. Report findings only.