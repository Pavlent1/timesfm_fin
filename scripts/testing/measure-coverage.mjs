#!/usr/bin/env node

import {
  formatCoverageMarkdown,
  measureCoverage,
  parseCliArgs,
  printResult,
} from "./_shared.mjs";

const options = parseCliArgs(process.argv.slice(2));
const result = await measureCoverage({ scope: options.scope });

if (options.markdown) {
  result.markdown = formatCoverageMarkdown(result);
}

printResult(result, { markdown: Boolean(options.markdown) });
