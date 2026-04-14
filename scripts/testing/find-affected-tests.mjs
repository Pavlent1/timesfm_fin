#!/usr/bin/env node

import {
  findAffectedTests,
  formatAffectedTestsMarkdown,
  parseCliArgs,
  printResult,
} from "./_shared.mjs";

const options = parseCliArgs(process.argv.slice(2));
const result = await findAffectedTests({ scope: options.scope });

if (options.markdown) {
  result.markdown = formatAffectedTestsMarkdown(result);
}

printResult(result, { markdown: Boolean(options.markdown) });
