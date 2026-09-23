import { MouseEvent } from 'react';
import { IntlShape } from 'react-intl';
import { handleOAuthClick } from '../handleOAuthClick';
import { getOAuthUrl } from '../../../../api/getGoogleAuthUrl';
import { NotificationManager } from '../../../../components/UI/Notifications';
import { EOAuthType } from '../../../../types/auth';

jest.mock('../../../../api/getGoogleAuthUrl', () => ({
  getOAuthUrl: jest.fn(),
}));

jest.mock('../../../../components/UI/Notifications', () => ({
  NotificationManager: {
    warning: jest.fn(),
  },
}));

type FormatMessageFn = IntlShape['formatMessage'];

describe('handleOAuthClick', () => {
  const originalLocation = window.location;
  const mockFormatMessageFn = jest.fn(
    ({ id }: { id: string }, values?: Record<string, string>) => `translated:${id}:${values?.type}`,
  );
  const mockFormatMessage = mockFormatMessageFn as FormatMessageFn;
  const createMockEvent = (): MouseEvent =>
    ({
      preventDefault: jest.fn(),
    }) as unknown as MouseEvent;

  beforeEach(() => {
    jest.clearAllMocks();
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: {
        ...originalLocation,
        assign: jest.fn(),
      },
    });
  });

  afterAll(() => {
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: originalLocation,
    });
  });

  it('calls preventDefault on the event', async () => {
    (getOAuthUrl as jest.Mock).mockResolvedValue({ redirectUri: 'https://oauth.example.com' });
    const mockEvent = createMockEvent();

    await handleOAuthClick(EOAuthType.Google, mockFormatMessage)(mockEvent);

    expect(mockEvent.preventDefault).toHaveBeenCalledTimes(1);
  });

  it('redirects via window.location.assign when redirectUri is valid', async () => {
    const mockRedirectUri = 'https://accounts.google.com/o/oauth2/v2/auth?client_id=123';
    (getOAuthUrl as jest.Mock).mockResolvedValue({ redirectUri: mockRedirectUri });
    const mockEvent = createMockEvent();

    await handleOAuthClick(EOAuthType.Google, mockFormatMessage)(mockEvent);

    expect(getOAuthUrl).toHaveBeenCalledTimes(1);
    expect(getOAuthUrl).toHaveBeenCalledWith(EOAuthType.Google);
    expect(window.location.assign).toHaveBeenCalledTimes(1);
    expect(window.location.assign).toHaveBeenCalledWith(mockRedirectUri);
    expect(NotificationManager.warning).not.toHaveBeenCalled();
  });

  it('shows warning instead of crashing when response is an HTML string', async () => {
    const htmlResponse = '<!DOCTYPE html><html><body>Error</body></html>';
    (getOAuthUrl as jest.Mock).mockResolvedValue(htmlResponse);
    const mockEvent = createMockEvent();

    await handleOAuthClick(EOAuthType.Google, mockFormatMessage)(mockEvent);

    expect(window.location.assign).not.toHaveBeenCalled();
    expect(NotificationManager.warning).toHaveBeenCalledTimes(1);
    expect(mockFormatMessageFn).toHaveBeenCalledWith({ id: 'user.oauth-unavailable' }, { type: EOAuthType.Google });
    expect(NotificationManager.warning).toHaveBeenCalledWith({
      message: 'translated:user.oauth-unavailable:Google',
    });
  });

  it('shows warning when result is undefined (network failure)', async () => {
    (getOAuthUrl as jest.Mock).mockResolvedValue(undefined);
    const mockEvent = createMockEvent();

    await handleOAuthClick(EOAuthType.SSOAuth0, mockFormatMessage)(mockEvent);

    expect(window.location.assign).not.toHaveBeenCalled();
    expect(NotificationManager.warning).toHaveBeenCalledTimes(1);
    expect(mockFormatMessageFn).toHaveBeenCalledWith({ id: 'user.oauth-unavailable' }, { type: 'SSO' });
    expect(NotificationManager.warning).toHaveBeenCalledWith({
      message: 'translated:user.oauth-unavailable:SSO',
    });
  });

  it('shows warning when result has no redirectUri', async () => {
    (getOAuthUrl as jest.Mock).mockResolvedValue({});
    const mockEvent = createMockEvent();

    await handleOAuthClick(EOAuthType.Google, mockFormatMessage)(mockEvent);

    expect(window.location.assign).not.toHaveBeenCalled();
    expect(NotificationManager.warning).toHaveBeenCalledTimes(1);
    expect(mockFormatMessageFn).toHaveBeenCalledWith({ id: 'user.oauth-unavailable' }, { type: EOAuthType.Google });
    expect(NotificationManager.warning).toHaveBeenCalledWith({
      message: 'translated:user.oauth-unavailable:Google',
    });
  });

  it('does not call assign and shows warning when redirectUri is null', async () => {
    (getOAuthUrl as jest.Mock).mockResolvedValue({ redirectUri: null });
    const mockEvent = createMockEvent();

    await handleOAuthClick(EOAuthType.Google, mockFormatMessage)(mockEvent);

    expect(window.location.assign).not.toHaveBeenCalled();
    expect(NotificationManager.warning).toHaveBeenCalledTimes(1);
  });

  it('does not call assign and shows warning when redirectUri is empty string', async () => {
    (getOAuthUrl as jest.Mock).mockResolvedValue({ redirectUri: '' });
    const mockEvent = createMockEvent();

    await handleOAuthClick(EOAuthType.Google, mockFormatMessage)(mockEvent);

    expect(window.location.assign).not.toHaveBeenCalled();
    expect(NotificationManager.warning).toHaveBeenCalledTimes(1);
  });

  it('rejects javascript: protocol in redirectUri to prevent XSS', async () => {
    (getOAuthUrl as jest.Mock).mockResolvedValue({ redirectUri: 'javascript:alert(1)' });
    const mockEvent = createMockEvent();

    await handleOAuthClick(EOAuthType.Google, mockFormatMessage)(mockEvent);

    expect(window.location.assign).not.toHaveBeenCalled();
    expect(NotificationManager.warning).toHaveBeenCalledTimes(1);
  });
});
