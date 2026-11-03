// ESM loader for smoke.js: bare 'three' -> the vendored build.
import { pathToFileURL, fileURLToPath } from 'node:url';
import path from 'node:path';
const here = path.dirname(fileURLToPath(import.meta.url));
const THREE = pathToFileURL(path.join(here, '..', 'vendor', 'three', 'three.module.js')).href;
export async function resolve(specifier, context, next) {
  if (specifier === 'three') return { url: THREE, shortCircuit: true };
  return next(specifier, context);
}
