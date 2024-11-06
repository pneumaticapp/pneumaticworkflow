import { EProfile, getGoogleInfo,  getProfileType, mapAuthProfiles } from '../getProfiles';
import { ERoutes } from '../../../../public/constants/routes';
import { EOAuthType } from '../../../../public/types/auth';
import { serverApi } from '../../../utils';

const getTokenUrl = (baseRoute: ERoutes, token: string = '123456') => `${baseRoute}/?token=${token}`;

describe('getProfiles', () => {
  beforeEach(() => {
    jest.resetAllMocks();
  });
  describe('getProfileType', () => {
    it('returns the type “google” if the URL contains a part of the Google link.', () => {
      const result = getProfileType(getTokenUrl(ERoutes.SignUpGoogle));

      expect(result).toEqual(EOAuthType.Google);
    });
    it('returns the type “invite” if the URL contains a part of the invitation link.', () => {
      const result = getProfileType(getTokenUrl(ERoutes.SignUpInvite));

      expect(result).toEqual(EProfile.Invite);
    });
    it('returns null in other cases.', () => {
      const result = getProfileType(ERoutes.Main);

      expect(result).toBeNull();
    });
  });
  describe('getProfileRequestCreator', () => {
    it('returns an empty object if an unexpected type is provided.', async () => {
      const result = await getGoogleInfo(EOAuthType.Google, '', jest.fn(), {});

      expect(result).toEqual({});
    });
    it('returns the result of the request to the specified endpoint.', async () => {
      jest.spyOn(serverApi, 'get').mockResolvedValueOnce({email: 'google@pneumatic.app'});
      const url = getTokenUrl(ERoutes.SignUpGoogle);

      const result = await getGoogleInfo(EOAuthType.Google, url, jest.fn(), {});

      expect(result).toEqual({email: 'google@pneumatic.app'});
    });
    it('if the ID is not found, returns an empty object.', async () => {
      jest.spyOn(serverApi, 'get').mockResolvedValueOnce({email: 'google@pneumatic.app'});
      const url = getTokenUrl(ERoutes.SignUpGoogle, '');

      const result = await getGoogleInfo(EOAuthType.Google, url, jest.fn(), {});

      expect(result).toEqual({email: 'google@pneumatic.app'});
    });
    it('if an error occurs during the request, it calls onError and returns an empty object.', async () => {
      const error = new Error('some bad things happened');
      jest.spyOn(serverApi, 'get').mockRejectedValueOnce(error);
      const onError = jest.fn();
      const url = getTokenUrl(ERoutes.SignUpGoogle);

      const result = await getGoogleInfo(EOAuthType.Google, url, onError, {});

      expect(result).toEqual({});
      expect(onError).toHaveBeenCalledWith(error);
    });
  });
  describe('mapAuthProfiles', () => {
    it('gets the current profile type and returns the necessary objects.', async () => {
      const result = await mapAuthProfiles(ERoutes.Main, jest.fn(), {});

      expect(result).toEqual({
        googleAuthUserInfo: {},
        invitedUser: {},
      });
    });
  });
});
