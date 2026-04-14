#!/usr/bin/env node

import {
  classifyTestLevel,
  formatTestLevelMarkdown,
  parseCliArgs,
  printResult,
} from "./_shared.mjs";

const options = parseCliArgs(process.argv.slice(2));
const result = await classifyTestLevel({ source: options.source });

if (options.markdown) {
  result.markdown = formatTestLevelMarkdown(result);
}

printResult(result, { markdown: Boolean(options.markdown) });
