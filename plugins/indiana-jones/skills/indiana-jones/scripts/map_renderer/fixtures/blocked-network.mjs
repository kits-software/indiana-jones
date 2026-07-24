export async function install() {
  await fetch('http://127.0.0.1:9/render-job').catch(() => null);
  return {layerIds: []};
}
