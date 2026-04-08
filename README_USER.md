# TREQSO Automation Tool — User Guide

This guide covers everything you need to install and use the TREQSO Automation Tool: what it does, how to install it, and how to use each feature.

---

## Table of Contents

1. [What This Tool Does](#what-this-tool-does)
2. [Before You Install](#before-you-install)
3. [Installing the Application](#installing-the-application)
4. [First-Time Setup](#first-time-setup)
5. [The Application Window](#the-application-window)
6. [Tab 1: Print Manufacturing Orders](#tab-1-print-manufacturing-orders)
7. [Tab 2: Create Parts](#tab-2-create-parts)
8. [Tab 3: Edit Parts](#tab-3-edit-parts)
9. [Tab 4: Create BOMs](#tab-4-create-boms)
10. [Tab 5: Mass Replace Part](#tab-5-mass-replace-part)
11. [Tab 6: Settings](#tab-6-settings)
12. [Understanding Results](#understanding-results)
13. [Preparing Your CSV Files](#preparing-your-csv-files)
14. [Troubleshooting](#troubleshooting)

---

## What This Tool Does

The TREQSO Automation Tool is a Windows desktop application that automates repetitive tasks inside TREQSO — things that would otherwise require clicking through many screens one record at a time. Instead, you prepare a spreadsheet, point the tool at it, and it handles the rest.

The tool can:

- **Print Manufacturing Orders** — given a parent MO Reference ID, the tool finds every child MO beneath it and sends them all to a printer of your choosing, one after another, without any further clicking
- **Create Parts** — given a CSV file with part information, the tool creates each part in TREQSO automatically, filling in all required fields
- **Edit Parts** — given a CSV file containing part numbers and the specific fields you want to change, the tool opens each part record and updates only those fields, leaving everything else untouched
- **Create Bills of Materials** — given a CSV file with BOM structure, the tool builds the complete BOM for one or more assemblies in TREQSO
- **Mass Replace a Part** — given an old part number and a new one, the tool finds every assembly that contains the old part and swaps it out across all of them at once

The tool opens a browser window, navigates TREQSO just as you would, and performs the actions on your behalf. You can watch it work, or configure it to run invisibly in the background.

---

## Before You Install

### No additional software required

The TREQSO Automation Tool is fully portable. The installer bundles everything it needs, including its own copy of Node.js. You do not need to install Node.js, Python, or any other runtime separately.

The only requirement is that **your Windows account must be on the Douglas Dynamics domain and have access to TREQSO**. The tool logs in using your Windows credentials automatically — the same ones you use to log into your work computer. If your account does not have TREQSO access, contact IT before proceeding.

### Playwright browser — one-time download on first launch

The tool drives a browser to automate TREQSO. The browser itself (Google Chromium, approximately 150 MB) downloads automatically the first time you open the application. This is a one-time step that requires an internet connection. All subsequent launches will be instant. You will see a message in the Output Console when this is happening.

---

## Installing the Application

The installer is fully self-contained. Nothing needs to be installed beforehand.

### Step 1: Run the installer

Double-click **`TREQSO_Automation_Setup_v1.0.2.exe`**.

Windows may show a security prompt:
> "Do you want to allow this app to make changes to your device?"

Click **Yes** — the installer needs administrator access to write to Program Files.

### Step 2: The setup wizard

You will see a window titled **"TREQSO Automation Tool Setup"**.

---

**Welcome page** — Click **Next**.

---

**Select Destination Location**

The default path is:
```
C:\Program Files\TREQSO Automation Tool
```
Leave this as-is. Click **Next**.

---

**Select Additional Tasks**

You are offered an optional **Desktop shortcut**. Unchecked by default — check it if you want one. Click **Next**.

---

**Ready to Install**

Click **Install**. The installer copies all application files including the bundled Node.js runtime and automation packages. This typically takes 30–60 seconds. Do not close the installer during this time.

---

**Completing Setup**

Two checkboxes appear on the final page:

- **Configure TREQSO connection settings** — opens the `.env` configuration file in Notepad. The TREQSO URL is already set correctly; you only need this if you are changing the Company value. You can always do this later from the Settings tab.
- **Launch TREQSO Automation Tool** — starts the application immediately.

Click **Finish**.

### What was installed

- Application: `C:\Program Files\TREQSO Automation Tool\TREQSO_Automation.exe`
- Start Menu folder: **Start → TREQSO Automation Tool**
- Desktop shortcut (if selected)
- Configuration file: `C:\Program Files\TREQSO Automation Tool\.env`
- Bundled Node.js: `C:\Program Files\TREQSO Automation Tool\node_portable\node.exe`
- Automation engine: `C:\Program Files\TREQSO Automation Tool\dist\`
- Node.js packages: `C:\Program Files\TREQSO Automation Tool\node_modules\`
- Sample CSV files and Excel templates

---

## First-Time Setup

The application comes pre-configured with the correct TREQSO URL for Douglas Dynamics. In most cases the only thing you need to verify before running operations is the **Company** field.

### Checking your settings

Launch the application and click the **Settings** tab (the rightmost tab). You should see:

- **TREQSO URL:** `https://dtetreqso.douglasdynamics.int/Treqso` — this is correct and should not need to be changed.
- **Company:** `CargoTest` — this is the default. If you work under a different company in TREQSO, update this field to match exactly how it appears when you log into TREQSO in a browser (spelling and capitalization must match).

If you make any changes, click **Save Settings** before continuing.

### Testing the connection

Click **Test Connection**. The tool will open a browser, log into TREQSO using your Windows credentials, and confirm it reached the correct company. A popup will say **"Successfully connected to TREQSO!"** on success, and a screenshot named `login_success.png` will be saved to `C:\Program Files\TREQSO Automation Tool\` so you can see exactly what the tool saw.

If the test fails, see [Troubleshooting: Connection Problems](#connection-problems).

---

## The Application Window

The main window has the following areas:

**Tab row** — six tabs across the top of the working area:
- Print Manufacturing Orders
- Create Parts
- Edit Parts
- Create BOMs
- Mass Replace Part
- Settings

**Working area** — the content of the currently selected tab.

**Output Console** — a scrolling text area at the bottom showing real-time messages as each operation runs. Every step the tool takes is written here, including errors. This is your primary source of information about what is happening.

**Status bar** — a single line at the very bottom showing a brief current state (e.g., "Ready", "Creating parts...", "Parts edit completed").

All operations run in the background so the window stays responsive. You can watch the Output Console update in real time.

---

## Tab 1: Print Manufacturing Orders

Use this tab to print every child Manufacturing Order that belongs to a parent MO.

### What it does

You provide a **Parent MO Reference ID**. The tool logs into TREQSO, navigates to MO Maintenance, filters by that Reference ID, collects every MO number it finds (across multiple pages if there are many), then opens each MO one at a time and sends it to print.

### Before you use this tab — printer setup

There is a Windows setting that must be turned off before this tab works correctly.

The setting is called **"Let Windows manage my default printer"**. When on, Windows automatically changes your default printer based on which network you are on — overriding whatever printer the tool tries to select.

**To turn it off:** Click the **⚙ Open Printer Settings** button in this tab. This opens **Printers & Scanners** in Windows Settings. Find the toggle labeled **"Let Windows manage my default printer"** and switch it to **Off**. You only need to do this once.

### Using this tab

**Parent MO Reference ID**
Type the Reference ID of the parent Manufacturing Order as it appears in TREQSO's MO Maintenance screen.

**Select Printer**
Choose the printer from the dropdown. If a printer you expect to see is missing, click **⟳** to refresh the list.

**Print MOs**
Click **Print MOs** when ready. The tool will:

1. Set the selected printer as the Windows default
2. Log into TREQSO
3. Navigate to MO Maintenance and apply the Reference ID filter
4. Collect all MO numbers (flipping through pages if needed)
5. Open each MO and send it to the printer
6. Report how many printed successfully

### Results

- **All succeeded:** "MOs printed successfully! X/X MOs printed."
- **Some failed:** Warning popup lists the specific MO numbers that failed
- **Complete failure:** Error popup with the error message

Failed MOs are also listed in the Output Console. Re-running the operation will retry all MOs under that Reference ID.

---

## Tab 2: Create Parts

Use this tab to create multiple new parts in TREQSO from a single CSV file instead of entering each one manually.

### What it does

The tool reads each row from your CSV and creates that part in TREQSO by navigating to the Add Part screen, filling in all the fields, and saving. Parts are processed one at a time in sequence.

### Using this tab

**Step 1 — Open the template and fill in your data**

Click **Open Parts Template** to open `Parts_Template.xlsx` in Excel. The correct column headers are already in place. Fill in one part per row. Do not rename or reorder the columns.

**Step 2 — Save as CSV**

In Excel: **File → Save As**, change the file type to **CSV (Comma delimited) (*.csv)**, and click **Save**. Excel may warn about CSV compatibility — click **Keep Current Format**. Note where you saved the file.

**Step 3 — Select the CSV and run**

Click **Browse…** to select the CSV file you just saved. Then click **Create Parts**.

**The format preview table**
Below the file selection row there is a table showing the expected column names and example values from the sample file. Use it as a quick reference when filling in your data.

**Open Sample CSV**
Opens `sample_parts.csv` — a completed example with ten rows showing exactly what valid data looks like in each column.

### Results

- **All succeeded:** "Parts created successfully! X/X parts created."
- **Some failed:** Warning popup lists the specific part numbers that failed. Successfully created parts are unaffected.
- **Complete failure:** Error popup with the error message.

Failed parts are listed in the Output Console under "Failed parts:". Fix those rows in your CSV and re-run with a file containing only the failures — parts that already exist in TREQSO will be rejected as duplicates if you re-run the full file.

---

## Tab 3: Edit Parts

Use this tab to update attributes of existing parts in TREQSO from a CSV file. Only the fields you include in your CSV will be changed — everything else on each part record is left exactly as it is.

### What it does

The tool reads each row from your CSV, navigates to that part's record in TREQSO, and updates only the fields you provided. If a column is present in your CSV but a particular row's cell is blank, that field is skipped for that part. This means you can update different fields for different parts in the same run, and you never need to worry about accidentally overwriting fields you did not intend to change.

### Using this tab

**Step 1 — Open the template and fill in your data**

Click **Open Edit Parts Template** to open `Edit_Parts_Template.xlsx` in Excel. The template contains all editable field columns. Delete the columns you do not need, or simply leave their cells blank for rows where you are not changing that field.

**partNumber is the only required column.** All other columns are optional — include only the ones you want to update.

**Step 2 — Fill in your changes**

Each row is one part. In each row, fill in the `partNumber` and then fill in values only for the fields you want to change. Leave all other cells blank.

For example, to update only descriptions for two parts:

| partNumber | partDescription | fullDescription |
|---|---|---|
| ABC-001 | New short description | |
| ABC-002 | | New long description text |

**Step 3 — Save as CSV**

In Excel: **File → Save As → CSV (Comma delimited) (*.csv) → Save**. Click **Keep Current Format** if prompted.

**Step 4 — Select the CSV and run**

Click **Browse…** to select the CSV, then click **Edit Parts**.

**The format preview table**
Shows sample data demonstrating how each field can be updated independently on different rows.

**Open Sample CSV**
Opens `sample_edit_parts.csv` — a completed example showing one field being updated per part row, illustrating how the tool handles partial updates.

### All editable fields

Every part field except part number can be updated. Include any combination of these columns in your CSV:

| Column | What it controls |
|---|---|
| `partNumber` | **Required** — used to locate the part record |
| `partStatus` | The part's status, e.g. `Active`, `Discontinued`, `Hold` |
| `partDescription` | The short description shown on the part list |
| `fullDescription` | The longer description field |
| `partCategory` | e.g. `4041 (PART)` or `4042 (ASSEMBLY)` |
| `productCode` | e.g. `40 (MANUFACTURED)`, `31 (RAW MATERIAL)`, `50 (PARTS)` |
| `salesGroup` | Sales group assignment |
| `partType` | `B (Buy)` or `M (Make)` — see note below |
| `phaseNumber` | e.g. `110 (Parts)` |
| `standardCost` | Numeric cost value |
| `unitOfMeasure` | e.g. `EA (Each)`, `FT (Foot)` |
| `defaultCostField` | `Standard Cost`, `Base Cost`, `Average Cost`, or `Last Purchase Cost` |

Values for dropdown fields (`partStatus`, `partCategory`, `productCode`, `partType`, `phaseNumber`, `unitOfMeasure`, `defaultCostField`) must match exactly what TREQSO displays in its dropdowns — including the code and the text in parentheses.

> **Note on `partType`:** Changing a part type in TREQSO is a significant operation that goes through a dedicated "Change Type" confirmation dialog. The tool handles this automatically — it opens the dialog, sets the new type, and confirms the change. However, because TREQSO requires confirmation, the tool first checks whether the new value actually differs from the current one. If the value in your CSV already matches what is in TREQSO, the change step is skipped entirely. If TREQSO shows a warning dialog during the type change, the tool will accept it automatically.

### Results

- **All succeeded:** "Parts updated successfully! X/X parts updated."
- **Some failed:** Warning popup lists the specific part numbers that failed. Successfully updated parts are unaffected.
- **Complete failure:** Error popup with the error message.

Failed parts are listed in the Output Console under "Failed parts:". If a part number was not found in TREQSO, that row will appear as a failure — double-check the part number spelling. Fix the affected rows and re-run with a CSV containing only those failures.

---

## Tab 4: Create BOMs

Use this tab to create Bills of Materials in TREQSO from a CSV file. A single file can contain BOM data for multiple assemblies at once.

### What it does

Each row in your CSV represents one component line in one assembly. The tool groups rows by assembly, then for each assembly creates the BOM header and adds each component line. Multiple assemblies in one file are handled in sequence.

### Using this tab

**Step 1 — Open the template and fill in your data**

Click **Open BOM Template** to open `BOMs_Template.xlsx` in Excel. Fill in one component line per row. Keep all lines for the same assembly grouped together — do not interleave rows from different assemblies. Do not rename or reorder the columns.

**Step 2 — Save as CSV**

In Excel: **File → Save As → CSV (Comma delimited) (*.csv) → Save**. Click **Keep Current Format** if prompted.

**Step 3 — Select the CSV and run**

Click **Browse…** to select the CSV, then click **Create BOMs**.

**The format preview table**
Shows the expected columns and example values for quick reference.

**Open Sample CSV**
Opens `sample_bom.csv` — a completed example with two assemblies and ten lines total, showing how rows should be structured and grouped.

### Results

- **Success:** Popup confirms the BOMs were created.
- **Failure:** Error popup with the error message; the Output Console shows more detail.

---

## Tab 5: Mass Replace Part

Use this tab to swap one component part for another across every BOM in TREQSO that contains it. The tool finds all affected assemblies automatically — you do not need to know which ones they are.

### What it does

You provide the old part number and the new part number. The tool searches TREQSO for every assembly containing the old part, then for each one: opens the BOM, removes the old part line, and adds a new line with the new part number. If you provide a new quantity, it is applied to every affected BOM. If you leave the quantity blank, each BOM line keeps its existing quantity.

### Using this tab

**Old Part Number**
The exact part number to replace, as it appears in TREQSO.

**New Part Number**
The part number that should replace it.

**New Quantity (optional)**
Leave blank to preserve each BOM line's existing quantity. Enter a number to set the same quantity in every affected BOM.

**Replace Part**
Click when the fields are filled in. Watch the Output Console — each assembly is logged as it is processed.

### Results

- **Success:** Popup confirms the replacement was completed.
- **Failure:** Error popup with the error message.

If some assemblies fail, the Output Console and error popup list which ones. Those can be fixed manually in TREQSO or re-run once the cause is resolved.

---

## Tab 6: Settings

Use this tab to configure how the tool connects to TREQSO and how the browser behaves.

### Fields

**TREQSO URL**
Pre-configured as `https://dtetreqso.douglasdynamics.int/Treqso`. This is the correct address for Douglas Dynamics and does not need to be changed.

**Company**
The company name as it appears in TREQSO after login. The default is `CargoTest`. If you work under a different company, update this to match exactly — spelling and capitalization must be identical to what TREQSO displays. The tool uses this to confirm it is in the right company after login, and will switch automatically if there is a mismatch.

**Headless Mode**
When **unchecked**, the browser is visible while the tool runs. When **checked**, the browser runs invisibly in the background. The tool works the same either way.

Leave unchecked while getting started so you can see what is happening. Once you are confident everything is working, check this box so the browser does not appear on screen during operations.

**Slow Motion (ms)**
Leave at `0` for normal operation. Increasing this value (e.g., `500`) adds a delay between every browser action, which can help when TREQSO is slow to respond. Reset to `0` when done troubleshooting.

### Buttons

**Save Settings**
Saves the current field values to the configuration file at `C:\Program Files\TREQSO Automation Tool\.env`. Settings are not saved automatically — you must click this after making any changes. A popup will confirm "Settings saved to .env file."

**Test Connection**
Opens a browser, logs into TREQSO using your Windows credentials, and confirms the correct company is shown. A success popup appears if everything is working. A screenshot named `login_success.png` is also saved to `C:\Program Files\TREQSO Automation Tool\` so you can verify what the tool saw.

**Open User Guide**
Opens this guide in your default text editor or Markdown viewer.

> **Note:** Settings are loaded from the `.env` file on startup. Always click **Save Settings** after making changes, otherwise they will be lost when the application is closed and reopened.

---

## Understanding Results

### Popups

Every operation ends with a popup:

- **Success (blue "i" icon):** Everything worked. Shows how many items were processed.
- **Warning (yellow "!" icon):** Partial failure — some items worked, some did not. Lists the specific part numbers, MO IDs, or assembly names that failed. Successfully processed items are complete and do not need to be re-run.
- **Error (red "X" icon):** The operation failed before processing any items. Shows the error message.

### Output Console

The console is cleared at the start of each operation and shows live progress as the tool works — each part number, MO, or assembly is logged as it is processed, with a `✓` for success or `✗` for failure. A **=== Results ===** summary appears at the end. If an operation fails, the console typically shows more detail than the popup.

### Error screenshots

When the tool fails on a specific item, it takes a screenshot of the browser at the moment of failure and saves it to `C:\Program Files\TREQSO Automation Tool\`. Files are named after the operation and the specific item, for example:

```
error_create_part_ABC-001.png
error_edit_part_ABC-002.png
error_replace_bom_XYZ-100.png
```

Open these to see exactly what was on screen when the failure occurred — whether a dialog appeared unexpectedly, a field was not filled correctly, or a page did not load.

---

## Preparing Your CSV Files

Create Parts, Edit Parts, and Create BOMs all read data from CSV files you prepare in Excel.

### General CSV rules

- The first row must contain the exact column headers shown in the format tables below
- Column names are case-sensitive — `partNumber` is not the same as `PartNumber`
- Save the file as **CSV (Comma delimited)** from Excel — not as `.xlsx`
- Always save as **CSV (Comma delimited)** from Excel, not as `.xlsb`, `.xls`, or `.xlsx`

### Using the built-in templates

Each tab has a button to open the corresponding Excel template directly from the application. The templates have the correct column headers already in place.

**General workflow:**
1. Click the template button (e.g., **Open Parts Template**)
2. Fill in your data
3. In Excel: **File → Save As → CSV (Comma delimited) (*.csv) → Save**
4. Click **Browse…** in the tab and select the CSV you just saved
5. Click the action button

The sample CSV files installed with the application are also useful references — they show exactly what completed data looks like.

---

### Parts CSV format

All columns are required and must be present in every row. Use the exact values shown in TREQSO's dropdowns for the coded fields.

| Column | Required? | What to enter |
|---|---|---|
| `partNumber` | Yes | The unique part number exactly as it should appear in TREQSO |
| `partDescription` | Yes | A short description of the part |
| `fullDescription` | No | A longer description; leave blank if not needed |
| `partCategory` | Yes | e.g. `4041 (PART)` or `4042 (ASSEMBLY)` |
| `productCode` | Yes | e.g. `40 (MANUFACTURED)`, `31 (RAW MATERIAL)`, or `50 (PARTS)` |
| `salesGroup` | No | Leave blank if not used |
| `partType` | Yes | `B (Buy)` for purchased parts or `M (Make)` for manufactured parts |
| `phaseNumber` | No | Leave blank to use the TREQSO default (`110 (Parts)`) |
| `orderType` | No | Leave blank if not used |
| `standardCost` | No | Numeric value; leave blank if not entering a cost |
| `unitOfMeasure` | Yes | e.g. `EA (Each)` or `FT (Foot)` |
| `defaultCostField` | Yes | `Standard Cost`, `Base Cost`, `Average Cost`, or `Last Purchase Cost` |

Open **Start → TREQSO Automation Tool → Sample Files → Sample Parts** for a complete working example with ten rows.

---

### Edit Parts CSV format

`partNumber` is the only required column. Include only the additional columns you need — any combination is valid. Columns you omit are not touched in TREQSO. Cells within an included column can also be left blank to skip that field for that specific part.

| Column | Notes |
|---|---|
| `partNumber` | **Required.** Must match the part number exactly as it exists in TREQSO. |
| `partStatus` | Include to update the part's status (e.g. `Active`, `Discontinued`, `Hold`) |
| `partDescription` | Include to update the short description |
| `fullDescription` | Include to update the long description |
| `partCategory` | Must match a valid TREQSO category code |
| `productCode` | Must match a valid TREQSO product code |
| `salesGroup` | Include to update the sales group |
| `partType` | `B (Buy)` or `M (Make)` — goes through a Change Type confirmation dialog; see below |
| `phaseNumber` | Must match a valid TREQSO phase number |
| `standardCost` | Numeric value |
| `unitOfMeasure` | Must match a valid TREQSO unit of measure code |
| `defaultCostField` | `Standard Cost`, `Base Cost`, `Average Cost`, or `Last Purchase Cost` |

> **`partType` behaviour:** Because TREQSO treats a part type change as a significant operation, the tool handles it differently from other fields. It compares the value in your CSV against the current type in TREQSO — if they already match, the step is skipped. If they differ, the tool opens TREQSO's "Change Type" dialog, sets the new type, and confirms the change automatically.

**Example — updating status and descriptions:**
```
partNumber,partStatus,partDescription,fullDescription
ABC-001,Discontinued,Revised Short Description,
ABC-002,Hold,,Updated long description text here
ABC-003,Active,New Short Desc,New long description
```

The output console will confirm which fields are being updated at the start of each run.

---

### BOM CSV format

| Column | Required? | What to enter |
|---|---|---|
| `assembly_part_number` | Yes | The part number of the assembly this line belongs to |
| `BOMSequence` | Yes | The sequence number for this line (1, 2, 3...) |
| `BOMOption` | Yes | `0` for the standard BOM option; any other number for an alternate option |
| `partNumber` | Yes | The component part number for this line |
| `quantity` | Yes | How many of this component are needed |
| `doRollup` | Yes | Whether to roll up cost: `TRUE` or `FALSE` |

**Important:** A single CSV can contain lines for multiple assemblies. Keep all lines for the same assembly grouped together — list all of Assembly A's lines first, then all of Assembly B's lines. The first row for each assembly creates the BOM header; subsequent rows for that assembly are added as component lines beneath it.

`BOMOption` `0` is the standard BOM option. Any other value creates an alternate option. Both can coexist within the same assembly.

Open **Start → TREQSO Automation Tool → Sample Files → Sample BOM** for a complete working example with two assemblies.

---

## Troubleshooting

### Installation Issues

**"You do not have permission to install to this directory"**

Right-click the installer and choose **Run as administrator**.

**The Chromium browser download fails on first launch**

The application downloads the Playwright Chromium browser (~150 MB) on its first launch. If the download fails, you will see an error in the Output Console. Close and reopen the application to retry — the check runs automatically each time the app starts until the download succeeds. Ensure you are connected to the internet and that network security software is not blocking downloads from Microsoft's CDN.

---

### Connection Problems

**Test Connection fails — "Connection failed" error**

The most common causes:

1. **Wrong Company name** — open TREQSO in a browser, log in, and check exactly how the company name is displayed. Copy it character-for-character into the Company field in Settings. It is case-sensitive.
2. **Not connected to the VPN** — if working remotely, connect to the Douglas Dynamics VPN and try again.
3. **TREQSO URL was changed** — the correct URL is `https://dtetreqso.douglasdynamics.int/Treqso`. Check the Settings tab to confirm it matches this exactly.
4. **Browser stalls at the login page** — set **Slow Motion** to `500` in the Settings tab, click **Save Settings**, and run Test Connection again. This gives TREQSO more time to load between each step.

**Tool keeps switching companies after login**

The `Company` value in Settings does not match what TREQSO displays after login. Correct the Company field, click **Save Settings**, and test again.

---

### Printing Problems

**No printers appear in the dropdown**

Click **⟳** to refresh the list. If still empty, check that at least one printer is installed in **Windows Settings → Printers & Scanners**.

**The wrong printer is used even though the right one was selected**

The **"Let Windows manage my default printer"** setting is still on. Click **⚙ Open Printer Settings** in the Print Manufacturing Orders tab and turn that toggle off.

**Some MOs failed to print**

The warning popup and Output Console list the specific MO IDs that failed. Error screenshots are saved in `C:\Program Files\TREQSO Automation Tool\`. Re-running the operation will retry all MOs under the Reference ID, including the ones that previously failed.

---

### Create Parts Problems

**Some parts failed to create**

The warning popup and Output Console list the failed part numbers. Error screenshots named `error_create_part_<partnumber>.png` are saved in the install folder.

Fix the affected rows in your CSV and re-run using a file containing only the failed rows. Re-running the full original file will cause already-created parts to be rejected as duplicates.

**"Please select a CSV file first"**

Click **Browse…** and select a file before clicking Create Parts.

**"File not found"**

The file was moved, renamed, or deleted after it was selected. Click **Browse…** to select it again at its current location.

---

### Edit Parts Problems

**A part number shows as failed**

The most common cause is the part number in your CSV not matching exactly what is in TREQSO — check for extra spaces, capitalization differences, or typos. The tool searches TREQSO's part list by the exact string you provide.

An error screenshot named `error_edit_part_<partnumber>.png` is saved in the install folder. Open it to see what was on screen when the failure occurred.

**A field I updated does not appear to have changed**

The value you entered may not match what TREQSO expects for that dropdown field. TREQSO requires the exact code-and-label format (e.g., `EA (Each)`, not just `EA`). Open TREQSO in a browser, navigate to the Add Part screen, and check exactly how the dropdown option is displayed.

**"CSV must contain a 'partNumber' column"**

Your CSV is missing the `partNumber` header. Check that the column is named exactly `partNumber` (case-sensitive) and is present in the first row of the file.

**"Please select a CSV file first"**

Click **Browse…** and select a file before clicking Edit Parts.

---

### Create BOMs Problems

**BOM creation failed**

Check the popup and Output Console for the error message. An error screenshot will be saved in the install folder. Common causes: the assembly part number does not exist in TREQSO yet (create it first using Create Parts), or a component part number does not exist in TREQSO.

---

### Mass Replace Part Problems

**Replace Part succeeded but the change is not visible in TREQSO**

Wait a moment and refresh the BOM screen — TREQSO can take a few seconds to reflect changes. If the change still does not appear, check the error screenshots in the install folder.

**Some assemblies failed**

The Output Console and error popup list which assemblies failed. Error screenshots are saved for each failure. Those assemblies can be updated manually in TREQSO, or re-run once the cause is identified.

---

### General Problems

**The application does not open**

Try launching from the Start Menu rather than a shortcut. If that also fails, open Command Prompt and run:
```
"C:\Program Files\TREQSO Automation Tool\TREQSO_Automation.exe"
```
This may reveal an error message that the shortcut would otherwise hide.

**Operations run slowly**

Check that **Slow Motion** in Settings is set to `0`. If it was increased for troubleshooting and not reset, every browser action will include that delay.

**"No result file generated" in the Output Console**

The automation engine started but exited unexpectedly without reporting a result. Open Command Prompt and run the automation CLI directly to see the raw error:
```
cd "C:\Program Files\TREQSO Automation Tool"
node_portable\node.exe dist\cli.js
```
Pass the error message you see to whoever supports this tool.

**The browser window opens and immediately disappears**

Check the Output Console for error messages. Try enabling **Headless Mode** temporarily in Settings — if the operation then succeeds, the issue is specific to the visible browser window and may indicate a display driver or permission conflict.

---

## Getting Help

1. Check the **Output Console** for the specific error message — it typically has more detail than the popup
2. Open any **error screenshots** in `C:\Program Files\TREQSO Automation Tool\` — they show exactly what the browser saw when the failure occurred
3. Set **Slow Motion to 500** and uncheck **Headless Mode** in Settings, then re-run while watching the browser — you can often see the problem directly
4. Contact IT with the error message from the console and any error screenshots from the install folder
