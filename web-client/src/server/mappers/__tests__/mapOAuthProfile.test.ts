import { mapGooglePeopleResponse } from '../mapGooglePeopleResponse';

describe('mapGooglePeopleResponse', () => {
  it('returns an empty object if no data is provided.', () => {
    expect(mapGooglePeopleResponse()).toEqual({});
  });
  it('returns an empty object if the required data is not present in the input.', () => {
    const data = { etag: 'etag' };
    const result = mapGooglePeopleResponse(data);

    expect(result).toEqual({
      email: '',
      firstName: '',
      lastName: '',
      companyName: '',
      phone: '',
      photo: '',
    });
  });
  it('returns formatted data.', () => {
    const data = {
      emailAddresses: [{ value: 'example@pneumatic.com' }],
      names: [{ givenName: 'Example', familyName: 'Test' }],
      organizations: [{ name: 'Pneumatic' }],
      photos: [{ url: '/google/photo.jpg' }],
    };
    const result = mapGooglePeopleResponse(data);

    expect(result).toEqual({
      email: 'example@pneumatic.com',
      firstName: 'Example',
      lastName: 'Test',
      companyName: 'Pneumatic',
      phone: '',
      photo: '/google/photo.jpg',
    });
  });
});
