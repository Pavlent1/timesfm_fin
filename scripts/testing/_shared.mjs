import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const scriptPath = fileURLToPath(import.meta.url);
const scriptsDir = path.dirname(scriptPath);
export const repoRoot = path.resolve(scriptsDir, "..", "..");
const approvedRoots = ["src", "configs", "scripts"];

export function parseCliArgs(argv) {
  const options = {
    markdown: false,
    scope: null,
    source: null,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];

    if (arg === "--markdown") {
      options.markdown = true;
      continue;
    }

    if (arg === "--scope") {
      options.scope = argv[index + 1] ?? null;
      index += 1;
      continue;
    }

    if (arg === "--source") {
      options.source = argv[index + 1] ?? null;
      index += 1;
    }
  }

  return options;
}

export function printResult(result, { markdown = false } = {}) {
  if (markdown) {
    process.stdout.write(`${result.markdown ?? ""}\n`);
    return;
  }

  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
}

function normalizePath(value) {
  return value.split(path.sep).join("/");
}

export function relativeRepoPath(targetPath) {
  return normalizePath(path.relative(repoRoot, targetPath));
}

function listFilesRecursive(rootDir, extensions) {
  if (!fs.existsSync(rootDir)) {
    return [];
  }

  const entries = fs.readdirSync(rootDir, { withFileTypes: true });
  const files = [];

  for (const entry of entries) {
    if (entry.name === "__pycache__" || entry.name === ".pytest_cache") {
      continue;
    }

    const entryPath = path.join(rootDir, entry.name);
    if (entry.isDirectory()) {
      files.push(...listFilesRecursive(entryPath, extensions));
      continue;
    }

    if (extensions.some((extension) => entry.name.endsWith(extension))) {
      files.push(entryPath);
    }
  }

  return files.sort();
}

export function resolvePythonCommand() {
  const candidates = [
    path.join(repoRoot, ".venv", "Scripts", "python.exe"),
    path.join(repoRoot, ".venv", "Scripts", "python"),
    path.join(repoRoot, ".venv", "bin", "python"),
  ];

  for (const candidate of candidates) {
    if (fs.existsSync(candidate)) {
      return { command: candidate, args: [] };
    }
  }

  return { command: "python", args: [] };
}

export async function runCaptured(command, args, options = {}) {
  return await new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      cwd: options.cwd ?? repoRoot,
      stdio: ["ignore", "pipe", "pipe"],
      shell: false,
    });

    let stdout = "";
    let stderr = "";

    child.stdout.on("data", (chunk) => {
      stdout += chunk;
    });

    child.stderr.on("data", (chunk) => {
      stderr += chunk;
    });

    child.on("error", reject);
    child.on("exit", (code, signal) => {
      if (signal) {
        reject(new Error(`Command exited via signal ${signal}`));
        return;
      }

      resolve({
        code: code ?? 1,
        stdout,
        stderr,
      });
    });
  });
}

function parseCollectedCount(output) {
  const match = output.match(/(\d+)\s+tests?\s+collected/i);
  return match ? Number(match[1]) : null;
}

function readPytestMarkers() {
  const pytestIniPath = path.join(repoRoot, "pytest.ini");

  if (!fs.existsSync(pytestIniPath)) {
    return [];
  }

  const lines = fs.readFileSync(pytestIniPath, "utf-8").split(/\r?\n/);
  const markers = [];
  let inMarkers = false;

  for (const line of lines) {
    if (line.trim() === "markers =") {
      inMarkers = true;
      continue;
    }

    if (inMarkers) {
      if (!line.startsWith("    ")) {
        break;
      }

      const markerName = line.trim().split(":")[0];
      if (markerName) {
        markers.push(markerName);
      }
    }
  }

  return markers;
}

