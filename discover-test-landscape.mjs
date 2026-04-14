#!/usr/bin/env node

import { collectLandscape, formatLandscapeMarkdown, parseCliArgs, printResult } from "./_shared.mjs";

const options = parseCliArgs(process.argv.slice(2));
const result = collectLandscape({ scope: options.scope });

if (options.markdown) {
  result.markdown = formatLandscapeMarkdown(result);
}

printResult(result, { markdown: Boolean(options.markdown) });
