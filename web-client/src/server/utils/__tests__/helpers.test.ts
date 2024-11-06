import { get, set } from '../helpers';
import { isArrayWithItems } from '../../../public/utils/helpers';

describe('helpers', () => {
  describe('get', () => {
    it('returns the value from the object by the provided key.', () => {
      const nestedObject = { 1: { 2: { 3: 4 } } };

      const result = get(nestedObject, '1.2.3');

      expect(result).toEqual(4);
    });
    it('returns the fallback if the provided key is not present in the object.', () => {
      const nestedObject = { 1: { 2: { 3: 4 } } };

      const result = get(nestedObject, '1.2.4', '');

      expect(result).toEqual('');
    });
  });
  describe('set', () => {
    it('sets the value for the specified nested key in the object.', () => {
      const nestedObject: any = { 1: {} };

      set(nestedObject, '1.2.3', { 4: 5 });

      expect(nestedObject).toEqual({ 1: { 2: { 3: { 4: 5 } } } });
    });
    it('if no value is provided, it does not set anything.', () => {
      const nestedObject = { 1: { 2: { 3: 4 } } };

      set(nestedObject, '1.2.3');

      expect(nestedObject).toEqual({ 1: { 2: { 3: 4 } } });
    });
  });
  describe('isArrayWithItems', () => {
    it('returns true if a non-empty array is provided.', () => {
      expect(isArrayWithItems([1])).toBe(true);
    });
    it('returns false if an empty array is provided.', () => {
      expect(isArrayWithItems([])).toBe(false);
    });
    it('returns false if the provided value is not an array.', () => {
      expect(isArrayWithItems('1' as any)).toBe(false);
    });
  });
});
