// <reference types="jest" />
import * as React from 'react';
import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { RouteComponentProps } from 'react-router-dom';
import { intlMock } from '../../../__stubs__/intlMock';
import { McpConnect } from '../McpConnect';
import { McpConnections } from '../McpConnections';
import { McpConnectionsLink } from '../McpConnectionsLink';
import { McpUpload } from '../McpUpload';
import {
  approveMcp,
  connectMcp,
  getMcpConsent,
  getMcpConnections,
  getMcpUploadSession,
  isMcpEnabled,
  McpApiError,
  navigateMcp,
  revokeMcpConnection,
  uploadMcpFile,
} from '../../../api/mcp';

jest.mock('../../../api/mcp', () => ({
  ...jest.requireActual('../../../api/mcp'),
  approveMcp: jest.fn(),
  connectMcp: jest.fn(),
  getMcpConsent: jest.fn(),
  getMcpConnections: jest.fn(),
  getMcpUploadSession: jest.fn(),
  isMcpEnabled: jest.fn(),
  navigateMcp: jest.fn(),
  revokeMcpConnection: jest.fn(),
  uploadMcpFile: jest.fn(),
}));
jest.mock('../../UI/Buttons/Button/Button', () => ({
  Button: ({
    label,
    disabled,
    isLoading,
    onClick,
    type,
    ...attributes
  }: {
    label: string;
    disabled?: boolean;
    isLoading?: boolean;
    onClick?(event: React.MouseEvent): void;
    type?: 'submit' | 'button';
  }) => (
    <button {...attributes} type={type || 'button'} disabled={disabled || isLoading} onClick={onClick}>
      {label}
    </button>
  ),
}));

