// <reference types="jest" />
import { connectMcp, getMcpUploadSession, isMcpEnabled, McpApiError, navigateMcp, uploadMcpFile } from '../mcp';
import { IMcpUploadSession } from '../../types/mcp';
import { getBrowserConfigEnv } from '../../utils/getConfig';

jest.mock('../../utils/getConfig', () => ({
  getBrowserConfigEnv: jest.fn(),
}));

describe('MCP browser requests', () => {
  const ID = '550e8400-e29b-41d4-a716-446655440000';
  const originalLocation = window.location;
  const mockFetch = jest.fn();
  const session: IMcpUploadSession = {
    id: ID,
    user_id: 7,
    account_id: 9,
    status: 'pending',
    expires_at: '2099-01-01T00:00:00Z',
    filename: 'report.pdf',
    content_type: 'application/pdf',
    size: 100,
  };
  const response = (data: unknown) => ({ ok: true, status: 200, json: jest.fn().mockResolvedValue(data) });
  const token = (overrides: Record<string, unknown> = {}) => ({
    access_token: 'mcp-u_limited',
    upload_session_id: ID,
    expires_in: 300,
    file_upload_url: 'https://my.pneumatic.app/files/upload',
    ...overrides,
  });

  beforeEach(() => {
    jest.clearAllMocks();
    (getBrowserConfigEnv as jest.Mock).mockReturnValue({
      featureFlags: { MCP_PUBLIC_URL: 'https://my.pneumatic.app/mcp' },
    });
    Object.defineProperty(global, 'fetch', { value: mockFetch, configurable: true });
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { ...originalLocation, origin: 'https://my.pneumatic.app', assign: jest.fn() },
    });
  });
  afterAll(() => Object.defineProperty(window, 'location', { configurable: true, value: originalLocation }));

  it.each(['no', 'true', 'false', '1', 'YES', '', undefined])(
    'test_isMcpEnabled__hides_MCP_for_MCP_ENABLED_%p__rejects',
    (value) => {
      // arrange
      (getBrowserConfigEnv as jest.Mock).mockReturnValue({ featureFlags: { MCP_ENABLED: value } });

      // act
      const enabled = isMcpEnabled();

      // assert
      expect(enabled).toBe(false);
    },
  );
  it('test_isMcpEnabled__enables_MCP_only_for_literal_yes__ok', () => {
    // arrange
    (getBrowserConfigEnv as jest.Mock).mockReturnValue({ featureFlags: { MCP_ENABLED: 'yes' } });

    // act
    const enabled = isMcpEnabled();

    // assert
    expect(enabled).toBe(true);
  });
  it('test_connectMcp__uses_the_cookie_session_and_CSRF_without_a_user_Bearer_in__ok', async () => {
    // arrange
    mockFetch.mockResolvedValue(response({ redirect_url: 'fixed' }));

    // act
    await connectMcp(ID, 'csrf');

    // assert
    expect(mockFetch).toHaveBeenCalledTimes(1);
    expect(mockFetch).toHaveBeenCalledWith(
      '/mcp/connect',
      expect.objectContaining({
        credentials: 'same-origin',
        cache: 'no-store',
        referrerPolicy: 'no-referrer',
        headers: { 'Content-Type': 'application/json', 'X-MCP-CSRF': 'csrf' },
        body: JSON.stringify({ request_id: ID }),
      }),
    );
  });
  it('test_getMcpUploadSession__rejects_malicious_session_IDs_before_a_netwo__rejects', () => {
    // arrange
    let error: unknown;

    // act
    try {
      getMcpUploadSession('../secret');
    } catch (reason) {
      error = reason;
    }

    // assert
    expect(error).toBeInstanceOf(McpApiError);
    expect(error).toMatchObject({ status: 400, message: 'MCP request failed' });
    expect(mockFetch).not.toHaveBeenCalled();
  });
  it('test_uploadMcpFile__uploads_with_an_ephemeral_session_capability_and_ignore__ok', async () => {
    // arrange
    mockFetch
      .mockResolvedValueOnce(response(token()))
      .mockResolvedValueOnce(response({ file_id: 'untrusted-file-id' }));
    const onDispatch = jest.fn();

    // act
    await uploadMcpFile(
      new File(['pdf'], 'local.pdf', { type: 'application/pdf' }),
      session,
      'csrf',
      undefined,
      onDispatch,
    );

    // assert
    expect(onDispatch).toHaveBeenCalledTimes(1);
    expect(onDispatch).toHaveBeenCalledWith();
    expect(mockFetch).toHaveBeenLastCalledWith(
      'https://my.pneumatic.app/files/upload',
      expect.objectContaining({
        headers: { Authorization: 'Bearer mcp-u_limited', 'X-MCP-Upload-Session': ID },
        credentials: 'omit',
        redirect: 'error',
      }),
    );
    expect(mockFetch).toHaveBeenCalledTimes(2);
    expect(mockFetch).toHaveBeenNthCalledWith(1, `/mcp/uploads/${ID}/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-MCP-CSRF': 'csrf' },
      body: '{}',
      signal: undefined,
      credentials: 'same-origin',
      cache: 'no-store',
      referrerPolicy: 'no-referrer',
      redirect: 'error',
    });
    expect(sessionStorage.length).toBe(0);
    expect(localStorage.length).toBe(0);
  });
  it('test_uploadMcpFile__refuses_an_arbitrary_storage_URL_before_transmitti__rejects', async () => {
    // arrange
    mockFetch.mockResolvedValueOnce(response(token({ file_upload_url: 'https://evil.example/upload' })));
    const onDispatch = jest.fn();
    const file = new File(['pdf'], 'report.pdf');

    // act
    const error = await uploadMcpFile(file, session, 'csrf', undefined, onDispatch).catch((reason: unknown) => reason);

    // assert
    expect(error).toBeInstanceOf(McpApiError);
    expect(error).toMatchObject({ status: 400, message: 'MCP request failed' });
    expect(mockFetch).toHaveBeenCalledTimes(1);
    expect(mockFetch).toHaveBeenCalledWith(`/mcp/uploads/${ID}/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-MCP-CSRF': 'csrf' },
      body: '{}',
      signal: undefined,
      credentials: 'same-origin',
      cache: 'no-store',
      referrerPolicy: 'no-referrer',
      redirect: 'error',
    });
    expect(onDispatch).not.toHaveBeenCalled();
  });
  it('test_uploadMcpFile__does_not_mark_byte_dispatch_when_the_token_request__rejects', async () => {
    // arrange
    mockFetch.mockResolvedValueOnce({ ok: false, status: 503 });
    const onDispatch = jest.fn();
    const file = new File(['pdf'], 'report.pdf');

    // act
    const error = await uploadMcpFile(file, session, 'csrf', undefined, onDispatch).catch((reason: unknown) => reason);

    // assert
    expect(error).toBeInstanceOf(McpApiError);
    expect(error).toMatchObject({ status: 503, message: 'MCP request failed' });
    expect(mockFetch).toHaveBeenCalledTimes(1);
    expect(mockFetch).toHaveBeenCalledWith(`/mcp/uploads/${ID}/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-MCP-CSRF': 'csrf' },
      body: '{}',
      signal: undefined,
      credentials: 'same-origin',
      cache: 'no-store',
      referrerPolicy: 'no-referrer',
      redirect: 'error',
    });
    expect(onDispatch).not.toHaveBeenCalled();
  });
  it.each([
    'https://evil.example/oauth/mcp/login?code=code',
    `https://my.pneumatic.app/redirect?code=code&request_id=${ID}`,
    `https://my.pneumatic.app/oauth/mcp/login?code=code&request_id=${ID}&next=https://evil.example`,
  ])('test_navigateMcp__refuses_untrusted_browser_navigation_%s__rejects', (url) => {
    // arrange
    let error: unknown;

    // act
    try {
      navigateMcp(url);
    } catch (reason) {
      error = reason;
    }

    // assert
    expect(error).toBeInstanceOf(McpApiError);
    expect(error).toMatchObject({ status: 400, message: 'MCP request failed' });
    expect(window.location.assign).not.toHaveBeenCalled();
  });
  it('test_navigateMcp__navigates_only_to_the_configured_one_time_login_route__ok', () => {
    // arrange
    const url = `https://my.pneumatic.app/oauth/mcp/login?code=code&request_id=${ID}`;

    // act
    navigateMcp(url);

    // assert
    expect(window.location.assign).toHaveBeenCalledWith(url);
  });
});
