# Antigravity execution prompt

Copy the prompt below into Antigravity with this project folder open. It asks Antigravity to inspect the existing work, complete the application, run appropriate checks, and return a report you can review.

---

## Prompt

You are the **senior developer** working for the user, who is the **technical manager**. Deliver a complete, beginner-friendly, GitHub-ready student project titled **Weather Forecast & Alert Application**. Work directly in the currently open project folder. The technical manager wants a working application they can demonstrate, understand, and explain in interviews, and will review your completion report.

### Delivery objective

Inspect the repository before editing. Preserve useful existing work and user changes. Then complete the application end to end. Do not stop after proposing a plan or producing sample snippets: make the code, documentation, setup instructions, and demo path work together. Work in clear phases, keep the user informed with concise progress updates, and resolve routine implementation decisions yourself. Ask only if a required external credential or destructive action cannot be avoided.

### Product requirements

Build a Python application with:

1. **FastAPI backend** that accepts a city name and optional latitude/longitude, fetches current weather and forecast data, normalizes the JSON response, computes risk alerts, and returns predictable JSON.
2. **Streamlit dashboard** with a city input, current-weather metrics, forecast charts, a location map, risk notifications, clear loading/error states, simulation mode, and a CSV report download.
3. **Public weather data integration.** Prefer a no-key public provider such as Open-Meteo so a student can run the project immediately. If a provider that needs a key is selected, load the key from a local `.env` file on the server only; never put it in frontend code, logs, screenshots, or Git.
4. **Offline simulation** with deterministic, visibly labeled example scenarios. Simulation must not be confused with live weather and must work without network access.
5. **Risk rules** for rain probability/amount, high temperature, relative humidity, wind, and AQI when available. If the selected weather source exposes storm/severe-weather codes, document their meaning and add a cautious code-based rule. Do not claim that rain or wind alone confirms a storm. Handle absent optional fields without inventing values.
6. **CSV report generation** containing location, source, retrieval time, current readings, forecast rows, and alerts. Provide an API download route and a dashboard download control. Save a local report copy in `outputs/` if appropriate, and keep generated/private files out of Git.
7. **Usable failure handling** for unknown cities, invalid coordinates, timeouts, provider errors, malformed responses, unavailable AQI, and report-write failures. Live-provider failure must not silently return simulation data.

Use transparent, configurable educational thresholds. Clearly label them as examples rather than official warnings. Keep units, local timestamps, source, and simulation status visible. Do not provide medical, safety, or operational guarantees.

### Repository shape

Keep or adapt the project toward this structure:

```text
Weather-Forecast-Alert-Application/
├── data/
├── src/
│   ├── weather_app/       # API, provider service, configuration, alert rules
│   └── dashboard/         # Streamlit user interface
├── outputs/               # local generated reports, ignored by Git
├── images/                # real project screenshots/visuals
├── reports/               # report templates or report documentation
├── docs/                  # explanation, architecture, install, plan, interview guides
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
└── main.py                # root ASGI entry point
```

Explain each folder and file in the README. Keep modules small and beginner-readable. Add comments/docstrings at the points where a learner needs to understand the workflow; avoid unexplained dense code.

### Work phases

1. **Audit:** inspect the existing tree, source, README, dependency files, and Git status if available. Identify missing or inconsistent pieces before editing.
2. **Setup and configuration:** document supported Python version, virtual environment commands for Windows PowerShell and macOS/Linux, dependency installation, `.env.example`, and secret-safe behavior. Ensure `.gitignore` excludes `.env`, virtual environments, Python caches, and generated outputs while allowing `.env.example`.
3. **Provider and data model:** implement location lookup and live forecast/AQI retrieval with timeouts. Normalize into documented `location`, `current`, `hourly`, `daily`, `alerts`, `source`, and `fetched_at` fields. Keep provider-specific details in the service layer.
4. **Alerts:** implement readable, testable rule functions for rain, temperature, humidity, wind, and optional AQI. Handle missing values. Put thresholds in one clearly documented location.
5. **Simulation:** add deterministic offline locations covering useful alert examples; label every simulated response and dashboard view.
6. **API:** provide health, locations, weather, and CSV report routes; validate inputs and map failures to helpful HTTP errors. Include interactive OpenAPI docs.
7. **Dashboard:** wire the city search to the API and display metrics, charts, map, alert levels, source, timestamp, and simulation state. Add an actionable report download and clear error messages.
8. **Documentation and portfolio:** provide a concise README, architecture/data-flow diagram, beginner project explanation, tech stack choices, phased build plan, installation guide, GitHub publishing instructions, screenshot workflow, limitations, and interview preparation.
9. **Validation:** install dependencies only if available/allowed, run focused automated checks and app-level smoke checks, and fix failures. At minimum verify imports, API health, simulation weather, key alert boundaries including humidity, missing-AQI handling, CSV output, dashboard startup, and documented run commands. Do not claim a check passed unless it was actually run. Do not use real paid APIs or expose secrets for validation.
10. **Review:** inspect the final diff and repository tree. Check links and commands for stale paths, ensure `.env` and generated reports are ignored, and confirm the README matches actual behavior. Capture a genuine dashboard screenshot in `images/` if the environment supports it; never fabricate a screenshot. If capture is unavailable, leave clear capture instructions and say so in the report.

### GitHub and safety boundaries

Make the repository ready for GitHub, but do not create a remote repository, publish, push, deploy, or spend money unless the user explicitly authorizes that action. Never commit real API keys, account data, `.env`, local databases, or private reports. Do not overwrite unrelated user files. Avoid adding unnecessary frameworks or services.

### Required final report

When implementation is complete, provide a clear **Project Completion Report** for the student to review. Include:

- **Executive summary:** what was delivered and what the application does.
- **Architecture:** a short request/data flow from city input through provider, processing, alerts, report, and dashboard.
- **Changed files:** group important files by backend, dashboard, configuration, and documentation; explain each group's purpose.
- **How to run:** exact Windows and macOS/Linux commands, API docs URL, dashboard URL, and how to use simulation mode.
- **API examples:** weather, simulation, and CSV report routes with example parameters.
- **Alert rules:** list the actual thresholds, units, and severity levels implemented.
- **Validation results:** commands/checks actually run and their outcomes. Separate passed, failed, skipped, and blocked checks. Include environment limitations plainly.
- **Screenshot status:** link the genuine screenshot if created, or state why it could not be captured and how the user can capture one.
- **Known limitations and next steps:** clearly distinguish current features from future work such as persistence, scheduled polling, email/SMS, authentication, or deployment.
- **GitHub readiness:** confirm secret ignore rules and whether anything was published. Do not imply that the project was uploaded if it was only prepared locally.

Write the report so a student can understand it and use it as a project handoff. Do not hide unfinished work behind optimistic language. Finish with a short checklist of anything the student must still do personally, such as adding their own screenshot or creating the GitHub repository.

---
