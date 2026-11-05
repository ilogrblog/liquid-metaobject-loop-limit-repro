// Paste into the browser console on the preview storefront (same origin as the theme preview).
// Prints the probe lines for the plain URL, then for ?page=N and for the keyed page parameter.
(async () => {
  const read = async (qs) => {
    const t = await (await fetch('/' + qs, { credentials: 'same-origin' })).text();
    return [...t.matchAll(/PROBE [^<]*/g)].map(m => m[0]);
  };
  const out = { plain: await read('') };
  const key = (out.plain[0].match(/page_param="([^"]+)"/) || [])[1];
  out.page_param = key;
  for (const n of [1, 2, 3]) {
    out['?page=' + n] = await read('?page=' + n);
    out['?' + key + '=' + n] = await read('?' + key + '=' + n);
  }
  return JSON.stringify(out, null, 1);
})()
