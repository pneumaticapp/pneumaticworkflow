import { mapOAuthProfile } from '../mapOAuthProfile';

describe('mapOAuthProfile', () => {
  it('возвращает пустой объект, есии не переданы данные', () => {
    expect(mapOAuthProfile()).toEqual({});
  });
  it('возвращает пустой объект, есии в данных нет нужных', () => {
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
  it('возвращает отформатированные данные', () => {
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
