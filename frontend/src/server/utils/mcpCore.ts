import axios from 'axios';
import { serverApi } from './request';

export class McpCoreError extends Error {
  constructor(public readonly status: number) {
    super('MCP request failed');
  }
}

// Never pass upstream bodies, headers, or Axios errors to a browser or logger.
export async function mcpCore<T>(
  method: 'GET' | 'POST' | 'DELETE',
  path: string,
  token: string,
  data?: unknown,
): Promise<T> {
  try {
    const response = await axios.request<T>({
      method,
      url: serverApi.getUrl(path),
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      data,
      timeout: 15000,
      proxy: false,
      maxRedirects: 0,
      maxContentLength: 1024 * 1024,
    });
    return response.data;
  } catch (error) {
    const status = axios.isAxiosError(error) ? error.response?.status : undefined;
    throw new McpCoreError(status && [400, 401, 403, 404, 409, 410, 429].includes(status) ? status : 502);
  }
}
