import { EUserStatus, TUserListItem } from '../types/user';

const lastNames = ['Boreckiy', 'Careckiy', 'Tvoreckiy', 'Skvoreckiy', ''];

export const generateUser = (id: number, data?: Partial<TUserListItem>): TUserListItem  => ({
  id,
  photo: `/img/avatar${id}.png`,
  email: `stas@boreckiy_${id}.app`,
  firstName: 'Stas',
  lastName: 'Boreckiy',
  status: EUserStatus.Active,
  phone: '88005553535',
  type: 'user',
  ...data,
});

export const mockUsers = [-1, ...new Array(10).keys()].map(index => generateUser(index + 1));

export const mockLastNameUsers = [-1, ...new Array(10).keys()].map(index =>
  generateUser(index + 1, {lastName: lastNames[index % lastNames.length]}));

export const getResponsibleUsers = (ids: number[]) => mockUsers.filter(({id}) => ids.includes(id));
