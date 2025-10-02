import { mapOAuthProfile } from '../mapOAuthProfile';

describe('mapOAuthProfile', () => {
  it('returns an empty object if no data is provided.', () => {
    expect(mapOAuthProfile()).toEqual({});
  });
  it('returns an empty object if the required data is not present in the input.', () => {
    const result = mapOAuthProfile({ email: 'test@pneumatic.app' } as any);

    expect(result).toEqual({
      email: 'test@pneumatic.app',
      firstName: '',
      lastName: '',
      companyName: '',
      phone: '',
      photo: '',
    });
  });
  it('returns formatted data.', () => {
    const data = {
      id: '1',
      email: 'example@pneumatic.com',
      first_name: 'Example',
      last_name: 'Test',
      company: 'Pneumatic',
      phone: '88005553535',
      photo: '/api/photo.jpg',
    };
    const result = mapOAuthProfile(data);

    expect(result).toEqual({
      email: 'example@pneumatic.com',
      firstName: 'Example',
      lastName: 'Test',
      companyName: 'Pneumatic',
      phone: '88005553535',
      photo: '/api/photo.jpg',
    });
  });
});
