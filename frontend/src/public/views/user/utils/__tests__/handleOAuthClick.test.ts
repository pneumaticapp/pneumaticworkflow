import { MouseEvent } from 'react';
import { handleOAuthClick } from '../handleOAuthClick';
import { getOAuthUrl } from '../../../../api/getGoogleAuthUrl';
import { NotificationManager } from '../../../../components/UI/Notifications';
import { EOAuthType } from '../../../../types/auth';
import { intlMock } from '../../../../__stubs__/intlMock';

jest.mock('../../../../api/getGoogleAuthUrl', () => ({
  getOAuthUrl: jest.fn(),
}));

jest.mock('../../../../components/UI/Notifications', () => ({
  NotificationManager: {
    warning: jest.fn(),
  },
}));

describe('handleOAuthClick', () => {
  const originalLocation = window.location;
  const formatUnavailableMessage = (type: EOAuthType) =>
    intlMock.formatMessage({ id: 'user.oauth-unavailable' }, { type });
  const createMockEvent = (): MouseEvent => {
    const preventDefault: MouseEvent['preventDefault'] = jest.fn();

    return { preventDefault } as MouseEvent;
  };

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

    await handleOAuthClick(EOAuthType.Google, intlMock.formatMessage)(mockEvent);

    expect(mockEvent.preventDefault).toHaveBeenCalledTimes(1);
  });

  it('redirects via window.location.assign when redirectUri is valid', async () => {
    const mockRedirectUri = 'https://accounts.google.com/o/oauth2/v2/auth?client_id=123';
    (getOAuthUrl as jest.Mock).mockResolvedValue({ redirectUri: mockRedirectUri });
    const mockEvent = createMockEvent();

    await handleOAuthClick(EOAuthType.Google, intlMock.formatMessage)(mockEvent);

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

    await handleOAuthClick(EOAuthType.Google, intlMock.formatMessage)(mockEvent);

    expect(window.location.assign).not.toHaveBeenCalled();
    expect(NotificationManager.warning).toHaveBeenCalledTimes(1);
    expect(NotificationManager.warning).toHaveBeenCalledWith({
      message: formatUnavailableMessage(EOAuthType.Google),
    });
  });

  it('shows warning when result is undefined (network failure)', async () => {
    (getOAuthUrl as jest.Mock).mockResolvedValue(undefined);
    const mockEvent = createMockEvent();

    await handleOAuthClick(EOAuthType.SSOAuth0, intlMock.formatMessage)(mockEvent);

    expect(window.location.assign).not.toHaveBeenCalled();
    expect(NotificationManager.warning).toHaveBeenCalledTimes(1);
    expect(NotificationManager.warning).toHaveBeenCalledWith({
      message: formatUnavailableMessage(EOAuthType.SSOAuth0),
    });
  });

  it('shows warning when result has no redirectUri', async () => {
    (getOAuthUrl as jest.Mock).mockResolvedValue({});
    const mockEvent = createMockEvent();

    await handleOAuthClick(EOAuthType.Google, intlMock.formatMessage)(mockEvent);

    expect(window.location.assign).not.toHaveBeenCalled();
    expect(NotificationManager.warning).toHaveBeenCalledTimes(1);
    expect(NotificationManager.warning).toHaveBeenCalledWith({
      message: formatUnavailableMessage(EOAuthType.Google),
    });
  });

  it('does not call assign and shows warning when redirectUri is null', async () => {
    (getOAuthUrl as jest.Mock).mockResolvedValue({ redirectUri: null });
    const mockEvent = createMockEvent();

    await handleOAuthClick(EOAuthType.Google, intlMock.formatMessage)(mockEvent);

    expect(window.location.assign).not.toHaveBeenCalled();
    expect(NotificationManager.warning).toHaveBeenCalledTimes(1);
  });

  it('rejects javascript: protocol in redirectUri to prevent XSS', async () => {
    (getOAuthUrl as jest.Mock).mockResolvedValue({ redirectUri: 'javascript:alert(1)' });
    const mockEvent = createMockEvent();

    await handleOAuthClick(EOAuthType.Google, intlMock.formatMessage)(mockEvent);

    expect(window.location.assign).not.toHaveBeenCalled();
    expect(NotificationManager.warning).toHaveBeenCalledTimes(1);
  });

  it('uses the provider name from enum as is for SSOOkta', async () => {
    (getOAuthUrl as jest.Mock).mockResolvedValue(undefined);
    const mockEvent = createMockEvent();

    await handleOAuthClick(EOAuthType.SSOOkta, intlMock.formatMessage)(mockEvent);

    expect(NotificationManager.warning).toHaveBeenCalledTimes(1);
    expect(NotificationManager.warning).toHaveBeenCalledWith({
      message: formatUnavailableMessage(EOAuthType.SSOOkta),
    });
  });

  it('shows warning when getOAuthUrl rejects with an error', async () => {
    (getOAuthUrl as jest.Mock).mockRejectedValue(new Error('Network error'));
    const mockEvent = createMockEvent();

    await handleOAuthClick(EOAuthType.Google, intlMock.formatMessage)(mockEvent);

    expect(window.location.assign).not.toHaveBeenCalled();
    expect(NotificationManager.warning).toHaveBeenCalledTimes(1);
    expect(NotificationManager.warning).toHaveBeenCalledWith({
      message: formatUnavailableMessage(EOAuthType.Google),
    });
  });
});