function classifyTestFile(testPath, text) {
  const repoPath = relativeRepoPath(testPath);
  const dockerFixtures = [
    "repo_postgres_service",
    "postgres_test_database",
    "bootstrapped_postgres_connection",
    "dataset_factory",
  ];

  if (dockerFixtures.some((fixtureName) => text.includes(fixtureName))) {
    return {
      layer: "integration",
      docker: true,
    };
  }

  if (repoPath.endsWith("tests/test_docs_contract.py")) {
    return {
      layer: "contract",
      docker: false,
    };
  }

  return {
    layer: "unit",
    docker: false,
  };
}

function detectRunnerLayers(testFiles) {
  const layers = new Set(testFiles.map((entry) => entry.layer));
  return {
    unit: layers.has("unit") ? ["pytest"] : [],
    integration: layers.has("integration") ? ["pytest"] : [],
    e2e: [],
  };
}

export async function collectLandscape({ scope = null } = {}) {
  const testingDir = path.join(repoRoot, "scripts", "testing");
  const testFiles = listFilesRecursive(path.join(repoRoot, "tests"), [".py"])
    .filter((testPath) => path.basename(testPath).startsWith("test_"))
    .map((testPath) => {
      const text = fs.readFileSync(testPath, "utf-8");
      const classification = classifyTestFile(testPath, text);
      return {
        path: relativeRepoPath(testPath),
        ...classification,
      };
    });

  const helperScripts = listFilesRecursive(testingDir, [".mjs"]).map(relativeRepoPath);
  const python = resolvePythonCommand();
  const collectResult = await runCaptured(python.command, [
    ...python.args,
    "-m",
    "pytest",
    "--collect-only",
    "-q",
  ]);
  const collectedCount = parseCollectedCount(
    `${collectResult.stdout}\n${collectResult.stderr}`,
  );

  return {
    generated_at: new Date().toISOString(),
    scope: scope ?? "whole approved codebase (`src/`, `configs/`, `scripts/`) plus `tests/`",
    runners: detectRunnerLayers(testFiles),
    helperScripts,
    pytest: {
      config: fs.existsSync(path.join(repoRoot, "pytest.ini")) ? "pytest.ini" : "none",
      markers: readPytestMarkers(),
      collect_command: `${relativeRepoPath(python.command)} -m pytest --collect-only -q`,
      collect_status: collectResult.code === 0 ? "passed" : "failed",
      collected_tests: collectedCount,
      collect_stderr: collectResult.stderr,
    },
    testFiles,
  };
}

export function formatLandscapeMarkdown(result) {
  const lines = [
    "# Test Landscape",
    "",
    `- Scope: ${result.scope}`,
    `- Generated: ${result.generated_at}`,
    "",
    "## Runners",
    "",
    `- Unit: ${result.runners.unit.join(", ") || "none"}`,
    `- Integration: ${result.runners.integration.join(", ") || "none"}`,
    `- E2E: ${result.runners.e2e.join(", ") || "none"}`,
    "",
    "## Pytest",
    "",
    `- Config: \`${result.pytest.config}\``,
    `- Registered markers: ${result.pytest.markers.length ? result.pytest.markers.map((marker) => `\`${marker}\``).join(", ") : "none"}`,
    `- Collect status: \`${result.pytest.collect_status}\``,
    `- Collected tests: ${result.pytest.collected_tests ?? "unknown"}`,
    "",
    "## Helper Scripts",
    "",
    ...result.helperScripts.map((script) => `- \`${script}\``),
    "",
    "## Test Files",
    "",
    "| Path | Layer | Docker |",
    "| --- | --- | --- |",
    ...result.testFiles.map(
      (entry) => `| \`${entry.path}\` | ${entry.layer} | ${entry.docker ? "yes" : "no"} |`,
    ),
  ];

  if (result.pytest.collect_stderr) {
    lines.push(
      "",
      "## Collect Notes",
      "",
      "```text",
      result.pytest.collect_stderr,
      "```",
    );
  }

  return lines.join("\n");
}

