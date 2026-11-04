export interface AuthorizePageParams {
  clientName: string;
  redirectHost: string;
  hiddenFields: Record<string, string>;
  error?: string;
}

// Only upload pages restrict form-action: CSP form-action also covers redirects after a submit, and the consent form
// redirects to the client's callback.
export function pageHeaders({ formActionSelf = false }: { formActionSelf?: boolean } = {}): Record<string, string> {
  const directives = [
    "default-src 'none'",
    "style-src 'unsafe-inline'",
    ...(formActionSelf ? ["form-action 'self'"] : []),
    "frame-ancestors 'none'",
  ];
  return { 'X-Frame-Options': 'DENY', 'Content-Security-Policy': directives.join('; ') };
}

const STYLES = `
  :root { color-scheme: light dark; font-family: system-ui, -apple-system, sans-serif; }
  body { margin: 0; min-height: 100vh; display: grid; place-items: center; background: Canvas; }
  main { width: min(26rem, calc(100vw - 2rem)); padding: 2rem; border: 1px solid #8884; border-radius: 1rem; }
  h1 { font-size: 1.25rem; margin: 0 0 0.75rem; }
  p { line-height: 1.5; margin: 0 0 1rem; color: GrayText; }
  strong { color: CanvasText; }
  label { display: block; font-weight: 600; margin-bottom: 0.5rem; }
  input { box-sizing: border-box; width: 100%; padding: 0.625rem 0.75rem; font: inherit; border: 1px solid #8888; border-radius: 0.5rem; }
  button { margin-top: 1rem; width: 100%; padding: 0.7rem; font: inherit; font-weight: 600; border: 0; border-radius: 0.5rem; background: #ff7a00; color: #fff; cursor: pointer; }
  .error { color: #d33; margin-top: 0.75rem; }
  .hint { font-size: 0.875rem; margin-top: 1rem; }
`;

function escapeHtml(value: string): string {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function layout(title: string, body: string): string {
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="referrer" content="same-origin">
<title>${escapeHtml(title)}</title>
<style>${STYLES}</style>
</head>
<body><main>${body}</main></body>
</html>`;
}

export function renderAuthorizePage({ clientName, redirectHost, hiddenFields, error }: AuthorizePageParams): string {
  const hidden = Object.entries(hiddenFields)
    .map(([name, value]) => `<input type="hidden" name="${escapeHtml(name)}" value="${escapeHtml(value)}">`)
    .join('');

  return layout(
    'Connect Pneumatic',
    `<h1>Connect Pneumatic</h1>
<p><strong>${escapeHtml(clientName)}</strong> (${escapeHtml(redirectHost)}) wants to work with your Pneumatic
workflows, tasks and templates on your behalf.</p>
<form method="post" action="authorize" autocomplete="off">
${hidden}
<label for="api_key">Pneumatic API key</label>
<input id="api_key" name="api_key" type="password" required autofocus spellcheck="false">
${error ? `<p class="error" role="alert">${escapeHtml(error)}</p>` : ''}
<button type="submit">Allow access</button>
</form>
<p class="hint">Create a key in Pneumatic: <strong>Integrations → Your API Keys → Create</strong>
(admins only; the key is shown once). The connector acts with the same permissions as the key owner.</p>`,
  );
}

export function renderErrorPage(message: string): string {
  return layout('Authorization error', `<h1>Authorization error</h1><p>${escapeHtml(message)}</p>`);
}

export function renderUploadPage({
  filename,
  limit,
  error,
}: {
  filename: string | null;
  limit: string;
  error?: string;
}) {
  return layout(
    'Upload a file to Pneumatic',
    `<h1>Upload a file to Pneumatic</h1>
<p>Claude asked for ${filename ? `<strong>${escapeHtml(filename)}</strong>` : 'a file'}. Choose it on your device
(up to ${escapeHtml(limit)}); it is stored in Pneumatic with your permissions and is not attached anywhere yet.</p>
<form method="post" enctype="multipart/form-data">
<label for="file">File</label>
<input id="file" name="file" type="file" required>
${error ? `<p class="error" role="alert">${escapeHtml(error)}</p>` : ''}
<button type="submit">Upload</button>
</form>`,
  );
}

export function renderUploadDonePage(name: string) {
  return layout(
    'File uploaded',
    `<h1>File uploaded</h1><p><strong>${escapeHtml(name)}</strong> is stored in Pneumatic. Return to Claude to continue.</p>`,
  );
}
