# Antigravity follow-up prompt — technical review actions

Copy this prompt to Antigravity to close out the technical manager review.

---

You are the **Senior Developer**. I am the **Technical Manager** and will review your final report. Continue work in the currently open Weather Forecast & Alert Application repository. Inspect the current files first, preserve existing work, and do not assume the review notes are already applied correctly.

## Review actions

1. Confirm the live hourly forecast begins at the current observation hour, and that current rain probability comes from that same hour. If the current timestamp is not present in the hourly series, handle the nearest valid future hour safely.
2. Confirm direct-coordinate requests ask the provider for the location's local timezone and return the resolved timezone in the API response.
3. Confirm storm WMO codes are named constants, malformed codes do not crash the API, and `/thresholds` returns the code list.
4. Review the dashboard's offline-mode wording: simulation removes the external weather-provider dependency, but the local FastAPI backend is still required by the Streamlit dashboard.
5. Reconcile all documentation with the actual API and code. There are five routes: `/health`, `/locations`, `/thresholds`, `/weather`, and `/weather/report`. Make response examples, error codes, alert rules, report fields, forecast window, and setup commands accurate.
6. Review simulation scenarios, CSV report fields and filename behavior, `.env.example`, `.gitignore`, and generated-output handling. Do not claim secrets were checked in Git history unless a Git repository and its history were actually inspected.
7. Correct the completion report author/reviewer line: **Prepared by Antigravity, Senior Developer; reviewed by the user, Technical Manager.**

## Validation and boundaries

Run focused checks only if a working Python environment is available. At minimum, verify imports, alert boundaries (including humidity and storm), simulation responses, the weather/threshold/report routes, correct current-hour forecast alignment, and dashboard startup. Do not use paid services or real credentials. Do not claim a check passed unless it ran and you observed its result.

If Python or another required tool is unavailable, record exactly what prevented validation and provide the commands for the Technical Manager to run locally. A screenshot must be genuine; if the dashboard cannot be launched, leave capture instructions and say no screenshot was captured.

Do not initialize a remote repository, commit, push, publish, deploy, or spend money. Do not overwrite unrelated files. Keep generated reports and private settings out of source control.

## Final response to the Technical Manager

Return a concise **Review Closure Report** with:

- Actions completed and files changed.
- Validation commands actually run and results, separated into passed, failed, and blocked/skipped.
- Whether the live forecast alignment, timezone, report route, and simulation behavior were verified.
- Screenshot status and reason if unavailable.
- Git status: state whether a Git repository exists; do not imply files were committed or secrets scanned from history if it does not.
- Remaining issues and exact next steps for the Technical Manager.

Be precise about what is implemented versus runtime-verified. The Technical Manager is the approver; you are the Senior Developer.

---
