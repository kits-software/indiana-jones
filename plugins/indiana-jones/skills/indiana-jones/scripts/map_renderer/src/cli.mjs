#!/usr/bin/env node
import {loadRenderJob} from './job.mjs';
import {
  importScreenshot,
  probeWebGl,
  renderJob,
  renderSummary,
} from './render.mjs';

function usage() {
  return `Indiana Jones MapLibre renderer

Usage:
  node src/cli.mjs validate --job <job.json>
  node src/cli.mjs probe [--browser <executable>]
  node src/cli.mjs render --job <job.json> --output <image.png> [--browser <executable>]
  node src/cli.mjs import-screenshot --job <job.json> --input <image.png> --output <image.png> --source-id <id> --kind <kind> --license <text> --access-basis <text> --accessed-at <ISO-8601> [--reason <text>]
`;
}

function parseArguments(values) {
  const [command, ...tokens] = values;
  const options = {};
  for (let index = 0; index < tokens.length; index += 1) {
    const token = tokens[index];
    if (!token.startsWith('--')) {
      throw new Error(`unexpected argument: ${token}`);
    }
    const name = token.slice(2);
    const value = tokens[index + 1];
    if (!value || value.startsWith('--')) {
      throw new Error(`missing value for --${name}`);
    }
    options[name] = value;
    index += 1;
  }
  return {command, options};
}

function required(options, name) {
  if (!options[name]) {
    throw new Error(`--${name} is required`);
  }
  return options[name];
}

async function main() {
  const {command, options} = parseArguments(process.argv.slice(2));
  if (!command || command === 'help' || command === '--help') {
    process.stdout.write(usage());
    return;
  }
  if (command === 'validate') {
    const loaded = await loadRenderJob(required(options, 'job'));
    process.stdout.write(
      `${JSON.stringify(
        {
          ok: true,
          job: loaded.jobPath,
          mode: loaded.job.mode,
          sources: loaded.job.sources.length,
          customLayerModules: loaded.job.customLayerModules.length,
          fallbackConfigured: Boolean(loaded.job.fallbackScreenshot),
        },
        null,
        2,
      )}\n`,
    );
    return;
  }
  if (command === 'probe') {
    process.stdout.write(
      `${JSON.stringify(
        await probeWebGl({browserPath: options.browser}),
        null,
        2,
      )}\n`,
    );
    return;
  }
  if (command === 'render') {
    const manifest = await renderJob({
      jobPath: required(options, 'job'),
      outputPath: required(options, 'output'),
      browserPath: options.browser,
    });
    process.stdout.write(`${JSON.stringify(renderSummary(manifest), null, 2)}\n`);
    return;
  }
  if (command === 'import-screenshot') {
    const manifest = await importScreenshot({
      jobPath: required(options, 'job'),
      inputPath: required(options, 'input'),
      outputPath: required(options, 'output'),
      sourceId: required(options, 'source-id'),
      kind: required(options, 'kind'),
      license: required(options, 'license'),
      accessBasis: required(options, 'access-basis'),
      accessedAt: required(options, 'accessed-at'),
      reason: options.reason,
    });
    process.stdout.write(`${JSON.stringify(renderSummary(manifest), null, 2)}\n`);
    return;
  }
  throw new Error(`unknown command: ${command}`);
}

main().catch((error) => {
  process.stderr.write(`${error.stack ?? error.message}\n\n${usage()}`);
  process.exitCode = 1;
});
