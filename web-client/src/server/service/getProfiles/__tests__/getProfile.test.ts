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
    it('возвращает тип google, если в ссылке содержится часть ссылки для гугла', () => {
      const result = getProfileType(getTokenUrl(ERoutes.SignUpGoogle));

      expect(result).toEqual(EOAuthType.Google);
    });
    it('возвращает тип invite, если в ссылке содержится часть ссылки приглашения', () => {
      const result = getProfileType(getTokenUrl(ERoutes.SignUpInvite));

      expect(result).toEqual(EProfile.Invite);
    });
    it('возвращает null в других случаях', () => {
      const result = getProfileType(ERoutes.Main);

      expect(result).toBeNull();
    });
  });
  describe('getProfileRequestCreator', () => {
    it('возвращает пустой объект, если передать не тот тип, который ожидается', async () => {
      const result = await getGoogleInfo(EOAuthType.Google, '', jest.fn(), {});

      expect(result).toEqual({});
    });
    it('возвращает результат выполнения запроса к нужной ручке', async () => {
      jest.spyOn(serverApi, 'get').mockResolvedValueOnce({email: 'google@pneumatic.app'});
      const url = getTokenUrl(ERoutes.SignUpGoogle);

      const result = await getGoogleInfo(EOAuthType.Google, url, jest.fn(), {});

      expect(result).toEqual({email: 'google@pneumatic.app'});
    });
    it('если не найден id, то возвращает пустой объект', async () => {
      jest.spyOn(serverApi, 'get').mockResolvedValueOnce({email: 'google@pneumatic.app'});
      const url = getTokenUrl(ERoutes.SignUpGoogle, '');

      const result = await getGoogleInfo(EOAuthType.Google, url, jest.fn(), {});

      expect(result).toEqual({email: 'google@pneumatic.app'});
    });
    it('если произойдёт ошибка при запросе вызывает onError и возвращает пустой объект', async () => {
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
    it('получает текущий тип профиля и возвращает нужные объекты', async () => {
      const result = await mapAuthProfiles(ERoutes.Main, jest.fn(), {});

      expect(result).toEqual({
        googleAuthUserInfo: {},
        invitedUser: {},
      });
    });
  });
});
