#!/usr/bin/env node

import {
  formatGapSummaryMarkdown,
  parseCliArgs,
  printResult,
  summarizeTestGaps,
} from "./_shared.mjs";

const options = parseCliArgs(process.argv.slice(2));
const result = await summarizeTestGaps({ scope: options.scope });

if (options.markdown) {
  result.markdown = formatGapSummaryMarkdown(result);
}

printResult(result, { markdown: Boolean(options.markdown) });