export async function measureCoverage({ scope = null } = {}) {
  const python = resolvePythonCommand();
  const probe = await runCaptured(python.command, [
    ...python.args,
    "-c",
    "import importlib.util, sys; sys.stdout.write('yes' if importlib.util.find_spec('pytest_cov') else 'no')",
  ]);
  const available = probe.code === 0 && probe.stdout.trim() === "yes";

  return {
    generated_at: new Date().toISOString(),
    scope: scope ?? "whole approved codebase (`src/`, `configs/`, `scripts/`) plus `tests/`",
    status: available ? "available" : "unavailable",
    command: available
      ? `${relativeRepoPath(python.command)} -m pytest --cov`
      : null,
    reason: available
      ? null
      : "pytest-cov is not installed in the repo-managed Python environment, so no repo-owned coverage command is currently runnable.",
  };
}

export function formatCoverageMarkdown(result) {
  const lines = [
    "# Coverage Status",
    "",
    `- Scope: ${result.scope}`,
    `- Generated: ${result.generated_at}`,
    `- Coverage status: \`${result.status}\``,
  ];

  if (result.command) {
    lines.push(`- Coverage command: \`${result.command}\``);
  }

  if (result.reason) {
    lines.push(`- Reason: ${result.reason}`);
  }

  return lines.join("\n");
}

function findReferencedSourceFiles(testFiles) {
  const sourceFiles = [];

  for (const root of approvedRoots) {
    const rootDir = path.join(repoRoot, root);
    const extensions = root === "scripts" ? [".mjs", ".ps1"] : [".py"];

    for (const sourcePath of listFilesRecursive(rootDir, extensions)) {
      if (relativeRepoPath(sourcePath).startsWith("scripts/testing/")) {
        continue;
      }

      sourceFiles.push(relativeRepoPath(sourcePath));
    }
  }

  const covered = [];
  const uncovered = [];
  const runtimeTestTexts = testFiles
    .filter(
      (testFile) =>
        testFile.layer !== "contract" &&
        !testFile.path.endsWith("tests/test_testing_scripts.py"),
    )
    .map((testFile) => testFile.text);

  for (const sourcePath of sourceFiles) {
    const basename = path.basename(sourcePath);
    const stem = basename.replace(path.extname(basename), "");
    const coveredByTests = runtimeTestTexts.some(
      (text) =>
        text.includes(stem) ||
        text.includes(basename) ||
        text.includes(`src/${basename}`) ||
        text.includes(`scripts/${basename}`),
    );

    if (coveredByTests) {
      covered.push(sourcePath);
    } else {
      uncovered.push(sourcePath);
    }
  }

  return { covered, uncovered };
}

export async function summarizeTestGaps({ scope = null } = {}) {
  const landscape = await collectLandscape({ scope });
  const testFiles = listFilesRecursive(path.join(repoRoot, "tests"), [".py"])
    .filter((testPath) => path.basename(testPath).startsWith("test_"))
    .map((testPath) => ({
      path: relativeRepoPath(testPath),
      text: fs.readFileSync(testPath, "utf-8"),
      layer: classifyTestFile(testPath, fs.readFileSync(testPath, "utf-8")).layer,
    }));
  const coverage = await measureCoverage({ scope });
  const mapped = findReferencedSourceFiles(testFiles);
  const dockerHeavy =
    landscape.testFiles.length > 0 &&
    landscape.testFiles.filter((entry) => entry.docker).length / landscape.testFiles.length >= 0.5;

  return {
    generated_at: new Date().toISOString(),
    scope: scope ?? "whole approved codebase (`src/`, `configs/`, `scripts/`) plus `tests/`",
    blockers: [
      ...(dockerHeavy
        ? ["Most collected tests still depend on Docker-backed PostgreSQL fixtures."]
        : []),
      ...(coverage.status === "unavailable" ? [coverage.reason] : []),
    ],
    covered: mapped.covered,
    uncovered: mapped.uncovered,
  };
}

