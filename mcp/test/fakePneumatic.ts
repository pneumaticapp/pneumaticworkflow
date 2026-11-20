export const VALID_API_KEY = 'pn-valid-key';

export interface RecordedRequest {
  method: string;
  path: string;
  query: Record<string, string>;
  body: unknown;
  authorization: string | null;
}

interface StoredFile {
  name: string;
  type: string;
  data: Buffer;
}

type Responder = (request: RecordedRequest) => { status?: number; body?: unknown } | undefined;

const listRoutes: Array<[string, RegExp]> = [
  ['GET', /^\/accounts\/(?:users|groups)$/],
  ['GET', /^\/templates$/],
  ['GET', /^\/workflows(?:\/\d+\/events)?$/],
  ['GET', /^\/v3\/tasks$/],
  ['GET', /^\/reports\/(?:dashboard\/(?:workflows|tasks)\/breakdown|highlights)$/],
  ['GET', /^\/datasets$/],
  ['GET', /^\/attachments$/],
  ['GET', /^\/templates\/system(?:\/categories)?$/],
  ['GET', /^\/workflows\/(?:fields|count\/by-(?:workflow-starter|current-performer|template-task))$/],
  ['GET', /^\/reports\/dashboard\/(?:workflows\/by-tasks|tasks\/by-steps)$/],
  ['GET', /^\/accounts\/notifications$/],
  ['GET', /^\/v2\/tasks\/\d+\/events$/],
];

const objectRoutes: Array<[string, RegExp]> = [
  ['GET', /^\/templates\/\d+$/],
  ['GET', /^\/workflows\/\d+$/],
  ['GET', /^\/v2\/tasks\/\d+$/],
  ['GET', /^\/reports\/dashboard\/(?:workflows|tasks)\/overview$/],
  ['GET', /^\/datasets\/\d+$/],
  ['POST', /^\/templates\/\d+\/run$/],
  ['POST', /^\/workflows\/\d+\/(?:comment|snooze|resume)$/],
  ['POST', /^\/v2\/tasks\/\d+\/(?:complete|comment)$/],
  ['POST', /^\/v2\/tasks\/checklists\/\d+\/(?:mark|unmark)$/],
  ['PATCH', /^\/workflows\/\d+$/],
  ['POST', /^\/templates(?:\/ai|\/\d+\/clone|\/system\/\d+\/fill)?$/],
  ['PUT', /^\/templates\/\d+$/],
  ['GET', /^\/accounts\/user\/counters$/],
  ['GET', /^\/accounts\/(?:users|groups)\/\d+\/count-workflows$/],
  ['POST', /^\/accounts\/(?:user|users\/\d+)\/(?:activate|deactivate)-vacation$/],
  ['POST', /^\/accounts\/(?:users|groups)$/],
  ['PATCH', /^\/accounts\/users\/\d+$/],
  ['GET', /^\/accounts\/groups\/\d+$/],
  ['PUT', /^\/accounts\/groups\/\d+$/],
  ['PATCH', /^\/workflows\/comments\/\d+$/],
  ['POST', /^\/datasets(?:\/\d+\/items)?$/],
  ['PATCH', /^\/datasets(?:\/items)?\/\d+$/],
];

const emptyRoutes: Array<[string, RegExp]> = [
  ['POST', /^\/workflows\/\d+\/(?:return-to|finish)$/],
  ['POST', /^\/v2\/tasks\/\d+\/(?:revert|due-date|(?:create|delete)-(?:group-|guest-)?performer)$/],
  ['DELETE', /^\/workflows\/\d+$/],
  ['DELETE', /^\/v2\/tasks\/\d+\/due-date$/],
  ['DELETE', /^\/(?:templates|accounts\/users|accounts\/groups|workflows\/comments|datasets(?:\/items)?)\/\d+$/],
  ['POST', /^\/accounts\/users\/(?:reassign|\d+\/toggle-admin)$/],
  ['POST', /^\/accounts\/notifications\/read$/],
  ['POST', /^\/workflows\/comments\/\d+\/(?:create|delete)-reaction$/],
];

const matches = (routes: Array<[string, RegExp]>, { method, path }: RecordedRequest) =>
  routes.some(([routeMethod, pattern]) => routeMethod === method && pattern.test(path));

