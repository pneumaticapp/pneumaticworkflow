/* eslint-disable */
/* prettier-ignore */
import { getUserFullName } from '../users';
import { EUserStatus } from '../../types/user';

describe('users', () => {
  describe('getUserFullName', () => {
    it('displays the full name of the user in the format “First Last”', () => {
      const firstName = 'John';
      const lastName = 'Lanister';

      const result = getUserFullName({ firstName, lastName });

      expect(result).toEqual('John Lanister');
    });
    it('displays the full name of the user in the format “First Last (Inactive)” if status === inactive', () => {
      const firstName = 'John';
      const lastName = 'Lanister';

      const result = getUserFullName({ firstName, lastName, status: EUserStatus.Inactive });

      expect(result).toEqual('John Lanister (Inactive)');
    });
    it('displays only the first name if the last name is not provided', () => {
      const firstName = 'Anonymous';
      const lastName = '';

      const result = getUserFullName({ firstName, lastName });

      expect(result).toEqual(firstName);
    });
    it('returns an empty string if neither the first name nor the last name is provided', () => {
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
