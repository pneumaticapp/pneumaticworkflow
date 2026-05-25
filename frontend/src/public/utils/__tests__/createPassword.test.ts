import { createPassword } from '../createPassword';

describe('createPassword', () => {
  describe('length', () => {
    it('returns password of default length 8', () => {
      const result = createPassword();
      expect(result).toHaveLength(8);
    });

    it('returns password of given length', () => {
      expect(createPassword(12)).toHaveLength(12);
      expect(createPassword(10)).toHaveLength(10);
    });
  });

  describe('character sets', () => {
    it('contains at least one character from each set (lowercase, uppercase, digit, special)', () => {
      const lowercase = /[a-z]/;
      const uppercase = /[A-Z]/;
      const digits = /[0-9]/;
      const special = /[!@#$%^&*]/;

      const result = createPassword();

      expect(result).toMatch(lowercase);
      expect(result).toMatch(uppercase);
      expect(result).toMatch(digits);
      expect(result).toMatch(special);
    });
  });

  describe('shuffle', () => {
    it('shuffles chosen chars so result is not fixed order aA0!aaaa', () => {
      jest.spyOn(Math, 'random').mockReturnValue(0);

      const result = createPassword(8);

      (Math.random as jest.Mock).mockRestore();

      const unshuffled = 'aA0!aaaa';
      expect(result).not.toBe(unshuffled);
    });
  });
});