export function createFakePneumatic(apiUrl = 'https://pneumatic.test', filesUrl = 'https://app.pneumatic.test/files') {
  const requests: RecordedRequest[] = [];
  const responders: Responder[] = [];
  const files = new Map<string, StoredFile>();
  const filesPath = new URL(filesUrl).pathname;
  const state = { storageCacheWarm: true, storageDown: false };

  async function recordBody(body: unknown) {
    if (typeof body === 'string') {
      return JSON.parse(body);
    }
    if (body instanceof FormData) {
      const file = body.get('file');
      if (file instanceof Blob) {
        const data = Buffer.from(await file.arrayBuffer());
        return { file: { name: (file as File).name, type: file.type, size: data.length, data } };
      }
    }
    return undefined;
  }

  function storage(request: RecordedRequest): Response {
    if (state.storageDown) {
      return Response.json({ code: 'SERVER_ERROR', message: 'Down' }, { status: 503 });
    }
    if (request.authorization !== `Bearer ${VALID_API_KEY}` || !state.storageCacheWarm) {
      return Response.json({ code: 'AUTH_001', message: 'Authentication required' }, { status: 401 });
    }
    const route = request.path.slice(filesPath.length);
    if (request.method === 'POST' && route === '/upload') {
      const { file } = request.body as { file: { name: string; type: string; data: Buffer } };
      const fileId = `file-${files.size + 1}-0000`;
      files.set(fileId, { name: file.name, type: file.type, data: file.data });
      return Response.json({ file_id: fileId, public_url: `${filesUrl}/${fileId}` });
    }
    const stored = request.method === 'GET' ? files.get(decodeURIComponent(route.slice(1))) : undefined;
    if (!stored) {
      return Response.json({ code: 'FILE_001', message: 'File not found' }, { status: 404 });
    }
    return new Response(new Uint8Array(stored.data), {
      headers: {
        'Content-Type': stored.type,
        'Content-Length': String(stored.data.length),
        'Content-Disposition': `attachment; filename*=utf-8''${encodeURIComponent(stored.name)}`,
      },
    });
  }

  const fetchFn: typeof fetch = async (input, init) => {
    const url = new URL(typeof input === 'string' ? input : input instanceof URL ? input.href : input.url);
    const isStorage = url.href.startsWith(`${filesUrl}/`);
    if (url.origin !== apiUrl && !isStorage) {
      return fetch(input, init);
    }
    const headers = new Headers(init?.headers);
    const request: RecordedRequest = {
      method: init?.method ?? 'GET',
      path: url.pathname,
      query: Object.fromEntries(url.searchParams),
      body: await recordBody(init?.body),
      authorization: headers.get('authorization'),
    };
    requests.push(request);
    if (isStorage) {
      return storage(request);
    }

    if (request.authorization !== `Bearer ${VALID_API_KEY}`) {
      return Response.json({ detail: 'Invalid token.' }, { status: 401 });
    }
    for (const responder of responders) {
      const response = responder(request);
      if (response) {
        return response.body === undefined
          ? new Response(null, { status: response.status ?? 204 })
          : Response.json(response.body, { status: response.status ?? 200 });
      }
    }
    if (request.method === 'GET' && request.path === '/accounts/user') {
      state.storageCacheWarm = true;
      return Response.json({ id: 7, email: 'ada@example.com', first_name: 'Ada' });
    }
    if (matches(listRoutes, request)) {
      return Response.json({ count: 0, next: null, previous: null, results: [] });
    }
    if (matches(objectRoutes, request)) {
      return Response.json({ id: Number(/\d+/.exec(request.path)?.[0] ?? 1) });
    }
    if (matches(emptyRoutes, request)) {
      return new Response(null, { status: 204 });
    }
    return Response.json({ detail: 'Unknown fake API route' }, { status: 404 });
  };

  return {
    apiUrl,
    filesUrl,
    fetchFn,
    requests,
    files,
    state,
    // The latest responder wins, so a test can override defaults registered in beforeEach.
    respond(responder: Responder) {
      responders.unshift(responder);
    },
    lastRequest(path: string) {
      return requests.filter((request) => request.path === path).at(-1);
    },
  };
}
