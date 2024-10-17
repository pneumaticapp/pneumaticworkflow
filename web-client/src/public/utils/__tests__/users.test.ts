/* eslint-disable */
/* prettier-ignore */
import { getUserFullName } from '../users';
import { EUserStatus } from '../../types/user';

describe('users', () => {
  describe('getUserFullName', () => {
    it('выводит полное имя пользователя в формате "Имя Фамилия"', () => {
      const firstName = 'Пётр';
      const lastName = 'Петренко';

      const result = getUserFullName({ firstName, lastName });

      expect(result).toEqual('Пётр Петренко');
    });
    it('выводит полное имя пользователя в формате "Имя Фамилия (Inactive)", если status===inactive', () => {
      const firstName = 'Пётр';
      const lastName = 'Петренко';

      const result = getUserFullName({ firstName, lastName, status: EUserStatus.Inactive });

      expect(result).toEqual('Пётр Петренко (Inactive)');
    });
    it('выводит только имя, если фамилия не указана', () => {
      const firstName = 'Анонимный';
      const lastName = '';

      const result = getUserFullName({ firstName, lastName });

      expect(result).toEqual(firstName);
    });
    it('возвращает пустую строку, если ни имя, ни фамилия не указаны', () => {
      const firstName = '';
      const lastName = '';

      const result = getUserFullName({ firstName, lastName });

      expect(result).toEqual('');
    });

    it('returns email if name is empty', () => {
      const firstName = '';
      const lastName = '';
      const email = 'test@example.com';

      const result = getUserFullName({ firstName, lastName, email });

      expect(result).toEqual(email);
    });

    it('returns name with at sign', () => {
      const firstName = 'Ilya';
      const lastName = '';
      const email = 'test@example.com';

      const result = getUserFullName({ firstName, lastName, email }, { withAtSign: true });

      expect(result).toEqual('@Ilya');
    });
  });
});
