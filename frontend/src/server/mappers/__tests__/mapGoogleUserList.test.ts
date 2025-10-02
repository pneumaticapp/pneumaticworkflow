import { mapGoogleUserList } from '../mapGoogleUserList';

describe('mapGoogleUserList', () => {
  it('returns an empty array if no data is provided.', () => {
    expect(mapGoogleUserList()).toEqual([]);
  });
  it('returns an empty array if an object with the list of users is not provided.', () => {
    expect(mapGoogleUserList({})).toEqual([]);
  });
  it('returns data from the list of profiles in the Google domain.', () => {
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
