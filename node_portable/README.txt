TREQSO Automation Tool — Portable Node.js
==========================================

This directory must contain node.exe before running build_release.bat.

How to get it
-------------
1. Go to: https://nodejs.org/en/download
2. Under "Prebuilt Binaries", select:
     Platform : Windows
     Version  : LTS (current Long Term Support)
     OS       : x64
     Package  : Binary (.zip)
3. Download and extract the .zip file.
4. Copy  node.exe  from the root of the extracted folder into this directory.

Result: node_portable\node.exe  (~30 MB)

Why only node.exe?
------------------
Only the node.exe binary is needed. npm, npx, and the bundled npm modules
that ship with Node.js are used on the developer's machine (via the normal
npm install step in build_release.bat) but are NOT required at runtime.

The Playwright browser (.cmd shim in node_modules/.bin/) calls node via
the PATH, which build_release.bat and the GUI's browser-installer both
patch to include this directory automatically.

This file (README.txt) is not included in the installer — only node.exe is.
