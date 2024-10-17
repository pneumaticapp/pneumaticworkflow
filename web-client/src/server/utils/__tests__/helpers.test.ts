import { get, set } from '../helpers';
import { isArrayWithItems } from '../../../public/utils/helpers';

describe('helpers', () => {
  describe('get', () => {
    it('возвращает значение из объекта по переданному ключу', () => {
      const nestedObject = { 1: { 2: { 3: 4 } } };

      const result = get(nestedObject, '1.2.3');

      expect(result).toEqual(4);
    });
    it('возвращает fallback если в объекте нет переданного ключа', () => {
      const nestedObject = { 1: { 2: { 3: 4 } } };

      const result = get(nestedObject, '1.2.4', '');

      expect(result).toEqual('');
    });
  });
  describe('set', () => {
    it('устанавливает значение по заданному вложенному ключу в объекте', () => {
      const nestedObject: any = { 1: {} };

      set(nestedObject, '1.2.3', { 4: 5 });

      expect(nestedObject).toEqual({ 1: { 2: { 3: { 4: 5 } } } });
    });
    it('если не передать значение ничего не устанавливает', () => {
      const nestedObject = { 1: { 2: { 3: 4 } } };

      set(nestedObject, '1.2.3');

      expect(nestedObject).toEqual({ 1: { 2: { 3: 4 } } });
    });
  });
  describe('isArrayWithItems', () => {
    it('возвращает true если передан не пустой массив', () => {
      expect(isArrayWithItems([1])).toBe(true);
    });
    it('возвращает false если передан пустой массив', () => {
      expect(isArrayWithItems([])).toBe(false);
    });
    it('возвращает false если переданное значение не массив', () => {
      expect(isArrayWithItems('1' as any)).toBe(false);
    });
  });
});
