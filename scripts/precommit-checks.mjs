#!/usr/bin/env node

import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const scriptPath = fileURLToPath(import.meta.url);
const repoRoot = path.resolve(path.dirname(scriptPath), "..");

function resolvePythonCommand() {
  const candidates = [
    path.join(repoRoot, ".venv", "Scripts", "python.exe"),
    path.join(repoRoot, ".venv", "Scripts", "python"),
    path.join(repoRoot, ".venv", "bin", "python"),
  ];

  for (const candidate of candidates) {
    if (existsSync(candidate)) {
      return { command: candidate, args: [] };
    }
  }

  return { command: "python", args: [] };
}

function run(command, args) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      cwd: repoRoot,
      stdio: "inherit",
      shell: false,
    });

    child.on("error", reject);
    child.on("exit", (code, signal) => {
      if (signal) {
        reject(new Error(`Command exited via signal ${signal}`));
        return;
      }

      resolve(code ?? 1);
    });
  });
}

function runCaptured(command, args) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      cwd: repoRoot,
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
        stdout: stdout.trim(),
        stderr: stderr.trim(),
      });
    });
  });
}

async function ensureDockerReady() {
  const result = await runCaptured("docker", ["info"]);

  if (result.code === 0) {
    return;
  }

  const detail = result.stderr || result.stdout || "Docker is unavailable.";
  console.error("Pre-commit checks require Docker because the full pytest suite starts PostgreSQL via docker compose.");
  console.error("Start Docker Desktop or another compatible Docker daemon, then retry the commit.");
  console.error(detail);
  process.exit(1);
}

async function main() {
  const python = resolvePythonCommand();
  const command = python.command;
  const args = [...python.args, "-m", "pytest"];

  await ensureDockerReady();
  console.log("Running full pytest suite before commit...");

  try {
    const exitCode = await run(command, args);

    if (exitCode !== 0) {
      process.exit(exitCode);
    }

    console.log("Pre-commit checks passed.");
  } catch (error) {
    console.error("Pre-commit checks could not start.");
    console.error(
      "Expected a working Python environment with pytest, preferably under .venv/.",
    );
    console.error(error instanceof Error ? error.message : String(error));
    process.exit(1);
  }
}

await main();