describe('MCP pages', () => {
  const ID = '550e8400-e29b-41d4-a716-446655440000';
  const t = (id: string) => intlMock.formatMessage({ id });
  const CONTINUE = t('mcp.connect.continue');
  const ALLOW = t('mcp.connect.allow');
  const DENY = t('mcp.connect.deny');
  const DISCONNECT = t('mcp.connections.revoke');
  const CONFIRM = t('mcp.connections.confirm-revoke');
  const UPLOAD = t('mcp.upload.submit');
  const FILE = t('mcp.upload.file');
  const COMPLETE = t('mcp.upload.complete');
  const REFRESH = t('mcp.upload.refresh');
  const makeConsent = (overrides: Record<string, unknown> = {}) => ({
    request_id: ID,
    client_name: 'Assistant',
    account_name: 'My account',
    scopes: ['pneumatic:read', 'files:write'],
    login_complete: false,
    csrf_token: 'csrf',
    ...overrides,
  });
  const makeConnection = (overrides: Record<string, unknown> = {}) => ({
    id: ID,
    client_name: 'Assistant',
    user_id: 7,
    account_id: 9,
    scopes: ['pneumatic:read'],
    created_at: '2026-10-09T00:00:00Z',
    revoked_at: null,
    ...overrides,
  });
  const makeSession = (overrides: Record<string, unknown> = {}) => ({
    id: ID,
    user_id: 7,
    account_id: 9,
    status: 'pending',
    filename: 'report.pdf',
    size: 3,
    content_type: 'application/pdf',
    expires_at: '2099-01-01T00:00:00Z',
    ...overrides,
  });
  const makeUploadProps = (id: string = ID) =>
    ({ match: { params: { session_id: id } } }) as unknown as RouteComponentProps<{ session_id: string }>;
  const chooseFile = (file: File = new File(['pdf'], 'report.pdf', { type: 'application/pdf' })) =>
    userEvent.upload(screen.getByLabelText(FILE), file);
  const deferred = <T,>() => {
    let resolve!: (value: T) => void;
    const promise = new Promise<T>((complete) => {
      resolve = complete;
    });
    return { promise, resolve };
  };

  beforeEach(() => {
    jest.clearAllMocks();
    window.history.replaceState({}, '', `/mcp/connect?request_id=${ID}`);
    (getMcpConsent as jest.Mock).mockResolvedValue(makeConsent());
    (getMcpConnections as jest.Mock).mockResolvedValue({ results: [makeConnection()], csrf_token: 'csrf' });
    (getMcpUploadSession as jest.Mock).mockResolvedValue({ session: makeSession(), csrf_token: 'csrf' });
    (connectMcp as jest.Mock).mockResolvedValue({ redirect_url: 'fixed-login' });
    (approveMcp as jest.Mock).mockResolvedValue({ redirect_url: 'fixed-consent' });
    (revokeMcpConnection as jest.Mock).mockResolvedValue(undefined);
    (uploadMcpFile as jest.Mock).mockImplementation(async (_file, _session, _csrf, _signal, onDispatch) => {
      onDispatch?.();
    });
  });

  it('test_McpConnect__requires_confirmation_before_creating_the_login_handoff__ok', async () => {
    // arrange

    // act
    render(<McpConnect />);
    userEvent.click(await screen.findByRole('button', { name: CONTINUE }));
    await waitFor(() => expect(connectMcp).toHaveBeenCalledWith(ID, 'csrf'));

    // assert
    expect(approveMcp).not.toHaveBeenCalled();
    expect(navigateMcp).toHaveBeenCalledWith('fixed-login');
  });
  it.each([
    ['mcp.connect.allow', true],
    ['mcp.connect.deny', false],
  ])('test_McpConnect__submits_%s_after_the_login_to_consent_return__ok', async (label, allow) => {
    // arrange
    window.history.replaceState({}, '', `/mcp/connect?request_id=${ID}&step=consent`);
    (getMcpConsent as jest.Mock).mockResolvedValue(makeConsent({ login_complete: true }));

    // act
    render(<McpConnect />);
    userEvent.click(await screen.findByRole('button', { name: label === 'mcp.connect.allow' ? ALLOW : DENY }));
    await waitFor(() => expect(approveMcp).toHaveBeenCalledWith(ID, 'csrf', allow));

    // assert
    expect(connectMcp).not.toHaveBeenCalled();
    expect(navigateMcp).toHaveBeenCalledWith('fixed-consent');
  });
  it('test_McpConnect__renders_scope_titles_without_exposing_technical_scope_name__ok', async () => {
    // arrange

    // act
    render(<McpConnect />);

    // assert
    expect(await screen.findByText(t('mcp.scope.pneumatic:read'))).toBeVisible();
    expect(screen.getByText(t('mcp.scope.files:write'))).toBeVisible();
    expect(screen.queryByText('pneumatic:read')).not.toBeInTheDocument();
  });
  it('test_McpConnect__rejects_duplicate_or_malicious_request_IDs_before_fet__rejects', async () => {
    // arrange
    window.history.replaceState({}, '', '/mcp/connect?request_id=..%2Fsecret');

    // act
    render(<McpConnect />);

    // assert
    expect(await screen.findByRole('alert')).toHaveTextContent(t('mcp.error.expired'));
    expect(getMcpConsent).not.toHaveBeenCalled();
  });
  it('test_McpConnect__treats_untrusted_app_names_as_text__ok', async () => {
    // arrange
    (getMcpConsent as jest.Mock).mockResolvedValue(makeConsent({ client_name: '<script>secret()</script>' }));

    // act
    const { container } = render(<McpConnect />);
    await screen.findByRole('button', { name: CONTINUE });

    // assert
    expect(container).toHaveTextContent('<script>secret()</script>');
    expect(container.querySelector('script')).toBeNull();
  });
  it.each([401, 403, 410])('test_McpConnect__hides_connect_actions_for_core_status_%s__rejects', async (status) => {
    // arrange
    (getMcpConsent as jest.Mock).mockRejectedValue(new McpApiError(status));

    // act
    render(<McpConnect />);
    await screen.findByRole('alert');

    // assert
    expect(screen.queryByRole('button', { name: CONTINUE })).not.toBeInTheDocument();
  });
  it('запрашивает подтверждение перед отключением приложения', async () => {
    // arrange

    // act
    render(<McpConnections />);
    userEvent.click(await screen.findByRole('button', { name: DISCONNECT }));

    // assert
    expect(revokeMcpConnection).not.toHaveBeenCalled();
    expect(screen.getByRole('button', { name: CONFIRM })).toBeEnabled();
  });
  it('отключает приложение после явного подтверждения', async () => {
    // arrange
    render(<McpConnections />);
    userEvent.click(await screen.findByRole('button', { name: DISCONNECT }));
    (getMcpConnections as jest.Mock).mockResolvedValue({
      results: [makeConnection({ revoked_at: '2026-10-09T00:00:00Z' })],
      csrf_token: 'csrf',
    });

    // act
    userEvent.click(screen.getByRole('button', { name: CONFIRM }));
    await waitFor(() => expect(revokeMcpConnection).toHaveBeenCalledWith(ID, 'csrf'));

    // assert
    expect(await screen.findByRole('status')).toHaveTextContent(t('mcp.connections.revoked'));
  });
  it.each([401, 403, 410])('убирает устаревшие подключения после потери разрешения (%s)', async (status) => {
    // arrange
    (revokeMcpConnection as jest.Mock).mockRejectedValueOnce(new McpApiError(status));
    render(<McpConnections />);
    userEvent.click(await screen.findByRole('button', { name: DISCONNECT }));

    // act
    userEvent.click(screen.getByRole('button', { name: CONFIRM }));
    await screen.findByRole('alert');

    // assert
    expect(screen.queryByRole('button', { name: CONFIRM })).not.toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Assistant' })).not.toBeInTheDocument();
  });
  it('сохраняет подключения для повторного действия после временной ошибки', async () => {
    // arrange
    (revokeMcpConnection as jest.Mock).mockRejectedValueOnce(new McpApiError(503));
    render(<McpConnections />);
    userEvent.click(await screen.findByRole('button', { name: DISCONNECT }));

    // act
    userEvent.click(screen.getByRole('button', { name: CONFIRM }));
    await screen.findByRole('alert');

    // assert
    expect(screen.getByRole('heading', { name: 'Assistant' })).toBeVisible();
    expect(screen.getByRole('button', { name: CONFIRM })).toBeEnabled();
  });
  it('не запускает вторую сверку статуса до завершения первой', async () => {
    // arrange
    const refresh = deferred<{ session: ReturnType<typeof makeSession>; csrf_token: string }>();
    (getMcpUploadSession as jest.Mock)
      .mockResolvedValueOnce({ session: makeSession({ status: 'importing' }), csrf_token: 'csrf' })
      .mockReturnValueOnce(refresh.promise);
    render(<McpUpload {...makeUploadProps()} />);
    const button = await screen.findByRole('button', { name: REFRESH });

    // act
    userEvent.click(button);
    userEvent.click(button);
    const callsDuringRefresh = (getMcpUploadSession as jest.Mock).mock.calls.length;
    await act(async () => {
      refresh.resolve({ session: makeSession({ status: 'ready' }), csrf_token: 'csrf' });
    });

    // assert
    expect(callsDuringRefresh).toBe(2);
    expect(screen.getByRole('status')).toHaveTextContent(COMPLETE);
  });
  it('не перенаправляет пользователя после ухода со страницы согласия', async () => {
    // arrange
    const continuation = deferred<{ redirect_url: string }>();
    (connectMcp as jest.Mock).mockReturnValueOnce(continuation.promise);
    const { unmount } = render(<McpConnect />);
    userEvent.click(await screen.findByRole('button', { name: CONTINUE }));

    // act
    unmount();
    await act(async () => {
      continuation.resolve({ redirect_url: 'stale-login' });
    });

    // assert
    expect(navigateMcp).not.toHaveBeenCalled();
  });
  it('сбрасывает выбранный файл при смене сессии и игнорирует старую загрузку', async () => {
    // arrange
    const nextId = '650e8400-e29b-41d4-a716-446655440000';
    const upload = deferred<void>();
    (uploadMcpFile as jest.Mock).mockImplementationOnce((_file, _session, _csrf, _signal, onDispatch) => {
      onDispatch();
      return upload.promise;
    });
    const { rerender } = render(<McpUpload {...makeUploadProps()} />);
    await screen.findByLabelText(FILE);
    chooseFile();
    userEvent.click(screen.getByRole('button', { name: UPLOAD }));
    await waitFor(() => expect(uploadMcpFile).toHaveBeenCalledTimes(1));
    (getMcpUploadSession as jest.Mock).mockResolvedValue({ session: makeSession({ id: nextId }), csrf_token: 'csrf' });

    // act
    rerender(<McpUpload {...makeUploadProps(nextId)} />);
    await screen.findByLabelText(FILE);
    await act(async () => upload.resolve(undefined));

    // assert
    expect(screen.getByRole('button', { name: UPLOAD })).toBeDisabled();
    expect(getMcpUploadSession).toHaveBeenCalledTimes(2);
    expect(getMcpUploadSession).toHaveBeenLastCalledWith(nextId, expect.any(AbortSignal));
    expect(uploadMcpFile).toHaveBeenCalledTimes(1);
  });
  it('отклоняет пустой файл до отправки байтов', async () => {
    // arrange
    render(<McpUpload {...makeUploadProps()} />);
    await screen.findByLabelText(FILE);
    chooseFile(new File([], 'report.pdf', { type: 'application/pdf' }));

    // act
    userEvent.click(screen.getByRole('button', { name: UPLOAD }));

    // assert
    expect(await screen.findByRole('alert')).toHaveTextContent(t('mcp.upload.invalid-file'));
    expect(uploadMcpFile).not.toHaveBeenCalled();
  });
  it('очищает ошибку валидации после повторного выбора файла', async () => {
    // arrange
    render(<McpUpload {...makeUploadProps()} />);
    await screen.findByLabelText(FILE);
    chooseFile(new File(['wrong-size'], 'report.pdf', { type: 'application/pdf' }));
    userEvent.click(screen.getByRole('button', { name: UPLOAD }));
    await screen.findByRole('alert');

    // act
    chooseFile();

    // assert
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: UPLOAD })).toBeEnabled();
  });
  it.each([false, undefined])(
    'test_McpConnectionsLink__hides_the_settings_link_when_enabled_%s__rejects',
    (enabled) => {
      // arrange
      (isMcpEnabled as jest.Mock).mockReturnValue(enabled);

      // act
      render(<McpConnectionsLink />);

      // assert
      expect(screen.queryByRole('link')).not.toBeInTheDocument();
    },
  );
  it('test_McpConnectionsLink__exposes_connected_apps_from_settings_when_enabled__ok', () => {
    // arrange
    (isMcpEnabled as jest.Mock).mockReturnValue(true);

    // act
    render(<McpConnectionsLink />);

    // assert
    expect(screen.getByRole('link', { name: t('mcp.connections.title') })).toHaveAttribute('href', '/mcp/connections');
  });
  it('test_McpUpload__rejects_a_malicious_upload_session_ID_before_fetching__rejects', async () => {
    // arrange

    // act
    render(<McpUpload {...makeUploadProps('../secret')} />);

    // assert
    expect(await screen.findByRole('alert')).toHaveTextContent(t('mcp.error.expired'));
    expect(getMcpUploadSession).not.toHaveBeenCalled();
  });
  it.each([401, 403, 404, 410])(
    'test_McpUpload__hides_file_input_for_an_expired_revoked_foreign_sessio__rejects',
    async (status) => {
      // arrange
      (getMcpUploadSession as jest.Mock).mockRejectedValue(new McpApiError(status));

      // act
      render(<McpUpload {...makeUploadProps()} />);
      await screen.findByRole('alert');

      // assert
      expect(screen.queryByLabelText(FILE)).not.toBeInTheDocument();
      expect(uploadMcpFile).not.toHaveBeenCalled();
    },
  );
  it.each([1, 4])('test_McpUpload__rejects_a_file_whose_bytes_differ_from_the_requested_s__rejects', async (size) => {
    // arrange
    (getMcpUploadSession as jest.Mock).mockResolvedValue({ session: makeSession({ size }), csrf_token: 'csrf' });

    // act
    render(<McpUpload {...makeUploadProps()} />);
    await screen.findByLabelText(FILE);
    chooseFile();
    userEvent.click(screen.getByRole('button', { name: UPLOAD }));

    // assert
    expect(await screen.findByRole('alert')).toHaveTextContent(t('mcp.upload.invalid-file'));
    expect(uploadMcpFile).not.toHaveBeenCalled();
  });
  it('test_McpUpload__rejects_a_file_with_the_wrong_content_type__rejects', async () => {
    // arrange

    // act
    render(<McpUpload {...makeUploadProps()} />);
    await screen.findByLabelText(FILE);
    chooseFile(new File(['txt'], 'report.pdf', { type: 'text/plain' }));
    userEvent.click(screen.getByRole('button', { name: UPLOAD }));

    // assert
    expect(await screen.findByRole('alert')).toHaveTextContent(t('mcp.upload.invalid-file'));
    expect(uploadMcpFile).not.toHaveBeenCalled();
  });
  it.each(['', 'application/x-unknown-format', 'text/html', 'image/svg+xml'])(
    'test_McpUpload__uploads_binary_session_files_after_canonicalizing_browser_M__ok',
    async (type) => {
      // arrange
      (getMcpUploadSession as jest.Mock).mockResolvedValue({
        session: makeSession({ content_type: 'application/octet-stream' }),
        csrf_token: 'csrf',
      });

      // act
      render(<McpUpload {...makeUploadProps()} />);

      // assert
      expect(await screen.findByLabelText(FILE)).not.toHaveAttribute('accept');
      chooseFile(new File(['bin'], 'report.pdf', { type }));
      userEvent.click(screen.getByRole('button', { name: UPLOAD }));
      await screen.findByRole('button', { name: REFRESH });
      expect(uploadMcpFile).toHaveBeenCalledTimes(1);
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    },
  );
  it('test_McpUpload__uploads_a_permitted_MIME_after_trimming_parameters_and_whit__ok', async () => {
    // arrange

    // act
    render(<McpUpload {...makeUploadProps()} />);
    await screen.findByLabelText(FILE);
    chooseFile(new File(['pdf'], 'report.pdf', { type: ' Application/PDF ; charset=utf-8' }));
    userEvent.click(screen.getByRole('button', { name: UPLOAD }));
    await screen.findByRole('button', { name: REFRESH });

    // assert
    expect(uploadMcpFile).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });
  it('test_McpUpload__does_not_call_an_arbitrary_file_ID_a_completed_upload__rejects', async () => {
    // arrange
    (uploadMcpFile as jest.Mock).mockImplementationOnce(async (_file, _session, _csrf, _signal, onDispatch) => {
      onDispatch();
      return { file_id: 'untrusted' };
    });

    // act
    render(<McpUpload {...makeUploadProps()} />);
    await screen.findByLabelText(FILE);
    chooseFile();
    userEvent.click(screen.getByRole('button', { name: UPLOAD }));

    // assert
    expect(await screen.findByRole('button', { name: REFRESH })).toBeVisible();
    expect(screen.queryByText(COMPLETE)).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: UPLOAD })).not.toBeInTheDocument();
  });
  it.each([503, 400])(
    'test_McpUpload__allows_retry_when_token_or_preflight_status_%s_fails_before__ok',
    async (status) => {
      // arrange
      (uploadMcpFile as jest.Mock).mockRejectedValueOnce(new McpApiError(status));

      // act
      render(<McpUpload {...makeUploadProps()} />);
      await screen.findByLabelText(FILE);
      chooseFile();
      userEvent.click(screen.getByRole('button', { name: UPLOAD }));
      await screen.findByRole('alert');

      // assert
      expect(screen.getByRole('button', { name: UPLOAD })).toBeEnabled();
      expect(screen.queryByRole('button', { name: REFRESH })).not.toBeInTheDocument();
      userEvent.click(screen.getByRole('button', { name: UPLOAD }));
      await screen.findByRole('button', { name: REFRESH });
      expect(uploadMcpFile).toHaveBeenCalledTimes(2);
    },
  );
  it('test_McpUpload__reconciles_a_failure_after_byte_dispatch_without_allowing_u__ok', async () => {
    // arrange
    (uploadMcpFile as jest.Mock).mockImplementationOnce(async (_file, _session, _csrf, _signal, onDispatch) => {
      onDispatch();
      throw new McpApiError(503);
    });

    // act
    render(<McpUpload {...makeUploadProps()} />);
    await screen.findByLabelText(FILE);
    chooseFile();
    userEvent.click(screen.getByRole('button', { name: UPLOAD }));
    await screen.findByRole('alert');
    userEvent.click(screen.getByRole('button', { name: REFRESH }));
    await waitFor(() => expect(getMcpUploadSession).toHaveBeenCalledTimes(2));

    // assert
    expect(screen.queryByRole('button', { name: UPLOAD })).not.toBeInTheDocument();
    expect(uploadMcpFile).toHaveBeenCalledTimes(1);
  });
  it('test_McpUpload__shows_an_attached_file_after_its_upload_deadline_has_passed__ok', async () => {
    // arrange
    (getMcpUploadSession as jest.Mock).mockResolvedValue({
      session: makeSession({ status: 'attached', expires_at: '2000-01-01T00:00:00Z' }),
      csrf_token: 'csrf',
    });

    // act
    render(<McpUpload {...makeUploadProps()} />);

    // assert
    expect(await screen.findByText(COMPLETE)).toHaveAttribute('role', 'status');
    expect(screen.queryByLabelText(FILE)).not.toBeInTheDocument();
  });
  it('test_McpUpload__shows_success_only_after_core_reports_storage_verified_read__ok', async () => {
    // arrange

    // act
    render(<McpUpload {...makeUploadProps()} />);
    await screen.findByLabelText(FILE);
    chooseFile();
    (getMcpUploadSession as jest.Mock).mockResolvedValue({
      session: makeSession({ status: 'ready' }),
      csrf_token: 'csrf',
    });
    userEvent.click(screen.getByRole('button', { name: UPLOAD }));
    await screen.findByText(COMPLETE);

    // assert
    expect(screen.getByRole('status')).toHaveTextContent(COMPLETE);
  });
  it('test_McpUpload__removes_the_session_when_revocation_is_discovered_afte__rejects', async () => {
    // arrange

    // act
    render(<McpUpload {...makeUploadProps()} />);
    await screen.findByLabelText(FILE);
    chooseFile();
    (getMcpUploadSession as jest.Mock).mockRejectedValue(new McpApiError(410));
    userEvent.click(screen.getByRole('button', { name: UPLOAD }));

    // assert
    expect(await screen.findByRole('alert')).toHaveTextContent(t('mcp.error.expired'));
    expect(screen.queryByText(COMPLETE)).not.toBeInTheDocument();
  });

  it('test_McpUpload__transient_read_failure__keeps_reconciliation', async () => {
    // arrange
    const file = new File(['pdf'], 'report.pdf', { type: 'application/pdf' });
    render(<McpUpload {...makeUploadProps()} />);
    await screen.findByLabelText(FILE);
    chooseFile(file);
    (getMcpUploadSession as jest.Mock).mockRejectedValueOnce(new McpApiError(503));

    // act
    userEvent.click(screen.getByRole('button', { name: UPLOAD }));
    await screen.findByRole('alert');

    // assert
    expect(screen.getByRole('button', { name: REFRESH })).toBeEnabled();
    expect(screen.queryByRole('button', { name: UPLOAD })).not.toBeInTheDocument();
    expect(uploadMcpFile).toHaveBeenCalledTimes(1);
    expect(uploadMcpFile).toHaveBeenCalledWith(
      file,
      makeSession(),
      'csrf',
      expect.any(AbortSignal),
      expect.any(Function),
    );
    expect(getMcpUploadSession).toHaveBeenCalledTimes(2);
    expect(getMcpUploadSession).toHaveBeenNthCalledWith(1, ID, expect.any(AbortSignal));
    expect(getMcpUploadSession).toHaveBeenNthCalledWith(2, ID, expect.any(AbortSignal));
  });

  it('test_McpUpload__read_recovers__shows_verified_completion', async () => {
    // arrange
    const file = new File(['pdf'], 'report.pdf', { type: 'application/pdf' });
    render(<McpUpload {...makeUploadProps()} />);
    await screen.findByLabelText(FILE);
    chooseFile(file);
    (getMcpUploadSession as jest.Mock)
      .mockRejectedValueOnce(new McpApiError(503))
      .mockResolvedValueOnce({ session: makeSession({ status: 'ready' }), csrf_token: 'csrf' });
    userEvent.click(screen.getByRole('button', { name: UPLOAD }));
    await screen.findByRole('alert');

    // act
    userEvent.click(screen.getByRole('button', { name: REFRESH }));
    await screen.findByText(COMPLETE);

    // assert
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: UPLOAD })).not.toBeInTheDocument();
    expect(uploadMcpFile).toHaveBeenCalledTimes(1);
    expect(uploadMcpFile).toHaveBeenCalledWith(
      file,
      makeSession(),
      'csrf',
      expect.any(AbortSignal),
      expect.any(Function),
    );
    expect(getMcpUploadSession).toHaveBeenCalledTimes(3);
    expect(getMcpUploadSession).toHaveBeenNthCalledWith(1, ID, expect.any(AbortSignal));
    expect(getMcpUploadSession).toHaveBeenNthCalledWith(2, ID, expect.any(AbortSignal));
    expect(getMcpUploadSession).toHaveBeenNthCalledWith(3, ID, expect.any(AbortSignal));
  });

  it.each([401, 403, 410])('test_McpConnect__submit_status_%s__hides_actions', async (status) => {
    // arrange
    (connectMcp as jest.Mock).mockRejectedValueOnce(new McpApiError(status));
    render(<McpConnect />);
    await screen.findByRole('button', { name: CONTINUE });

    // act
    userEvent.click(screen.getByRole('button', { name: CONTINUE }));
    await screen.findByRole('alert');

    // assert
    expect(screen.queryByRole('button', { name: CONTINUE })).not.toBeInTheDocument();
    expect(getMcpConsent).toHaveBeenCalledTimes(1);
    expect(getMcpConsent).toHaveBeenCalledWith(ID, expect.any(AbortSignal));
    expect(connectMcp).toHaveBeenCalledTimes(1);
    expect(connectMcp).toHaveBeenCalledWith(ID, 'csrf');
    expect(approveMcp).not.toHaveBeenCalled();
    expect(navigateMcp).not.toHaveBeenCalled();
  });
});
