// <reference types="jest" />
import axios from 'axios';
import { mcpCore, McpCoreError } from '../mcpCore';

jest.mock('axios', () => ({ __esModule: true, default: { request: jest.fn(), isAxiosError: jest.fn(() => true) } }));
jest.mock('../request', () => ({ serverApi: { getUrl: (path: string) => `http://core${path}` } }));

describe('MCP core requests', () => {
  beforeEach(() => jest.clearAllMocks());
  it('test_mcpCore__cookie_handoff__uses_Bearer_without_redirects', async () => {
    // arrange
    (axios.request as jest.Mock).mockResolvedValue({ data: { code: 'one-use' } });
    const data = { request_id: 'request' };

    // act
    const result = await mcpCore('POST', '/integrations/mcp/login-code', 'cookie-session', data);

    // assert
    expect(result).toEqual({ code: 'one-use' });
    expect(axios.request).toHaveBeenCalledTimes(1);
    expect(axios.request).toHaveBeenCalledWith({
      url: 'http://core/integrations/mcp/login-code',
      method: 'POST',
      headers: { Authorization: 'Bearer cookie-session', 'Content-Type': 'application/json' },
      data,
      timeout: 15000,
      proxy: false,
      maxRedirects: 0,
      maxContentLength: 1024 * 1024,
    });
    expect(axios.isAxiosError).not.toHaveBeenCalled();
  });
  it('test_mcpCore__upstream_failure__discards_sensitive_payload', async () => {
    // arrange
    const upstream = {
      response: { status: 403, data: { credential: 'secret' } },
      config: { headers: { Authorization: 'secret' } },
    };
    (axios.request as jest.Mock).mockRejectedValue(upstream);

    // act
    const error = await mcpCore('GET', '/auth/context', 'token').catch((reason: unknown) => reason);

    // assert
    expect(error).toBeInstanceOf(McpCoreError);
    expect(error).toMatchObject({
      status: 403,
      message: 'MCP request failed',
    });
    expect(error).not.toHaveProperty('response');
    expect(error).not.toHaveProperty('config');
    expect(axios.request).toHaveBeenCalledTimes(1);
    expect(axios.request).toHaveBeenCalledWith({
      method: 'GET',
      url: 'http://core/auth/context',
      headers: { Authorization: 'Bearer token', 'Content-Type': 'application/json' },
      data: undefined,
      timeout: 15000,
      proxy: false,
      maxRedirects: 0,
      maxContentLength: 1024 * 1024,
    });
    expect(axios.isAxiosError).toHaveBeenCalledTimes(1);
    expect(axios.isAxiosError).toHaveBeenCalledWith(upstream);
  });
});
