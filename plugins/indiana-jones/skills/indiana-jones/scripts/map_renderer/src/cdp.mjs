import {access, mkdtemp, readFile, rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {delimiter, join} from 'node:path';
import {spawn} from 'node:child_process';

function unique(values) {
  return [...new Set(values.filter(Boolean))];
}

async function firstExecutable(candidates) {
  for (const candidate of unique(candidates)) {
    try {
      await access(candidate);
      return candidate;
    } catch {
      continue;
    }
  }
  return null;
}

function pathExecutables(names) {
  const directories = (process.env.PATH ?? '').split(delimiter).filter(Boolean);
  const suffix = process.platform === 'win32' ? '.exe' : '';
  return directories.flatMap((directory) =>
    names.map((name) => join(directory, `${name}${suffix}`)),
  );
}

export async function discoverBrowser(explicitPath = process.env.IJ_BROWSER_PATH) {
  /*
   * Prefer an explicit path, then branded browsers available on both target
   * operating systems. We intentionally do not disable the GPU: Chromium can
   * choose native acceleration or SwiftShader while preserving WebGL2.
   */

  if (explicitPath) {
    const executable = await firstExecutable([explicitPath]);
    if (!executable) {
      throw new Error(`browser executable does not exist: ${explicitPath}`);
    }
    return executable;
  }
  const home = process.env.HOME ?? '';
  const localAppData = process.env.LOCALAPPDATA ?? '';
  const programFiles = process.env.ProgramFiles ?? '';
  const programFilesX86 = process.env['ProgramFiles(x86)'] ?? '';
  const candidates =
    process.platform === 'darwin'
      ? [
          '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
          '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
          '/Applications/Chromium.app/Contents/MacOS/Chromium',
          join(home, 'Applications/Google Chrome.app/Contents/MacOS/Google Chrome'),
        ]
      : process.platform === 'win32'
        ? [
            join(programFiles, 'Google/Chrome/Application/chrome.exe'),
            join(programFilesX86, 'Google/Chrome/Application/chrome.exe'),
            join(localAppData, 'Google/Chrome/Application/chrome.exe'),
            join(programFiles, 'Microsoft/Edge/Application/msedge.exe'),
            join(programFilesX86, 'Microsoft/Edge/Application/msedge.exe'),
          ]
        : [
            ...pathExecutables([
              'google-chrome',
              'google-chrome-stable',
              'chromium',
              'chromium-browser',
              'microsoft-edge',
            ]),
          ];
  const executable = await firstExecutable(candidates);
  if (!executable) {
    throw new Error(
      'no Chrome, Edge, or Chromium executable found; set IJ_BROWSER_PATH',
    );
  }
  return executable;
}

class CdpConnection {
  constructor(socket) {
    this.socket = socket;
    this.nextId = 1;
    this.pending = new Map();
    this.listeners = new Map();
    socket.addEventListener('message', (event) => this.receive(event.data));
    socket.addEventListener('close', () => this.rejectPending('CDP socket closed'));
    socket.addEventListener('error', () => this.rejectPending('CDP socket failed'));
  }

  receive(data) {
    const message = JSON.parse(data);
    if (!message.id) {
      const listeners = this.listeners.get(message.method) ?? [];
      for (const listener of listeners) {
        Promise.resolve(listener(message.params ?? {}, message.sessionId)).catch(
          () => {},
        );
      }
      return;
    }
    const pending = this.pending.get(message.id);
    if (!pending) {
      return;
    }
    this.pending.delete(message.id);
    clearTimeout(pending.timer);
    if (message.error) {
      pending.reject(
        new Error(`${pending.method} failed: ${message.error.message}`),
      );
      return;
    }
    pending.resolve(message.result ?? {});
  }

  rejectPending(message) {
    for (const pending of this.pending.values()) {
      clearTimeout(pending.timer);
      pending.reject(new Error(message));
    }
    this.pending.clear();
  }

  send(method, params = {}, sessionId = undefined, timeoutMs = 15_000) {
    const id = this.nextId++;
    const payload = {id, method, params};
    if (sessionId) {
      payload.sessionId = sessionId;
    }
    return new Promise((resolvePromise, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`${method} timed out after ${timeoutMs} ms`));
      }, timeoutMs);
      this.pending.set(id, {
        method,
        resolve: resolvePromise,
        reject,
        timer,
      });
      this.socket.send(JSON.stringify(payload));
    });
  }

  on(method, listener) {
    const listeners = this.listeners.get(method) ?? [];
    listeners.push(listener);
    this.listeners.set(method, listeners);
    return () => {
      const current = this.listeners.get(method) ?? [];
      this.listeners.set(
        method,
        current.filter((candidate) => candidate !== listener),
      );
    };
  }

  async close() {
    this.socket.close();
  }
}

