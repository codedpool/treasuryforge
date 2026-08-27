#!/usr/bin/env node
// TrueForge v0.1.4's standalone (SQLite) mode crashes on native Windows during
// startup: Kysely's FileMigrationProvider dynamic-imports each migration file
// using a raw filesystem path (e.g. "C:\\...\\migrations\\0001.js"). Node's
// ESM loader requires a proper URL for dynamic import(), and a Windows drive
// letter parses as an (invalid) URL scheme -- so it throws
// ERR_UNSUPPORTED_ESM_URL_SCHEME before the server ever binds a port. This
// does not happen on macOS/Linux, where absolute paths are valid import()
// specifiers. Not needed for the Linux-based prod deploy targets in the plan.
//
// FileMigrationProvider already supports an `import` override for exactly
// this case (see kysely/dist/migration/file-migration-provider.js); TrueForge
// just doesn't pass one. This script patches the installed dist/main.js to
// wrap the migration file path in pathToFileURL() before importing it.
//
// Safe to re-run: no-ops on non-Windows platforms and if already patched.

const fs = require("fs");
const path = require("path");

if (process.platform !== "win32") {
  console.log("[patch-windows-esm-migrations] not on win32, skipping.");
  process.exit(0);
}

const mainPath = path.join(
  __dirname,
  "node_modules",
  "@truefoundry",
  "trueforge",
  "dist",
  "main.js"
);

if (!fs.existsSync(mainPath)) {
  console.error(`[patch-windows-esm-migrations] ${mainPath} not found -- did npm install run?`);
  process.exit(1);
}

let content = fs.readFileSync(mainPath, "utf-8");

const MARKER = "pathToFileURL2";
if (content.includes(MARKER)) {
  console.log("[patch-windows-esm-migrations] already patched.");
  process.exit(0);
}

const oldImport = 'import { promises as fs2 } from "fs";\nimport path4 from "path";';
const newImport =
  'import { promises as fs2 } from "fs";\nimport path4 from "path";\nimport { pathToFileURL as pathToFileURL2 } from "url";';

const oldProvider = `    provider: new FileMigrationProvider({
      fs: fs2,
      path: path4,
      migrationFolder: path4.join(import.meta.dirname, "sqlite", "migrations")
    })`;
const newProvider = `    provider: new FileMigrationProvider({
      fs: fs2,
      path: path4,
      migrationFolder: path4.join(import.meta.dirname, "sqlite", "migrations"),
      import: (p) => import(pathToFileURL2(p).href)
    })`;

if (!content.includes(oldImport) || !content.includes(oldProvider)) {
  console.error(
    "[patch-windows-esm-migrations] expected code not found -- TrueForge's dist/main.js " +
      "layout has likely changed in this version. Patch needs updating; see the comment " +
      "at the top of this file for the underlying issue (Kysely FileMigrationProvider + " +
      "Windows ESM paths)."
  );
  process.exit(1);
}

content = content.replace(oldImport, newImport);
content = content.replace(oldProvider, newProvider);

fs.writeFileSync(mainPath, content, "utf-8");
console.log("[patch-windows-esm-migrations] patched dist/main.js successfully.");
