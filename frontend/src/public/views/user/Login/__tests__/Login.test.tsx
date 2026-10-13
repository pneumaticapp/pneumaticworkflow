// <reference types="jest" />
import * as React from 'react';
import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { intlMock } from '../../../../__stubs__/intlMock';
import { EOAuthType } from '../../../../types/auth';
import { REDIRECT_URL_STORAGE_KEY } from '../../../../constants/storageKeys';
import { getOAuthUrl } from '../../../../api/getGoogleAuthUrl';
import { Login } from '../Login';

jest.mock('../../../../api/getGoogleAuthUrl', () => ({ getOAuthUrl: jest.fn() }));
jest.mock('../../../../utils/getConfig', () => ({
  getBrowserConfigEnv: () => ({ api: { fileServiceUrl: 'https://my.pneumatic.app/files' } }),
}));
jest.mock('../../utils/utmParams', () => ({ saveUTMParams: jest.fn() }));
jest.mock('../../../../constants/enviroment', () => ({
  isEnvGoogleAuth: true,
  isEnvMsAuth: false,
  isEnvSSOAuth: false,
  isEnvSignup: false,
}));
jest.mock('../../../../components/IntlMessages', () => ({ IntlMessages: () => null }));
jest.mock('../../../../components/NavLink', () => ({ NavLink: () => null }));
jest.mock('../../../../components/UI', () => ({
  Header: () => null,
  InputField: () => null,
  FormikCheckbox: () => null,
  Button: ({ label, disabled }: { label: string; disabled?: boolean }) => <button disabled={disabled}>{label}</button>,
}));
jest.mock('../../../../components/OAuthButtons', () => ({
  GoogleButton: ({
    label,
    disabled,
    onClick,
  }: {
    label: string;
    disabled?: boolean;
    onClick: (event: React.MouseEvent) => void;
  }) => (
    <button disabled={disabled} onClick={onClick}>
      {label}
    </button>
  ),
  MicrosoftButton: () => null,
  SSOButton: () => null,
}));

describe('Login — продолжение MCP', () => {
  const ID = '550e8400-e29b-41d4-a716-446655440000';
  const TARGET = `/mcp/connect?request_id=${ID}`;
  const t = (id: string) => intlMock.formatMessage({ id });
  const GOOGLE = t('user.sign-up-google');
  const UNAVAILABLE = t('user.oauth-unavailable');
  const originalLocation = window.location;
  const mockLogin = jest.fn();
  const mockRedirect = jest.fn();
  const mockNavigate = jest.fn();
  const renderLogin = (query: string = '') =>
    render(
      <MemoryRouter initialEntries={[`/auth/signin${query}`]}>
        <Login loginUser={mockLogin} setRedirectUrl={mockRedirect} />
      </MemoryRouter>,
    );
  const deferred = () => {
    let resolve!: (value: { redirectUri: string }) => void;
    const promise = new Promise<{ redirectUri: string }>((complete) => {
      resolve = complete;
    });
    return { promise, resolve };
  };

  beforeEach(() => {
    jest.clearAllMocks();
    sessionStorage.clear();
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { ...originalLocation, assign: mockNavigate },
    });
  });
  afterEach(() => {
    Object.defineProperty(window, 'location', { configurable: true, value: originalLocation });
    sessionStorage.clear();
  });

  it('сохраняет безопасный MCP-адрес из параметров страницы входа', () => {
    // arrange
    const query = `?redirectUrl=${encodeURIComponent(TARGET)}`;

    // act
    renderLogin(query);

    // assert
    expect(mockRedirect).toHaveBeenCalledWith(TARGET);
  });

  it('передаёт продолжение MCP при выборе OAuth-провайдера', async () => {
    // arrange
    sessionStorage.setItem(REDIRECT_URL_STORAGE_KEY, TARGET);
    (getOAuthUrl as jest.Mock).mockResolvedValueOnce({ redirectUri: 'https://provider.test/authorize' });
    renderLogin();

    // act
    userEvent.click(screen.getByRole('button', { name: GOOGLE }));
    await waitFor(() => expect(mockNavigate).toHaveBeenCalledTimes(1));

    // assert
    expect(getOAuthUrl).toHaveBeenCalledWith(EOAuthType.Google, TARGET);
    expect(mockNavigate).toHaveBeenCalledWith('https://provider.test/authorize');
    expect(screen.getByRole('button', { name: GOOGLE })).toBeDisabled();
  });

  it('не создаёт второй OAuth-запрос при повторном нажатии', async () => {
    // arrange
    const request = deferred();
    (getOAuthUrl as jest.Mock).mockReturnValueOnce(request.promise);
    renderLogin();
    const button = screen.getByRole('button', { name: GOOGLE });

    // act
    userEvent.click(button);
    userEvent.click(button);
    await act(async () => request.resolve({ redirectUri: 'https://provider.test/authorize' }));

    // assert
    expect(getOAuthUrl).toHaveBeenCalledTimes(1);
  });

  it('игнорирует OAuth-ответ после ухода со страницы входа', async () => {
    // arrange
    const request = deferred();
    (getOAuthUrl as jest.Mock).mockReturnValueOnce(request.promise);
    const { unmount } = renderLogin();
    userEvent.click(screen.getByRole('button', { name: GOOGLE }));

    // act
    unmount();
    await act(async () => request.resolve({ redirectUri: 'https://provider.test/authorize' }));

    // assert
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('показывает безопасную ошибку OAuth и разрешает повторное нажатие', async () => {
    // arrange
    (getOAuthUrl as jest.Mock).mockRejectedValueOnce(new Error('private-provider-data'));
    renderLogin();

    // act
    userEvent.click(screen.getByRole('button', { name: GOOGLE }));

    // assert
    expect(await screen.findByRole('alert')).toHaveTextContent(UNAVAILABLE);
    expect(screen.getByRole('button', { name: GOOGLE })).toBeEnabled();
    expect(screen.queryByText('private-provider-data')).not.toBeInTheDocument();
  });
});
