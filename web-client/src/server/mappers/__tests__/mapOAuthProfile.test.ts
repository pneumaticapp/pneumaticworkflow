import { mapGooglePeopleResponse } from '../mapGooglePeopleResponse';

describe('mapGooglePeopleResponse', () => {
  it('возвращает пустой объект, есии не переданы данные', () => {
    expect(mapGooglePeopleResponse()).toEqual({});
  });
  it('возвращает пустой объект, есии в данных нет нужных', () => {
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
  it('возвращает отформатированные данные', () => {
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
