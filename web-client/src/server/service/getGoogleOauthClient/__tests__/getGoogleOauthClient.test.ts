import { google } from 'googleapis';
import { getGoogleOauthClient } from '../getGoogleOauthClient';
import { getConfig } from '../../../../public/utils/getConfig';

const oAuth = {getToken: jest.fn()};

jest.mock('../../../../public/utils/getConfig');
jest.mock('googleapis', () => ({
  google: {
    auth: {
      OAuth2: jest.fn().mockImplementation(() => oAuth),
    },
  },
}));

describe('getGoogleOauthClient', () => {
  it('возвращает данные для авторизации через гугл', () => {
    const clientId = 'mock-client-id';
    const clientSecret = 'mock-client-secret';
    (getConfig as jest.Mock).mockReturnValueOnce({
      host: 'http://localhost:8080',
      google: {
        clientId,
        clientSecret,
      },
    });

    const result = getGoogleOauthClient();

    expect(google.auth.OAuth2).toHaveBeenCalledWith(
      clientId,
      clientSecret,
      'http://localhost:8080/oauth/google/',
    );
    expect(result).toEqual(oAuth);
  });
});
