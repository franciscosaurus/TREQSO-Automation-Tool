# TREQSO Automation Tool — Developer Guide

This document is the complete reference for anyone modifying, extending, or building this project. It covers the architecture in full, every file and its role, the complete data flow from GUI click to TREQSO page action, how to find and update Playwright locators when TREQSO changes its UI, and how to build and distribute a new release.

---

## Table of Contents

1. [Technology Stack and Prerequisites](#1-technology-stack-and-prerequisites)
2. [Repository Structure](#2-repository-structure)
3. [Architecture Overview](#3-architecture-overview)
4. [Layer 1: Python GUI — `treqso_gui.py`](#4-layer-1-python-gui--treqso_guipy)
5. [Layer 2: Python Processor — `treqso_processor.py`](#5-layer-2-python-processor--treqso_processorpy)
6. [Layer 3: TypeScript CLI — `src/cli.ts`](#6-layer-3-typescript-cli--srccllits)
7. [Layer 4: Playwright Automation — `src/treqso-automation.ts`](#7-layer-4-playwright-automation--srctreqso-automationts)
8. [Configuration and Environment](#8-configuration-and-environment)
9. [Data Flow: End to End](#9-data-flow-end-to-end)
10. [Adding a New Feature / Operation](#10-adding-a-new-feature--operation)
11. [Playwright Locators: Finding, Testing, and Updating Them](#11-playwright-locators-finding-testing-and-updating-them)
12. [Developer Setup](#12-developer-setup)
13. [Building a Release](#13-building-a-release)
14. [The Installer](#14-the-installer)
15. [Installing the Application (End-User Installer Walkthrough)](#15-installing-the-application-end-user-installer-walkthrough)
16. [Debugging and Troubleshooting the Codebase](#16-debugging-and-troubleshooting-the-codebase)
17. [Key Design Decisions and Gotchas](#17-key-design-decisions-and-gotchas)

---

## 1. Technology Stack and Prerequisites

### Runtime stack

| Component | Technology | Version |
|---|---|---|
| GUI | Python + Tkinter (ttk) | Python 3.10+ |
| Subprocess bridge | Python | — |
| CLI entry point | TypeScript / Node.js | Node.js LTS, TS 5.x |
| Browser automation | Playwright (Chromium) | `@playwright/test ^1.41.0` |
| Windows printer API | pywin32 | 311 |
| Env config | python-dotenv | 1.2.1 |
| Python bundling | PyInstaller | latest |
| Installer packaging | Inno Setup 6 | 6.x |

### Developer machine prerequisites

These are only needed on the machine that builds and packages the app. End users need none of these.

- **Python 3.10+** — for the GUI layer and PyInstaller build. Must be on PATH.
- **Node.js LTS** — for `npm install`, `tsc`, and running the TypeScript CLI during development.
- **`node_portable\node.exe`** — a portable Windows Node.js binary downloaded separately (see [Building a Release](#13-building-a-release)). This is what gets bundled into the installer for end users.
- **Inno Setup 6** — for compiling `installer_script.iss` into the setup `.exe`. Download from https://jrsoftware.org/isdl.php. Add `iscc.exe` to PATH.
- **Playwright Chromium** — installed via `npx playwright install` on the dev machine for local testing.

---

## 2. Repository Structure

```
TREQSO-Automation-Tool/
│
├── src/                          # TypeScript source (the automation engine)
│   ├── treqso-automation.ts      # All Playwright browser automation logic
│   └── cli.ts                    # CLI entry point — receives JSON, dispatches to automation
│
├── dist/                         # Compiled output from `npm run build` (gitignored)
│   ├── cli.js                    # Compiled CLI entry point
│   ├── treqso-automation.js      # Compiled automation class
│   └── *.js.map / *.d.ts         # Source maps and type declarations
│
├── node_modules/                 # npm dependencies (gitignored)
│
├── node_portable/                # Portable Node.js binary (NOT gitignored — committed)
│   ├── node.exe                  # Windows portable node binary (~30 MB)
│   └── README.txt                # Instructions for obtaining node.exe
│
├── build/                        # PyInstaller intermediate build files (gitignored)
├── installer_output/             # Inno Setup output directory (gitignored)
│
├── treqso_gui.py                 # Python GUI — all Tkinter tabs and user interaction
├── treqso_processor.py           # Python bridge — CSV parsing, subprocess management
│
├── TREQSO_Automation.spec        # PyInstaller spec — defines what goes in the .exe
├── installer_script.iss          # Inno Setup script — defines what goes in the installer
├── package.json                  # Node.js project config and scripts
├── tsconfig.json                 # TypeScript compiler config
├── requirements.txt              # Python dependencies
│
├── build_release.bat             # Full release build script (8 steps)
├── setup-smart.bat               # Developer environment setup
├── launcher-smart.bat            # Developer launcher (GUI or CLI)
│
├── .env                          # Local config — NOT committed
├── .env.template                 # Template committed to repo, copied to .env on install
│
├── sample_parts.csv              # Example data for Create Parts
├── sample_bom.csv                # Example data for Create BOMs
├── sample_edit_parts.csv         # Example data for Edit Parts
├── Parts_Template.csv            # Empty template for Create Parts
├── BOMs_Template.csv             # Empty template for Create BOMs
├── Edit_Parts_Template.csv       # Empty template for Edit Parts
│
├── icon.ico                      # Application icon
├── README_USER.md                # End-user documentation
└── README.md                     # This file
```

---

## 3. Architecture Overview

The application is built in four distinct layers that communicate in one direction. Understanding this layering is the key to understanding every part of the codebase.

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 1: Python GUI  (treqso_gui.py)                   │
│  Tkinter dark-mode interface. Handles all user input,   │
│  file selection, output console, status bar.            │
│  Owns no automation logic whatsoever.                   │
└────────────────────┬────────────────────────────────────┘
                     │  method calls
                     ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 2: Python Processor  (treqso_processor.py)       │
│  Reads CSV files. Serialises data to JSON.              │
│  Launches Node.js subprocess. Streams its stdout back   │
│  to the GUI console in real time. Reads result.json.    │
└────────────────────┬────────────────────────────────────┘
                     │  subprocess: node.exe dist/cli.js input.json
                     │  (writes automation_input.json, reads result.json)
                     ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 3: TypeScript CLI  (src/cli.ts → dist/cli.js)    │
│  Reads automation_input.json. Instantiates the          │
│  TREQSOAutomation class. Dispatches to the correct      │
│  handler. Writes result.json.                           │
└────────────────────┬────────────────────────────────────┘
                     │  method calls
                     ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 4: Playwright Automation  (treqso-automation.ts) │
│  Opens Chromium. Logs into TREQSO. Performs all         │
│  browser actions. Every locator lives here.             │
└─────────────────────────────────────────────────────────┘
```

The Python and Node.js layers communicate only through the filesystem: `automation_input.json` (Python → Node) and `result.json` (Node → Python). This means the TypeScript layer is completely decoupled from Python and can be tested independently with a raw JSON file.

All stdout produced by the Node.js process (every `console.log` in the TypeScript files) is streamed line by line back to the Python processor, which forwards it directly to the GUI console. This is what gives users real-time progress updates.

---

## 4. Layer 1: Python GUI — `treqso_gui.py`

### Responsibilities

- Renders the application window and all six tabs
- Handles all user interactions (button clicks, file selection, field input)
- Displays real-time output in the console widget
- Runs every operation in a background thread to keep the window responsive
- Manages the first-run Playwright browser download
- Reads configuration from `.env` on startup; writes it back on Save

### Key classes and methods

**`TREQSOGui.__init__`** — Sets up the entire window. Calls `_apply_dark_theme(root)` first (before any widgets exist), then builds the outer frame, title, notebook, console, and status bar. Spawns the `_ensure_playwright_browsers` daemon thread.

**`_apply_dark_theme(root)`** — Module-level function. Configures every ttk style using the `clam` base theme. All colour values are defined as module-level constants at the top of the file (`BG`, `SURFACE`, `CARD`, `ACCENT`, etc.). If you want to change the colour scheme, those constants are the only place you need to touch.

**`_make_tab_frame()`** — Returns a `ttk.Frame` with standard padding, used as the container for each notebook tab. All tab builder methods call this first.

**`_build_csv_table(parent, csv_filename)`** — Reads a CSV file and renders it as a dark-mode grid of `tk.Label` widgets. Used in Create Parts, Edit Parts, and Create BOMs tabs to show the format preview. The colours come from `TBL_H`, `TBL_ODD`, `TBL_EVEN`, `TBL_BORD`.

**`_build_instructions(parent, row, text)`** — Renders a "How to prepare your CSV" LabelFrame with step text. Shared between Create Parts and Create BOMs tabs.

**`create_*_tab()` methods** — One per tab. Each method creates a tab frame, adds it to the notebook, and lays out all the widgets for that tab using the grid geometry manager. These are the right place to add new fields, buttons, or UI text within an existing tab.

**Action handler pairs** — Every operation has a public method (e.g., `create_parts`) and a private thread worker (e.g., `_create_parts_thread`). The public method validates input and starts a `threading.Thread` targeting the private method. The private method calls `self.update_processor_config()`, then the appropriate processor method, then handles the result. This pattern must be followed for any new operations.

**`update_processor_config()`** — Reads all current GUI field values and writes them to `self.processor.config`. Also sets `self.processor.log_callback = self.log`. Must be called at the start of every thread worker, otherwise the processor uses stale settings.

**`log(message)`** — Appends text to the console widget and forces a UI update. Always called from thread workers, so the `self.root.update()` call is important — without it the console would not refresh until the thread finished.

**`_ensure_playwright_browsers()`** — Runs on a daemon thread at startup. Calls `_chromium_installed()` to check for a `chromium-*` directory under `%LOCALAPPDATA%\ms-playwright`. If absent, finds `playwright.cmd` in `node_modules/.bin/`, patches PATH to include the bundled node directory, and runs `playwright install chromium` with a 10-minute timeout.

### Adding a new tab

1. Create a `create_yourtab_tab(self)` method following the existing pattern.
2. Add a call to it in `__init__` in the correct position (tab order matters — it matches the order of `notebook.add()` calls).
3. Add a `StringVar` for any file picker: `self.your_file_var = tk.StringVar()`.
4. Add a public action method and a `_your_action_thread` worker method.
5. Wire the action button to the public method.

---

## 5. Layer 2: Python Processor — `treqso_processor.py`

### Responsibilities

- Parses CSV files into Python data structures
- Serialises data to JSON for the Node.js subprocess
- Resolves paths for node.exe and dist/cli.js (handles both dev and installed modes)
- Launches node.exe as a subprocess and streams its stdout to the GUI in real time
- Reads result.json after the subprocess exits
- Exposes one public method per operation (called by the GUI layer)

### Path resolution

Two critical helper methods handle the dual-mode path problem (running from source vs. running as a PyInstaller exe):

**`_get_app_dir()`**
```python
if getattr(sys, 'frozen', False):
    return os.path.dirname(sys.executable)  # installed: {app}/
return os.path.dirname(os.path.abspath(__file__))  # dev: project root
```
When frozen (PyInstaller exe), `sys.executable` is `{app}\TREQSO_Automation.exe`, so its dirname is `{app}\`. This is the directory where node_portable, dist, node_modules, and .env all live. In dev mode it returns the project root, which is the same layout.

**`_get_node_path()`**
```python
bundled = os.path.join(self._get_app_dir(), 'node_portable', 'node.exe')
if os.path.exists(bundled):
    return bundled
return 'node'  # fall back to system PATH for dev machines
```
This is what makes the app portable. End users always get the bundled node.exe. Developers get their system node.

### The subprocess execution (`execute_automation`)

This is the core of the processor. The full flow:

1. Builds a `command` dict: `{ action, config, data }`.
2. Writes it to `automation_input.json` in `app_dir`.
3. Resolves `node_exe`, `cli_path`, `input_file`, `result_file` — all absolute paths.
4. Builds `env` from `os.environ.copy()`, prepends the node directory to PATH.
5. Opens the subprocess with `subprocess.Popen` (not `subprocess.run`) so stdout can be streamed.
6. Iterates `process.stdout` line by line, calling `log_callback` for each non-empty line.
7. After the stdout loop, calls `process.wait(timeout=3600)` then drains stderr.
8. Reads and returns `result.json`.
9. In the `finally` block, deletes `automation_input.json`.

**Why Popen instead of run?** `subprocess.run(capture_output=True)` buffers all output and only delivers it after the process exits. For an operation that might process 50 parts over 10 minutes, users would see nothing until the end. `Popen` with iteration over `process.stdout` delivers each line the moment Node writes it.

**The log_callback pattern** — `execute_automation` accepts an optional `log_callback` parameter. If `None`, it falls back to `getattr(self, 'log_callback', None)`. The GUI sets `self.processor.log_callback = self.log` in `update_processor_config()`. This means Node's console output flows: TypeScript `console.log` → Node stdout → Python stdout iteration → `log_callback(line)` → `self.log(line)` → Tkinter console widget.

### CSV loading methods

**`load_parts_from_csv`** — Reads all rows into `Part` dataclass instances. All columns are required.

**`load_bom_from_csv`** — Groups rows by `assembly_part_number` into a dict of `{assembly: [BOMLine, ...]}`. Rows must be sorted by assembly (all lines for assembly A before assembly B).

**`load_part_updates_from_csv`** — The most flexible loader. First reads `reader.fieldnames` to discover which columns are present, intersects with `editable_fields`, then for each row builds a dict containing only non-blank values for present fields. `partNumber` is always required. All other fields are optional — if the column isn't in the file, it's never included in any row's dict, which means `editPart` in TypeScript will never touch that field.

### Adding a new operation

1. Add a CSV loader method if the operation needs CSV input.
2. Add a public method (e.g., `def your_operation(self, ...) -> Dict[str, Any]`) that builds a `data` dict and calls `self.execute_automation('your_action', data)`.
3. The action string must match exactly what the CLI switch case expects.

---

## 6. Layer 3: TypeScript CLI — `src/cli.ts`

### Responsibilities

- Entry point for the Node.js subprocess
- Reads and parses `automation_input.json`
- Instantiates `TREQSOAutomation` with the config
- Calls `startBrowser()` and `login()` once
- Dispatches to the correct handler based on `action`
- Calls `automation.close()` in `finally`
- Writes the result dict to `result.json` via `writeResult()`

### The action union type

```typescript
action: 'create_parts' | 'edit_parts' | 'create_bom' | 'replace_part' | 'login_test' | 'print_MOs'
```

Every new operation needs its string added here. TypeScript will then enforce that the switch statement handles it.

### The writeResult function

```typescript
function writeResult(result: any): void {
    const resultPath = path.join(process.cwd(), 'result.json');
    fs.writeFileSync(resultPath, JSON.stringify(result, null, 2));
}
```

`process.cwd()` is the `app_dir` passed as `cwd` by the Python subprocess call. The result dict must always include at least `{ success: boolean }`. Operations that process multiple items should also include a `summary` object with `{ total, successful, failed, failures: string[] }` — this is what the Python layer reads to build the success/warning/error popup.

### Adding a new action

1. Add the action string to the `CLICommand.action` union type.
2. Add a data interface (e.g., `interface YourActionData { ... }`).
3. Add a `handleYourAction` async function.
4. Add a `case 'your_action':` to the switch in `processCommand`.
5. Call `writeResult(...)` at the end of your handler.

---

## 7. Layer 4: Playwright Automation — `src/treqso-automation.ts`

### Responsibilities

This file contains every single browser automation action. It is the only file that touches TREQSO directly. All Playwright locators live here and nowhere else.

### Class structure

**`TREQSOAutomation`** — The main class. Holds `browser`, `context`, `page`, and `config` as private members.

**`startBrowser()`** — Launches Chromium with `--kiosk-printing` (suppresses the browser's print dialog so the OS print dialog can take over). Sets `page.setDefaultTimeout(60000)` — a 60-second timeout for all Playwright actions.

**`login()`** — Navigates to the TREQSO URL, selects Windows Authentication (`#rbWindows`), clicks Login, waits for `networkidle`, then checks the company text. If the company doesn't match `config.company`, clicks "Switch Company", selects the correct company from the dropdown, and logs in again.

**`WaitToLoad()`** — A custom wait helper used throughout the file. Waits 1 second (for the loading indicator to appear if it's going to), then waits for the loading spinner image (`getByAltText('Loading...')`) to become hidden. This is called after almost every significant browser action.

### Key methods and their locator patterns

#### `printMOs(referenceID)`
Calls `navigateAndProcessMOs` to collect all MO numbers, then for each:
- Navigates to `/MFG/MfgOrderMaint.aspx`
- Filters by MO ID using `getByAltText('Filter Mfg Order ID column')`
- Clicks the Select button with `getByTitle('Select')`
- Clicks the Print Order link with `getByRole('link', { name: 'Print Order' })`
- The print form is in an iframe: `locator('iframe[name="winPrintOrder"]').contentFrame()`
- Inside that frame, clicks the Print button
- Sets up `page.waitForEvent('popup')` before the click to capture the print preview window
- Calls `evaluate(() => window.print())` on the popup to trigger the actual print

#### `navigateAndProcessMOs(referenceID)`
Collects all MO IDs under a reference, handling pagination:
- Filters the MO grid by reference ID and status "Open"
- Reads the row count text to determine number of pages
- For multi-page results, clicks the `>` next-page button and iterates

#### `createPart(part)`
- Navigates to `/IMS/PartMaint.aspx?IsNew=Yes`
- Fills fields using `#ContentPlaceHolder1_txtPartNumber`, `#ContentPlaceHolder1_txtPartDescription`, etc.
- Phase number defaults to `'110 (Parts)'` if not supplied
- Saves with `getByRole('button', { name: 'Add', exact: true })`

#### `navigateToEditPart(partNumber)`
- Navigates to `/IMS/PartMaint.aspx` (the list view, not the add view)
- Filters by `getByAltText('Filter Part Number column')`
- Clicks `getByTitle('Select').first()` to open the record
- Returns `false` if no Select button is visible (part not found)

#### `editPart(update)`
The most complex method due to the `partType` special case:

For `partType`, a normal fill would not work because TREQSO treats a type change as a significant action. The method:
1. Reads the current value with `.inputValue()`
2. Only proceeds if the new value differs from the current one
3. Clicks `getByRole('link', { name: 'Change Type' })` to open the Change Type iframe
4. Uses `frameLocator('iframe[name="winChangeType"]')` to interact inside the frame — this is the iframe pattern that solved the "iframe disappears" problem
5. Fills the dropdown inside the frame
6. Registers a one-time `page.once('dialog', ...)` handler to auto-accept the confirmation dialog
7. Clicks the "Change Type" button inside the frame

For all other fields, a direct `.fill()` on the appropriate locator is used.

Saves with `getByRole('button', { name: 'Update', exact: true })`.

#### `navigateToBOM(partNumber, firstPart?, component?)`
Three modes controlled by the optional parameters:
- `firstPart` present → creating a new BOM (navigates to Add BOM flow)
- `component = true` → finding assemblies that contain a part (Detail Finder mode)
- Neither → opening an existing BOM for editing (filter by parent part number)

#### `massReplaceBOMParts(oldPartNumber, newPartNumber, updateQuantity?)`
1. Calls `processAssemblyNumbers` to find all BOMs containing `oldPartNumber`
2. For each assembly: navigates to its BOM, expands to show All rows, finds the row with `hasText: oldPartNumber`, reads its sequence number, option, and quantity
3. Clicks Edit Detail, deletes the old line (auto-accepts the confirm dialog with `page.once`), adds a new detail with the new part number, restores the original sequence and quantity, saves

### Interfaces

```typescript
interface Part           // Used for creating new parts — all required fields
interface PartUpdate     // Used for editing — partNumber required, all else optional
interface BOMLine        // A single component row in a BOM
interface TREQSOConfig   // url, company, headless?, slowMo?
```

---

## 8. Configuration and Environment

The `.env` file at the application root (or `{app}\.env` when installed) controls all connection settings. It is read at Python startup via `load_dotenv()` and accessed with `os.getenv()`.

`.env.template` (the version committed to the repo):
```
TREQSO_URL=https://dtetreqso.douglasdynamics.int/Treqso
COMPANY=CargoTest
TREQSO_HEADLESS=false
TREQSO_SLOW_MO=0
```

| Variable | Purpose | Default |
|---|---|---|
| `TREQSO_URL` | Full URL to the TREQSO instance, including path | `https://dtetreqso.douglasdynamics.int/Treqso` |
| `COMPANY` | Company name as displayed in TREQSO after login | `CargoTest` |
| `TREQSO_HEADLESS` | `true` = browser runs invisible; `false` = visible | `false` |
| `TREQSO_SLOW_MO` | Milliseconds of delay between every browser action | `0` |

The config is passed from Python to Node.js as part of `automation_input.json` — the `config` key in that JSON becomes the `TREQSOConfig` object in TypeScript. No environment variables are read by the Node.js layer directly.

The Inno Setup installer copies `.env.template` to `{app}\.env` **only if `.env` does not already exist** (`Flags: onlyifdoesntexist`). This means reinstalls and upgrades preserve the user's existing configuration.

---

## 9. Data Flow: End to End

Here is a complete trace of what happens when a user clicks "Create Parts" with a CSV file selected.

**1. GUI layer (treqso_gui.py)**
```
User clicks "Create Parts"
→ create_parts() validates the file path
→ clear_console(), log("=== Creating Parts ==="), update_status("Creating parts...")
→ threading.Thread(target=_create_parts_thread, args=(csv_file,)).start()
```

**2. Thread worker (treqso_gui.py)**
```
_create_parts_thread(csv_file):
→ update_processor_config()       # writes GUI values to processor.config, sets log_callback
→ processor.create_parts_from_csv(csv_file)
```

**3. Processor (treqso_processor.py)**
```
create_parts_from_csv(csv_file):
→ parts = load_parts_from_csv(csv_file)   # returns list of Part dataclasses
→ data = {'parts': [part.to_dict() for part in parts]}
→ execute_automation('create_parts', data)
```

**4. execute_automation (treqso_processor.py)**
```
→ command = { 'action': 'create_parts', 'config': self.config, 'data': data }
→ write command to automation_input.json
→ subprocess.Popen([node_exe, cli_path, input_file], stdout=PIPE, cwd=app_dir)
→ for each line of stdout: print(line); log_callback(line)   ← real-time console output
→ process.wait(timeout=3600)
→ return json.load(result.json)
```

**5. CLI entry point (dist/cli.js ← src/cli.ts)**
```
→ reads automation_input.json
→ const automation = new TREQSOAutomation(command.config)
→ await automation.startBrowser()
→ await automation.login()
→ case 'create_parts': await handleCreateParts(automation, command.data)
→ finally: await automation.close()
```

**6. Handler (src/cli.ts)**
```
handleCreateParts(automation, data):
→ results = await automation.batchCreateParts(data.parts)
→ console.log("=== Batch Part Creation Summary ===")   ← streams to Python console
→ writeResult({ success, results, summary })             ← writes result.json
```

**7. Playwright (src/treqso-automation.ts)**
```
batchCreateParts(parts):
→ for each part: await createPart(part)
    → page.goto('/IMS/PartMaint.aspx?IsNew=Yes')
    → fill each field
    → click Add
    → WaitToLoad()
    → console.log("Part X created successfully!")     ← streams to Python console
```

**8. Back in the GUI thread**
```
_create_parts_thread receives the result dict from execute_automation
→ reads result.get('success'), result.get('summary')
→ log("\n=== Results ===")
→ update_status("Parts creation completed")
→ messagebox.showinfo("Success", ...)   ← pops up on the main thread via tkinter
```

---

## 10. Adding a New Feature / Operation

Adding a new operation requires changes in all four layers. Here is the complete checklist using a hypothetical "Archive Part" operation as an example.

### Step 1 — Define the TypeScript interface (treqso-automation.ts)

If the operation needs a new data shape, add an interface:
```typescript
export interface ArchivePartData {
  partNumber: string;
  reason?: string;
}
```

### Step 2 — Implement the automation method (treqso-automation.ts)

Add a method to `TREQSOAutomation`:
```typescript
async archivePart(partNumber: string, reason?: string): Promise<boolean> {
    if (!this.page) throw new Error('Browser not started');
    try {
        console.log(`Archiving part: ${partNumber}`);
        // ... Playwright actions ...
        return true;
    } catch (error) {
        console.error(`Error archiving part ${partNumber}:`, error);
        await this.takeScreenshot(`error_archive_part_${partNumber}.png`);
        return false;
    }
}
```

### Step 3 — Add the CLI handler (cli.ts)

Add to the action union:
```typescript
action: '...' | 'archive_part';
```

Add the data interface:
```typescript
interface ArchivePartData {
    partNumber: string;
    reason?: string;
}
```

Add the handler function:
```typescript
async function handleArchivePart(
    automation: TREQSOAutomation,
    data: ArchivePartData
): Promise<void> {
    const success = await automation.archivePart(data.partNumber, data.reason);
    writeResult({ success, partNumber: data.partNumber });
}
```

Add the switch case:
```typescript
case 'archive_part':
    await handleArchivePart(automation, command.data as ArchivePartData);
    break;
```

### Step 4 — Add the processor method (treqso_processor.py)

```python
def archive_part(self, part_number: str, reason: str = None) -> Dict[str, Any]:
    data = {'partNumber': part_number}
    if reason:
        data['reason'] = reason
    return self.execute_automation('archive_part', data)
```

If it needs CSV input, add a loader method following the pattern of `load_part_updates_from_csv`.

### Step 5 — Add the GUI tab and handlers (treqso_gui.py)

1. Add `self.create_archive_part_tab()` call in `__init__` at the desired position.
2. Implement `create_archive_part_tab(self)`.
3. Implement `archive_part(self)` (the public action method).
4. Implement `_archive_part_thread(self, ...)` (the background thread worker).

### Step 6 — Build and test

```
npm run build         # compile TypeScript
launcher-smart.bat    # launch from source to test
```

---

## 11. Playwright Locators: Finding, Testing, and Updating Them

This is the most maintenance-heavy part of the codebase. If TREQSO updates its web interface, element IDs, button labels, or page structure can change, causing locators to fail. This section explains how locators work, where they all are, and how to find replacements.

### What is a locator?

A Playwright locator is a reference to one or more elements on the page. When an action is performed (fill, click, etc.), Playwright resolves the locator at that moment and retries until the element exists, is visible, and is actionable — or until the timeout (60 seconds by default) is reached.

All locators in this codebase are in `src/treqso-automation.ts`.

### The three locator types used in this project

**1. ID-based locators** — the most specific and the most brittle if TREQSO changes its generated IDs:
```typescript
this.page.locator('#ContentPlaceHolder1_txtPartNumber')
this.page.locator('#ctl00_ContentPlaceHolder1_ddlPartCategory_Input')
```

**2. Role-based locators** — more stable because they depend on accessible role and text, not IDs:
```typescript
this.page.getByRole('button', { name: 'Add', exact: true })
this.page.getByRole('link', { name: 'Print Order' })
this.page.getByRole('checkbox').first()
```

**3. Alt-text locators** — used for filter inputs on grid columns:
```typescript
this.page.getByAltText('Filter PartNumber column')
this.page.getByAltText('Filter ParentPartNumber column')
```

### Complete locator inventory

| Location in code | Selector | What it targets |
|---|---|---|
| `login()` | `#rbWindows` | Windows Auth radio button |
| `login()` | `getByRole('button', { name: 'Login' })` | Login button (used twice) |
| `login()` | `getByText('Company:')` | Company display text |
| `login()` | `getByRole('button', { name: 'Switch Company' })` | Company switch button |
| `login()` | `#ddlDatabases_Input` | Company dropdown |
| `WaitToLoad()` | `getByAltText('Loading...')` | Loading spinner image |
| `navigateAndProcessMOs()` | `getByAltText('Filter Order Status column')` | MO status filter |
| `navigateAndProcessMOs()` | `getByAltText('Filter Order Reference ID')` | MO reference filter |
| `navigateAndProcessMOs()` | `#ctl00_ContentPlaceHolder1_Finder1_gridFinder_ctl00` | MO grid container |
| `navigateAndProcessMOs()` | `getByText('records found')` | Page count text |
| `navigateAndProcessMOs()` | `getByRole('button', { name: '>', exact: true })` | Next page button |
| `printMOs()` | `getByAltText('Filter Mfg Order ID column')` | MO ID filter |
| `printMOs()` | `getByTitle('Select')` | Select record button |
| `printMOs()` | `getByRole('link', { name: 'Print Order' })` | Print Order link |
| `printMOs()` | `iframe[name="winPrintOrder"]` | Print form iframe |
| `printMOs()` | (inside iframe) `getByRole('button', { name: 'Print', exact: true })` | Print button in iframe |
| `createPart()` | `#ContentPlaceHolder1_txtPartNumber` | Part number input |
| `createPart()` | `#ContentPlaceHolder1_txtPartDescription` | Short description |
| `createPart()` | `#ContentPlaceHolder1_txtPlainFullDescription` | Full description |
| `createPart()` | `#ctl00_ContentPlaceHolder1_ddlPartCategory_Input` | Part category dropdown |
| `createPart()` | `#ctl00_ContentPlaceHolder1_ddlProductCode_Input` | Product code dropdown |
| `createPart()` | `#ctl00_ContentPlaceHolder1_ddlSalesGroup_Input` | Sales group dropdown |
| `createPart()` | `#ctl00_ContentPlaceHolder1_ddlPartType_Input` | Part type dropdown |
| `createPart()` | `#ctl00_ContentPlaceHolder1_ddlPhaseNumber_Input` | Phase number dropdown |
| `createPart()` | `#ctl00_ContentPlaceHolder1_ddlOrderType_Input` | Order type dropdown |
| `createPart()` | `#ctl00_ContentPlaceHolder1_ddlUOM1_Input` | Unit of measure dropdown |
| `createPart()` | `#ctl00_ContentPlaceHolder1_numStandardCost` | Standard cost input |
| `createPart()` | `#ctl00_ContentPlaceHolder1_ddlDefaultCostField_Input` | Default cost field dropdown |
| `createPart()` | `getByRole('button', { name: 'Add', exact: true })` | Save new part button |
| `navigateToEditPart()` | `getByAltText('Filter Part Number column')` | Part list filter |
| `navigateToEditPart()` | `getByTitle('Select').first()` | Select part from list |
| `editPart()` | `#ctl00_ContentPlaceHolder1_ddlPartStatus_Input` | Part status dropdown |
| `editPart()` | `getByRole('link', { name: 'Change Type' })` | Change Type link |
| `editPart()` | `iframe[name="winChangeType"]` | Change Type iframe |
| `editPart()` | (inside iframe) `#ctl00_ContentPlaceHolder1_ddlPartType_Input` | Part type inside iframe |
| `editPart()` | (inside iframe) `getByRole('button', { name: 'Change Type' })` | Confirm change button |
| `editPart()` | `getByRole('button', { name: 'Update', exact: true })` | Save edited part button |
| `navigateToBOM()` | `getByRole('button', { name: 'Add BOM' })` | Create new BOM button |
| `navigateToBOM()` | `#ctl00_ContentPlaceHolder1_txtBOMOptionNumber` | BOM option number |
| `navigateToBOM()` | `#ctl00_ContentPlaceHolder1_txtParentPart_Input` | Parent (assembly) part input |
| `navigateToBOM()` | `#ctl00_ContentPlaceHolder1_txtComponentPart_Input` | Component part input |
| `navigateToBOM()` | `#ctl00_ContentPlaceHolder1_txtQuantity` | Quantity input |
| `navigateToBOM()` | `getByRole('checkbox').first()` | "Is Assembly?" checkbox |
| `navigateToBOM()` | `getByRole('button', { name: 'Add' })` | Add first BOM line |
| `navigateToBOM()` | `getByAltText('Filter ParentPartNumber column')` | BOM parent filter |
| `navigateToBOM()` | `#ctl00_ContentPlaceHolder1_gridFinder1_ctl00_ctl04_gbcSelectRecord` | Select BOM record |
| `navigateToBOM()` | `getByRole('button', { name: 'Detail Finder' })` | Open component finder |
| `navigateToBOM()` | `getByAltText('Filter ComponentPartNumber column')` | Component filter |
| `createBOM()` | `getByRole('button', { name: 'Add Detail' })` | Add BOM line button |
| `createBOM()` | `#ctl00_ContentPlaceHolder1_txtBOMSequenceNumber` | BOM sequence number |
| `createBOM()` | `getByRole('button', { name: 'Save' })` | Save BOM line |
| `processAssemblyNumbers()` | `#ctl00_ContentPlaceHolder1_gridFinder2_ctl00` | Component finder grid |
| `processAssemblyNumbers()` | `getByAltText('Edit Record')` | Row with edit button |
| `processAssemblyNumbers()` | `getByText('items in')` | Page count text |
| `processAssemblyNumbers()` | `getByTitle('Next Page', { exact: true })` | Next page button |
| `massReplaceBOMParts()` | `#ctl00_ContentPlaceHolder1_rgDetail_ctl00_ctl03_ctl02_PageSizeComboBox` | Page size combobox |
| `massReplaceBOMParts()` | `getByText('All', { exact: true })` | "All" page size option |
| `massReplaceBOMParts()` | `#ctl00_ContentPlaceHolder1_rgDetail_ctl00` | BOM detail grid |
| `massReplaceBOMParts()` | `getByAltText('Edit Detail')` | Edit BOM line button |
| `massReplaceBOMParts()` | `getByRole('button', { name: 'Delete' })` | Delete BOM line |

### How to find a new locator when one breaks

**Method 1: Playwright Inspector (recommended)**

Run the codegen tool against the TREQSO instance. It watches your clicks and generates locator code automatically:

```bash
npx playwright codegen https://dtetreqso.douglasdynamics.int/Treqso
```

This opens a browser window and a code window side by side. Click the element you need, and Playwright will suggest the best locator for it. Copy the generated locator into `treqso-automation.ts`.

**Method 2: Browser DevTools**

1. Open TREQSO in Chrome.
2. Right-click the element → Inspect.
3. In the Elements panel, look at the element's `id`, `name`, `alt`, `title`, `role`, and `aria-label` attributes.
4. Choose the most stable attribute: `id` if it's static, `aria-label` or `title` for buttons, `alt` for images/filter inputs.

**Method 3: Playwright's `page.pause()`**

Add `await this.page.pause();` anywhere in the TypeScript code, compile, and run. The Playwright Inspector opens mid-execution and lets you explore the live page and test locators interactively.

### The most common locator failure: ASP.NET control IDs

TREQSO is an ASP.NET WebForms application. The IDs of form controls like `ctl00_ContentPlaceHolder1_ddlPartCategory_Input` are generated by the ASP.NET framework and can change if:
- The page's control hierarchy is reorganised
- A new server control is inserted above the one you're targeting (shifts the `ctl00_NN` numbering)
- The control is moved to a different content placeholder

**When an ID locator breaks:**
1. Navigate to the affected page in Chrome.
2. Open DevTools, click the element.
3. Check whether the `id` has changed (different numbers in the ctl chain).
4. If the new ID follows the same pattern, update it directly.
5. If the control no longer has a stable ID, consider switching to a role-based or label-based locator: `this.page.getByLabel('Part Category')` or `this.page.locator('input[name="PartCategory"]')`.

### The iframe pattern

Two operations use iframes: Print MOs and Edit Parts (Change Type). The pattern for both is:

```typescript
// For interacting with content inside a named iframe:
const frame = this.page.frameLocator('iframe[name="iframeName"]');
await frame.locator('#someElement').fill('value');
await frame.getByRole('button', { name: 'Confirm' }).click();

// For content that triggers a popup window (different from an iframe):
const popupPromise = this.page.waitForEvent('popup');
await this.page.getByRole('button', { name: 'Open Print Preview' }).click();
const popup = await popupPromise;
await popup.waitForLoadState('networkidle');
await popup.evaluate(() => window.print());
```

The key distinction: `frameLocator` is for content embedded in the page via `<iframe>`. `waitForEvent('popup')` is for content that opens in a new browser window. Print MOs uses both — the print options form is in an iframe within the main page, and the actual print preview opens as a popup from clicking the Print button inside that iframe.

---

## 12. Developer Setup

Run `setup-smart.bat` from the project root. It will:
1. Locate Python (tries `python`, `py`, `python3`, then common install paths)
2. Verify Node.js is on PATH
3. Run `npm install`
4. Run `npx playwright install` (downloads Chromium to `%LOCALAPPDATA%\ms-playwright`)
5. Install Python dependencies (`python-dotenv`, `pywin32`)
6. Run `npm run build` (compiles TypeScript to `dist/`)
7. Copy `.env.template` to `.env` if `.env` does not exist

**After setup:**
1. Edit `.env` with the correct `TREQSO_URL` and `COMPANY`.
2. Run `launcher-smart.bat` → option 1 to launch the GUI from source.
3. Click Test Connection in the Settings tab to verify everything works.

### Running without the launcher

```bat
# Launch the GUI directly
python treqso_gui.py

# Or test the Node.js CLI directly (useful for isolating automation issues)
node dist/cli.js test_input.json
```

Where `test_input.json` is:
```json
{
  "action": "login_test",
  "config": {
    "url": "https://dtetreqso.douglasdynamics.int/Treqso",
    "company": "CargoTest",
    "headless": false,
    "slowMo": 0
  },
  "data": {}
}
```

### TypeScript watch mode

During development, run `npm run watch` in a separate terminal. This continuously recompiles TypeScript as you save changes, so you never need to run `npm run build` manually. The `dist/` directory is always up to date.

---

## 13. Building a Release

Run `build_release.bat` from the project root. The script runs 8 steps:

| Step | What it does |
|---|---|
| 1 | Verifies `node_portable\node.exe` exists — exits with instructions if not |
| 2 | Deletes `dist\TREQSO_Automation.exe`, `build\`, and `installer_output\` |
| 3 | Installs/upgrades Python dependencies from `requirements.txt` + PyInstaller |
| 4 | Runs `npm install` |
| 5 | Verifies required data files (`.env.template`, `sample_parts.csv`, `sample_bom.csv`) exist |
| 6 | Runs `npm run build` to compile TypeScript |
| 7 | Runs `python -m PyInstaller TREQSO_Automation.spec --clean --noconfirm` |
| 8 | Runs `iscc installer_script.iss` if Inno Setup is available |

**Output:**
- `dist\TREQSO_Automation.exe` — the standalone Python executable (can be run directly but needs node_portable, dist/, node_modules/ next to it)
- `installer_output\TREQSO_Automation_Setup_v1.0.2.exe` — the self-contained installer

### Obtaining node_portable\node.exe

This file is not auto-downloaded. Download it once and commit it:

1. Go to https://nodejs.org/en/download
2. Choose: **Prebuilt Binaries → Windows → LTS → x64 → Binary (.zip)**
3. Extract the zip
4. Copy just `node.exe` from the root of the extracted folder to `node_portable\node.exe` in the project root
5. The file is approximately 30 MB

### Bumping the version number

Version is defined in two places — update both together:

| File | Location | Current value |
|---|---|---|
| `package.json` | `"version"` field | `"1.0.2"` |
| `installer_script.iss` | `#define MyAppVersion` | `"1.0.2"` |

The build script echoes the installer filename as `v2.1.0` in one place (a leftover from a previous version string in the echo output) — this is cosmetic only and does not affect the actual output filename, which is generated by Inno Setup from `#define MyAppVersion`.

### What PyInstaller bundles vs. what the installer bundles separately

This distinction is important. Getting it wrong means the exe works from `build_release.bat` output but fails after installation, or vice versa.

**Inside `TREQSO_Automation.exe` (via PyInstaller spec):**
- Python runtime
- `treqso_gui.py` and `treqso_processor.py` (as compiled bytecode)
- `python-dotenv`, `pywin32` and their dependencies
- `tkinter` and all standard library modules
- `sample_parts.csv`, `sample_bom.csv`, `sample_edit_parts.csv` (as `datas`)
- `Parts_Template.csv`, `BOMs_Template.csv`, `Edit_Parts_Template.csv`
- `.env.template`

**Not inside the exe — placed by the Inno Setup installer separately:**
- `node_portable\node.exe` → `{app}\node_portable\node.exe`
- `dist\cli.js` and `dist\treqso-automation.js` → `{app}\dist\`
- `node_modules\*` → `{app}\node_modules\`
- `.env.template` → `{app}\.env` (only if `.env` doesn't exist)
- Sample CSVs and templates → `{app}\`
- `README_USER.md` → `{app}\`

When `treqso_processor._get_app_dir()` returns `dirname(sys.executable)`, it points to `{app}\` — the directory where the Inno Setup installer placed all of the above. This is how `node.exe`, `dist\cli.js`, and `node_modules` are found at runtime.

The sample CSVs are embedded in the exe (for the GUI preview tables) **and** placed on disk by the installer (for user access via Start Menu). Both copies are needed.

---

## 14. The Installer

`installer_script.iss` is an Inno Setup 6 script. To compile it manually (outside `build_release.bat`):

```bat
iscc installer_script.iss
```

Output goes to `installer_output\TREQSO_Automation_Setup_v1.0.2.exe`.

### Key configuration

```ini
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
```
This GUID uniquely identifies the application to Windows. Do **not** change it unless you want Windows to treat the new installer as a completely different application (users would end up with two entries in Add/Remove Programs and the old installation would not be upgraded).

```ini
DefaultDirName={autopf}\{#MyAppName}
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
```
Installs to `C:\Program Files\TREQSO Automation Tool` by default. Requires admin but allows the user to override to a per-user install path.

```ini
Source: ".env.template"; DestDir: "{app}"; DestName: ".env"; Flags: onlyifdoesntexist uninsneveruninstall
```
Copies `.env.template` as `.env` only if `.env` doesn't already exist. The `uninsneveruninstall` flag means the uninstaller leaves `.env` behind (to preserve the user's credentials across reinstalls). The `[UninstallDelete]` section has an explicit entry to delete it if you want to clean it up: `Type: files; Name: "{app}\.env"`.

```ini
Source: "node_modules\*"; DestDir: "{app}\node_modules"; Flags: ignoreversion recursesubdirs createallsubdirs
```
Copies the entire pre-built `node_modules` directory. This is what makes installation work without an internet connection — no `npm install` is run on the user's machine.

### Adding new files to the installer

For a new template or sample file, add two lines to `installer_script.iss`:

```ini
; In [Files]:
Source: "your_new_file.csv"; DestDir: "{app}"; Flags: ignoreversion

; In [Icons] if you want a Start Menu shortcut:
Name: "{group}\Sample Files\Your New File"; Filename: "{app}\your_new_file.csv"
```

And add the file to the PyInstaller spec's `required_files` or `optional_files` list so it's also embedded in the exe for GUI preview:

```python
optional_files = [
    ...
    ('your_new_file.csv', '.'),
]
```

---

## 15. Installing the Application (End-User Installer Walkthrough)

For reference when testing releases or walking a user through installation:

1. Double-click `TREQSO_Automation_Setup_v1.0.2.exe`. Click **Yes** on the UAC prompt.
2. **Welcome** — Click Next.
3. **Select Destination Location** — Default is `C:\Program Files\TREQSO Automation Tool`. Leave as-is unless IT requires a different path. Click Next.
4. **Select Additional Tasks** — Desktop shortcut is unchecked by default. Click Next.
5. **Ready to Install** — Click Install. The installer copies ~200–300 MB of files (node_modules is large). This takes 30–60 seconds.
6. **Completing Setup** — Two post-install options:
   - **Configure TREQSO connection settings** — Opens `.env` in Notepad. The TREQSO URL is already pre-filled correctly. Only change `COMPANY` if needed.
   - **Launch TREQSO Automation Tool** — Opens the app immediately.
7. Click Finish.
8. On first launch, the app automatically downloads the Playwright Chromium browser (~150 MB, one time only). Progress is shown in the Output Console.

### Installed file layout

```
C:\Program Files\TREQSO Automation Tool\
├── TREQSO_Automation.exe       ← main application
├── node_portable\
│   └── node.exe                ← bundled Node.js runtime
├── dist\
│   ├── cli.js                  ← compiled TypeScript CLI
│   └── treqso-automation.js    ← compiled automation class
├── node_modules\               ← pre-built npm packages
├── .env                        ← user's connection settings
├── sample_parts.csv
├── sample_bom.csv
├── sample_edit_parts.csv
├── Parts_Template.csv
├── BOMs_Template.csv
├── Edit_Parts_Template.csv
└── README_USER.md
```

Playwright Chromium is downloaded separately to:
```
C:\Users\<username>\AppData\Local\ms-playwright\chromium-<version>\
```
This is per-user, not per-install, so it is not removed by uninstalling the app.

---

## 16. Debugging and Troubleshooting the Codebase

### Watching the browser during development

The easiest way to debug an automation problem is to run with `TREQSO_HEADLESS=false` and `TREQSO_SLOW_MO=500` in `.env`. This makes the browser visible and adds a half-second delay between every action. You can watch exactly where it fails.

### Isolating the Node.js layer

To test automation logic without the GUI, write a test JSON file and run it directly:

```bash
node dist/cli.js my_test_input.json
```

This lets you iterate on TypeScript changes quickly without rebuilding the Python exe.

### Adding temporary debug logging

Add `console.log(...)` calls anywhere in the TypeScript files. Rebuild with `npm run build`. When run through the GUI, these appear in the Output Console in real time. When run directly with `node dist/cli.js`, they appear in the terminal.

### Using page.pause() for interactive debugging

Add `await this.page.pause();` at any point in `treqso-automation.ts`, rebuild, and run. The Playwright Inspector UI opens, pausing execution. You can step through actions, inspect element properties, and test locators live.

Remove before committing.

### Reading result.json directly

After any run (successful or not), `result.json` is written to the app directory. On a dev machine this is the project root. Inspect it to see exactly what the Node.js layer reported.

### Common errors and causes

| Symptom | Likely cause |
|---|---|
| `"Could not launch node executable"` | `node_portable\node.exe` missing. Run as installed: get it from nodejs.org. Run from source: verify system Node.js is on PATH. |
| `"No result file generated"` | The Node.js process crashed before writing `result.json`. Run `node dist/cli.js` directly to see the raw error. |
| Locator timeout (60s) | An element wasn't found. The TREQSO page structure may have changed. Use Playwright Inspector or DevTools to find the new locator. |
| Loading spinner never disappears | `WaitToLoad()` is waiting on `getByAltText('Loading...')`. If TREQSO changed the alt text of its loading image, this will hang. Check the current alt text in DevTools. |
| iframe content disappears | The button that opens the iframe was clicked without a `frameLocator` waiting. See the iframe pattern in section 11. |
| Wrong company after login | `COMPANY` in `.env` doesn't match TREQSO's display exactly. Case and spacing must be identical. |
| `partType` change fails | The "Change Type" iframe may have a different `name` attribute on the current TREQSO version. Check with DevTools: right-click the iframe → Inspect → find the `name` attribute. |

---

## 17. Key Design Decisions and Gotchas

**Why Python + Node.js instead of one language?**
The GUI is Tkinter (Python's built-in GUI framework) because packaging a Python GUI into a Windows exe is well-understood and produces a small, clean installer. Playwright's Node.js/TypeScript API is significantly more capable and better documented than its Python bindings. The two-process architecture lets each language do what it's best at.

**Why write through a JSON file instead of stdin/stdout?**
Two reasons. First, the automation data (lists of parts, BOM structures) can be arbitrarily large and complex — passing structured data as JSON through a temp file is more reliable than escaping it for stdin. Second, `result.json` persists on disk after the process exits, which makes debugging much easier — you can always inspect exactly what the Node process returned.

**Why stream stdout instead of capturing it?**
Operations that process many records can take 10–30 minutes. Users need real-time feedback. `subprocess.Popen` with line-by-line stdout iteration is the only way to achieve this in Python without introducing async complexity.

**Why does `WaitToLoad()` wait 1 second before checking the spinner?**
TREQSO's loading spinner sometimes doesn't appear immediately after an action — there's a brief delay before the spinner renders. If `waitFor({state: 'hidden'})` is called before the spinner appears, it sees "spinner is already hidden" (because it hasn't appeared yet) and returns immediately, then the next action fires before the page is actually ready. The 1-second timeout ensures the spinner has had time to appear if it's going to.

**Why does `pressSequentially` get used for part number inputs instead of `fill`?**
TREQSO uses autocomplete dropdowns for part number inputs. `fill()` writes the value directly to the field's value property without triggering keyboard events, so the autocomplete never fires. `pressSequentially()` types character by character, simulating real keypresses, which triggers the autocomplete logic. The `waitForTimeout(750)` or `waitForTimeout(1000)` after it gives the autocomplete time to load suggestions before the next action.

**Why is `page.once('dialog', ...)` used instead of `page.on('dialog', ...)`?**
`page.on` registers a permanent listener that fires on every dialog for the rest of the page's life. `page.once` fires exactly once and removes itself. Since delete confirmations and Change Type dialogs appear in specific known spots and should only be auto-accepted there, `once` is the right choice. Using `on` would silently accept any unexpected dialog that appeared later.

**The `frameLocator` vs `contentFrame()` distinction:**
`contentFrame()` on a `Locator` gives you the raw `Frame` object. It works but requires the iframe to already be attached. `frameLocator()` on the `Page` gives you a `FrameLocator` — a lazy reference that Playwright auto-retries until the frame is available. For dynamic iframes (like the Change Type dialog), `frameLocator` is more reliable because it handles the timing gap between the iframe appearing in the DOM and its content being ready.

**The `onlyifdoesntexist` installer flag:**
This single flag is critical for upgrades. Without it, every reinstall would overwrite the user's `.env` with the template, erasing their company setting. With it, existing installations preserve their configuration automatically.

**PyInstaller `console=False`:**
The spec file sets `console=False`, which means no terminal window appears when the user launches the app. This is correct for a GUI application. During development, Python output (`print()` statements in the processor) goes to the terminal running `python treqso_gui.py`. After packaging, those same prints go nowhere — the GUI console (which reads from the Node.js subprocess stdout) is the only visible output channel. Add `log_callback` calls if you need processor-level messages to appear in the GUI.
