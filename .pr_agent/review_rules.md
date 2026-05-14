# Smartpet Review Rules

## Global
- Always prioritize clear bugs, security problems, and configuration mistakes over style suggestions.
- When a PR only changes documentation or README files, treat it as low risk unless installation, secrets, or deployment instructions are modified.
- For documentation-only PRs, tests are optional and should not be treated as a blocker.

## Python App Changes
- When pp.py, gui_app.py, or files under src/ change, pay extra attention to startup flow, tray behavior, window lifecycle, and background tasks.
- If a change touches configuration, environment variable handling, or secrets-related files, explicitly check for accidental secret exposure and raise the risk level when appropriate.

## Review Output Preference
- Mention the most important risk first.
- Prefer concise, actionable findings over style-only feedback.