export function formatGapSummaryMarkdown(result) {
  const lines = [
    "# Test Gap Summary",
    "",
    `- Scope: ${result.scope}`,
    `- Generated: ${result.generated_at}`,
    "",
    "## Active Blockers",
    "",
    ...(result.blockers.length
      ? result.blockers.map((blocker) => `- ${blocker}`)
      : ["- None detected"]),
    "",
    "## Missing Direct Coverage",
    "",
    ...result.uncovered.slice(0, 20).map((sourcePath) => `- \`${sourcePath}\``),
  ];

  if (!result.uncovered.length) {
    lines.push("- None detected");
  }

  return lines.join("\n");
}

export async function findAffectedTests() {
  const gitStatus = await runCaptured("git", ["status", "--porcelain"]);
  const changedPaths = gitStatus.stdout
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => {
      const match = line.match(/^.. (.+)$/);
      return (match ? match[1] : line.trim()).replace(/\\/g, "/");
    });

  const testFiles = listFilesRecursive(path.join(repoRoot, "tests"), [".py"]).map((testPath) => ({
    path: relativeRepoPath(testPath),
    text: fs.readFileSync(testPath, "utf-8"),
  }));

  const affected = changedPaths.map((changedPath) => {
    const stem = path.basename(changedPath, path.extname(changedPath));
    const relatedTests = testFiles
      .filter(
        (testFile) =>
          testFile.path === changedPath ||
          testFile.path.includes(stem) ||
          testFile.text.includes(stem) ||
          testFile.text.includes(changedPath),
      )
      .map((testFile) => testFile.path);

    return {
      path: changedPath,
      relatedTests,
    };
  });

  return {
    generated_at: new Date().toISOString(),
    changedPaths,
    affected,
  };
}

export function formatAffectedTestsMarkdown(result) {
  if (!result.changedPaths.length) {
    return "# Affected Tests\n\n- No changed files detected.";
  }

  const lines = ["# Affected Tests", "", "## Changed Files", ""];

  for (const entry of result.affected) {
    lines.push(`- \`${entry.path}\``);
    if (!entry.relatedTests.length) {
      lines.push("  - No matching tests found");
      continue;
    }

    for (const testPath of entry.relatedTests) {
      lines.push(`  - \`${testPath}\``);
    }
  }

  return lines.join("\n");
}

export async function classifyTestLevel({ source }) {
  if (!source) {
    throw new Error("--source is required");
  }

  const sourcePath = path.resolve(repoRoot, source);
  const repoPath = relativeRepoPath(sourcePath);
  const text = fs.existsSync(sourcePath) ? fs.readFileSync(sourcePath, "utf-8") : "";

  let recommended = "unit";
  const reasons = [];

  if (repoPath.startsWith("scripts/testing/")) {
    recommended = "unit";
    reasons.push("The helper is deterministic repo-inspection tooling with no required service dependency.");
  } else if (text.includes("argparse") || text.includes("subprocess") || repoPath.endsWith(".ps1")) {
    recommended = "contract";
    reasons.push("The surface is primarily CLI or command-boundary behavior, so contract tests are the first fit.");
  } else if (
    text.includes("psycopg") ||
    text.includes("docker") ||
    text.includes("sqlite3") ||
    text.includes("urllib.request")
  ) {
    recommended = "integration";
    reasons.push("The file crosses storage, service, or network boundaries that usually need integration-style coverage.");
  } else {
    reasons.push("The file looks isolated enough for deterministic unit coverage.");
  }

  return {
    generated_at: new Date().toISOString(),
    source: repoPath,
    recommended,
    reasons,
  };
}

export function formatTestLevelMarkdown(result) {
  return [
    "# Test Level Classification",
    "",
    `- Source: \`${result.source}\``,
    `- Recommended level: \`${result.recommended}\``,
    "",
    "## Rationale",
    "",
    ...result.reasons.map((reason) => `- ${reason}`),
  ].join("\n");
}