async function waitForDevToolsPort(profileDirectory, processHandle, timeoutMs) {
  /*
   * Chrome writes both the selected ephemeral port and browser target id.
   * Polling this file avoids racing a hard-coded debugging port on parallel
   * renders and works identically on macOS, Windows, and Linux.
   */

  const portFile = join(profileDirectory, 'DevToolsActivePort');
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (processHandle.launchError) {
      throw new Error(`browser failed to launch: ${processHandle.launchError.message}`);
    }
    if (processHandle.exitCode !== null) {
      throw new Error(`browser exited before CDP became ready (${processHandle.exitCode})`);
    }
    try {
      const [port, targetPath] = (await readFile(portFile, 'utf8')).trim().split(/\r?\n/u);
      if (port && targetPath) {
        return {port: Number.parseInt(port, 10), targetPath};
      }
    } catch {
      await new Promise((resolvePromise) => setTimeout(resolvePromise, 50));
    }
    await new Promise((resolvePromise) => setTimeout(resolvePromise, 10));
  }
  throw new Error(`browser did not expose CDP within ${timeoutMs} ms`);
}

async function connectWebSocket(url, timeoutMs = 10_000) {
  return await new Promise((resolvePromise, reject) => {
    const socket = new WebSocket(url);
    const timer = setTimeout(() => {
      socket.close();
      reject(new Error(`timed out connecting to ${url}`));
    }, timeoutMs);
    socket.addEventListener(
      'open',
      () => {
        clearTimeout(timer);
        resolvePromise(socket);
      },
      {once: true},
    );
    socket.addEventListener(
      'error',
      () => {
        clearTimeout(timer);
        reject(new Error(`failed connecting to ${url}`));
      },
      {once: true},
    );
  });
}

export async function launchBrowser(options = {}) {
  const executable = await discoverBrowser(options.executablePath);
  const profileDirectory = await mkdtemp(join(tmpdir(), 'ij-map-renderer-'));
  const args = [
    '--headless=new',
    '--remote-debugging-port=0',
    `--user-data-dir=${profileDirectory}`,
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-background-networking',
    '--disable-component-update',
    '--disable-sync',
    '--metrics-recording-only',
    '--mute-audio',
    'about:blank',
  ];
  if (options.noSandbox || process.env.IJ_BROWSER_NO_SANDBOX === '1') {
    args.splice(args.length - 1, 0, '--no-sandbox');
  }
  if (options.singleProcess || process.env.IJ_BROWSER_SINGLE_PROCESS === '1') {
    args.splice(args.length - 1, 0, '--single-process', '--no-zygote');
  }
  if (options.softwareGl || process.env.IJ_BROWSER_SOFTWARE_GL === '1') {
    args.splice(
      args.length - 1,
      0,
      '--use-gl=angle',
      '--use-angle=swiftshader',
      '--enable-unsafe-swiftshader',
    );
  }
  const processHandle = spawn(executable, args, {
    stdio: ['ignore', 'pipe', 'pipe'],
    windowsHide: true,
  });
  processHandle.launchError = null;
  processHandle.once('error', (error) => {
    processHandle.launchError = error;
  });
  let stderr = '';
  processHandle.stderr.setEncoding('utf8');
  processHandle.stderr.on('data', (chunk) => {
    if (stderr.length < 64_000) {
      stderr += chunk;
    }
  });
  let connection;
  try {
    const {port, targetPath} = await waitForDevToolsPort(
      profileDirectory,
      processHandle,
      options.timeoutMs ?? 10_000,
    );
    const socket = await connectWebSocket(`ws://127.0.0.1:${port}${targetPath}`);
    connection = new CdpConnection(socket);
    return {
      executable,
      connection,
      stderr: () => stderr,
      async close() {
        try {
          await connection.send('Browser.close', {}, undefined, 3_000);
        } catch {
          processHandle.kill();
        }
        if (processHandle.exitCode === null) {
          await Promise.race([
            new Promise((resolvePromise) =>
              processHandle.once('exit', resolvePromise),
            ),
            new Promise((resolvePromise) => setTimeout(resolvePromise, 2_000)),
          ]);
        }
        if (processHandle.exitCode === null) {
          processHandle.kill();
          await Promise.race([
            new Promise((resolvePromise) =>
              processHandle.once('exit', resolvePromise),
            ),
            new Promise((resolvePromise) => setTimeout(resolvePromise, 2_000)),
          ]);
        }
        await connection.close();
        await rm(profileDirectory, {
          recursive: true,
          force: true,
          maxRetries: 3,
          retryDelay: 100,
        });
      },
    };
  } catch (error) {
    processHandle.kill();
    if (processHandle.exitCode === null) {
      await Promise.race([
        new Promise((resolvePromise) => processHandle.once('exit', resolvePromise)),
        new Promise((resolvePromise) => setTimeout(resolvePromise, 2_000)),
      ]);
    }
    await rm(profileDirectory, {
      recursive: true,
      force: true,
      maxRetries: 3,
      retryDelay: 100,
    });
    const detail = stderr.trim();
    throw new Error(detail ? `${error.message}\n${detail}` : error.message);
  }
}

