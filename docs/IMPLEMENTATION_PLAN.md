# Ten-phase implementation plan

Use this as a student-friendly build order. The expected outputs below describe the goal of each phase. Some later items—especially report persistence—are planned extensions and are not in the current code yet.

## Phase 1: Setup

**What to do:** Install Python 3.10 or newer, create a virtual environment, activate it, and install the packages from the root `requirements.txt`.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
```

**Why:** A virtual environment keeps this project's packages separate from other Python projects and makes setup reproducible.

**Expected output:** The environment is active and FastAPI, Streamlit, HTTP, and chart libraries are installed.

**Common beginner mistakes:** Using a different Python interpreter for installation and running; forgetting to activate the environment in a new terminal; installing packages one at a time without recording them; confusing a PowerShell activation policy issue with an application error.

## Phase 2: Project folder creation

**What to do:** Create separate folders for the API, dashboard, documentation, data, and screenshots. Keep provider access and alert rules in backend modules rather than embedding everything in one script.

```text
weather-project/
  src/weather_app/   API, provider service, alert logic
  src/dashboard/     Streamlit interface
  data/              sample data notes or fixtures
  images/            screenshots and visuals
  docs/              project guides
```

**Why:** A clear layout makes it easier to explain, extend, and review the project.

**Expected output:** Files have predictable homes and backend components can be changed independently.

**Common beginner mistakes:** Creating duplicate files in several folders; putting secrets or virtual environments inside tracked project content; mixing dashboard display code with alert calculations.

## Phase 3: API key setup

**What to do:** Choose a weather provider and check whether your intended endpoints require an API key. If a key is required, put it in an environment variable or an untracked local `.env` file and read it on the server side. Add `.env` to `.gitignore`. Never paste a secret into dashboard code, a screenshot, or GitHub.

For this repository, Open-Meteo is configured without an API key, so live mode can be used without this phase's credential setup. If replacing it with OpenWeatherMap or WeatherAPI, configure the key according to that provider's current documentation and account plan.

**Why:** Providers use different authentication and access rules. Keeping credentials out of source code protects the account and makes deployment configuration easier.

**Expected output:** Either a documented no-key provider setup (current project) or a server-side credential that is loaded successfully without appearing in source control.

**Common beginner mistakes:** Assuming every provider requires the same key format; committing a `.env` file; exposing a key in frontend JavaScript; mistaking a missing key or restricted plan for a JSON parsing problem.

## Phase 4: Weather data fetching

**What to do:** Accept a city name, resolve it to coordinates when needed, and call the provider's current-weather and forecast endpoints. Set a timeout and handle network errors. Test with the built-in simulation when offline.

**Why:** Most forecast services request data using coordinates, while users prefer entering a recognizable city name. Timeouts prevent a slow provider from hanging requests indefinitely.

**Expected output:** A successful provider response for the requested location, or a clear error that describes a failed lookup/request. Simulation returns a clearly labeled example response without a network call.

**Common beginner mistakes:** Building a URL by concatenating user input; forgetting URL parameters/encoding; assuming network access always works; silently switching to sample data after a live request fails; confusing provider local time with UTC.

## Phase 5: JSON data parsing

**What to do:** Parse the response, check for expected fields, normalize provider-specific names and units into a stable internal structure, and represent unavailable optional values as `null`/`None`.

**Why:** APIs can omit values or change provider-specific field names. A normalized structure keeps alert and display logic independent of a particular provider's JSON format.

**Expected output:** Consistent `location`, `current`, `hourly`, `daily`, and `alerts` objects are returned by the service.

**Common beginner mistakes:** Treating missing fields as zero; relying on hard-coded array indexes without checking lengths; assuming every response is valid JSON; mixing Fahrenheit and Celsius or miles/hour and km/hour; losing timezone information.

## Phase 6: Forecast analysis

**What to do:** Select the relevant current and forecast intervals, compute summaries such as daily high/low and maximum rain chance, and keep timestamps associated with each value. Use Pandas when tabular aggregation is helpful.

**Why:** Raw provider data can be verbose. Summaries help people understand likely conditions at a glance while preserving source times for context.

**Expected output:** A concise hourly and daily forecast suitable for charts and for alert checks.

**Common beginner mistakes:** Comparing values from mismatched timestamps; analyzing only the first array value when it is not the current hour; treating precipitation probability as precipitation amount; labeling local timestamps as UTC; presenting a forecast as certain.

## Phase 7: Alert condition logic

**What to do:** Add small, clear functions that compare measurements with configurable thresholds. Include categories such as rain, heat, wind, and AQI. Add humidity or storm logic only when there is suitable provider data and clearly defined criteria. Return a severity and an explanation for each triggered condition.

**Why:** Isolated rules are easier to review and adjust than thresholds hidden inside UI code. Human-readable reasons help users understand why they saw an alert.

**Expected output:** A consistent list of alert objects, or an explicit no-elevated-risk message. The current implementation covers rain, heat, humidity, wind, and AQI using example thresholds.

**Common beginner mistakes:** Using thresholds as if they were official warnings; alerting on unavailable values; combining unlike units; generating repeated notifications every polling cycle; calling rain or high wind alone a confirmed storm; forgetting equality boundary cases.

## Phase 8: Visualization

**What to do:** Render current conditions and alerts first, then add forecast charts and a location map. Keep source, retrieval time, units, and simulation status visible. The current dashboard uses Streamlit and Plotly.

**Why:** Good labels and visuals let users scan conditions quickly and distinguish live observations from a forecast or simulation.

**Expected output:** A dashboard with current metrics, risk notifications, hourly/daily charts, and location context.

**Common beginner mistakes:** Plotting unlabeled values; using a misleading chart scale; hiding whether data is simulated; displaying stale results after the user changes city; overloading the first screen with too many charts.

## Phase 9: Report generation

**What to do:** Build a time-stamped report containing the location, source, current snapshot, forecast summary, thresholds used, and generated alerts. Start with a downloadable JSON or CSV file. If reports must persist across restarts or users, store them in SQLite first, then consider a server database as the project grows.

**Why:** A report makes the result shareable and gives users a record to review later. Persisted history supports comparisons and alert auditing.

**Expected output:** The current project downloads a CSV snapshot and saves a local copy under `outputs/`. With persistence added, this phase could also return a report ID and provide a report history endpoint.

**Common beginner mistakes:** Saving secrets with report data; omitting retrieval time or timezone; mixing simulated and live data without a source label; overwriting previous reports; assuming an in-memory cache is durable storage; storing more personal location data than needed.

## Phase 10: GitHub upload

**What to do:** Review `.gitignore`, remove secrets and local environment folders from the files to publish, add a useful README and screenshot, then initialize Git, commit, connect the GitHub repository, and push the main branch. See [GitHub & interview guide](GITHUB_AND_INTERVIEW.md) for exact commands.

**Why:** A clean public repository demonstrates the work and lets another person reproduce the project.

**Expected output:** A GitHub repository with the source, setup instructions, API examples, architecture, screenshot, limitations, and a concise project description.

**Common beginner mistakes:** Committing `.env`, API keys, `.venv`, cache files, or personal data; pushing before checking the repository contents; forgetting installation and run instructions; uploading screenshots that expose credentials or mislabel simulated conditions.

## Suggested completion checklist

- [ ] API health endpoint responds.
- [ ] Live weather returns a location and forecast, or a clear provider error.
- [ ] Simulation works without external connectivity and is labeled.
- [ ] Optional values such as AQI can be missing safely.
- [ ] Alert rules return readable explanations.
- [ ] Dashboard charts identify units and timestamps.
- [ ] Report export/history is implemented if required by the final scope.
- [ ] README, screenshot, and GitHub repository contain no secrets.
