import { mapGoogleUserList } from '../mapGoogleUserList';

describe('mapGoogleUserList', () => {
  it('возвращает пустой массив, если не передать данные', () => {
    expect(mapGoogleUserList()).toEqual([]);
  });
  it('возвращает пустой массив, если не передать объект со списком пользователей', () => {
    expect(mapGoogleUserList({})).toEqual([]);
  });
  it('возвращает данные из списка профилей в домене гугла', () => {
    const users = [
      {
        name: {
          familyName: 'Test',
          givenName: 'User',
        },
        thumbnailPhotoUrl: '/google/photo.jpg',
        primaryEmail: 'test@pneumatic.app',
        phones: ['88005553535'],
      },
      {
        primaryEmail: 'test2@pneumatic.app',
      },
    ];
    const result = mapGoogleUserList({ users });

    expect(result).toEqual([
      {
        avatar: '/google/photo.jpg',
        email: 'test@pneumatic.app',
        firstName: 'User',
        lastName: 'Test',
        phone: '88005553535',
      },
      {
        avatar: '',
        email: 'test2@pneumatic.app',
        firstName: '',
        lastName: '',
        phone: '',
      },
    ]);
  });
});