export async function createPage(browser, viewport) {
  const {targetId} = await browser.connection.send('Target.createTarget', {
    url: 'about:blank',
  });
  const {sessionId} = await browser.connection.send('Target.attachToTarget', {
    targetId,
    flatten: true,
  });
  await browser.connection.send('Page.enable', {}, sessionId);
  await browser.connection.send('Runtime.enable', {}, sessionId);
  await browser.connection.send(
    'Emulation.setDeviceMetricsOverride',
    {
      width: viewport.width,
      height: viewport.height,
      deviceScaleFactor: viewport.pixelRatio,
      mobile: false,
      screenWidth: viewport.width,
      screenHeight: viewport.height,
    },
    sessionId,
  );
  const requests = [];
  let removeFetchListener = null;
  let rendererOrigin = null;
  return {
    sessionId,
    async setNetworkPolicy(policy, rendererUrl) {
      /*
       * Intercept every browser request so a local adapter cannot silently
       * widen its network authority. Only the exact renderer origin plus
       * data/blob URLs are implicit; every remote host needs an allowlist.
       */

      const allowedHosts = new Set(policy.allowedHosts);
      rendererOrigin = new URL(rendererUrl).origin;
      const interceptedSessions = new Set([sessionId]);
      const enableSession = async (targetSessionId) => {
        await browser.connection.send(
          'Fetch.enable',
          {patterns: [{urlPattern: '*', requestStage: 'Request'}]},
          targetSessionId,
        );
        try {
          await browser.connection.send(
            'Target.setAutoAttach',
            {
              autoAttach: true,
              waitForDebuggerOnStart: true,
              flatten: true,
            },
            targetSessionId,
          );
        } catch {
          return;
        }
      };
      removeFetchListener = browser.connection.on(
        'Fetch.requestPaused',
        async (event, eventSessionId) => {
          if (!interceptedSessions.has(eventSessionId)) {
            return;
          }
          let allowed = false;
          let origin = null;
          try {
            const url = new URL(event.request.url);
            origin = url.origin === 'null' ? url.protocol : url.origin;
            allowed =
              url.protocol === 'data:' ||
              url.protocol === 'blob:' ||
              url.origin === rendererOrigin ||
              allowedHosts.has(url.hostname.toLowerCase());
          } catch {
            allowed = false;
          }
          requests.push({
            origin,
            method: event.request.method,
            allowed,
          });
          await browser.connection.send(
            allowed ? 'Fetch.continueRequest' : 'Fetch.failRequest',
            allowed
              ? {requestId: event.requestId}
              : {requestId: event.requestId, errorReason: 'BlockedByClient'},
            eventSessionId,
          );
        },
      );
      const removeAttachListener = browser.connection.on(
        'Target.attachedToTarget',
        async (event, parentSessionId) => {
          if (!interceptedSessions.has(parentSessionId)) {
            return;
          }
          interceptedSessions.add(event.sessionId);
          try {
            await enableSession(event.sessionId);
          } finally {
            await browser.connection.send(
              'Runtime.runIfWaitingForDebugger',
              {},
              event.sessionId,
            );
          }
        },
      );
      const previousRemoveListener = removeFetchListener;
      removeFetchListener = () => {
        previousRemoveListener();
        removeAttachListener();
      };
      await enableSession(sessionId);
    },
    networkSummary() {
      const remoteOrigins = new Set();
      const blockedOrigins = new Set();
      for (const request of requests) {
        if (
          request.origin &&
          request.origin !== rendererOrigin &&
          request.origin !== 'data:' &&
          request.origin !== 'blob:'
        ) {
          (request.allowed ? remoteOrigins : blockedOrigins).add(request.origin);
        }
      }
      return {
        requestCount: requests.length,
        blockedRequestCount: requests.filter((request) => !request.allowed).length,
        remoteOrigins: [...remoteOrigins].sort(),
        blockedOrigins: [...blockedOrigins].sort(),
      };
    },
    async navigate(url) {
      const result = await browser.connection.send('Page.navigate', {url}, sessionId);
      if (result.errorText) {
        throw new Error(`navigation failed: ${result.errorText}`);
      }
    },
    async evaluate(expression) {
      const result = await browser.connection.send(
        'Runtime.evaluate',
        {
          expression,
          returnByValue: true,
          awaitPromise: true,
        },
        sessionId,
      );
      if (result.exceptionDetails) {
        throw new Error(
          result.exceptionDetails.exception?.description ??
            result.exceptionDetails.text ??
            'page evaluation failed',
        );
      }
      return result.result.value;
    },
    async screenshot() {
      const result = await browser.connection.send(
        'Page.captureScreenshot',
        {
          format: 'png',
          fromSurface: true,
          captureBeyondViewport: false,
        },
        sessionId,
      );
      return Buffer.from(result.data, 'base64');
    },
    async close() {
      if (removeFetchListener) {
        removeFetchListener();
      }
      await browser.connection.send(
        'Target.closeTarget',
        {targetId},
      );
    },
  };
}
