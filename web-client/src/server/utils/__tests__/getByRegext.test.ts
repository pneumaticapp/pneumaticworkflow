import { getByRegEx } from '../getByRegEx';

describe('getByRegex', () => {
  it('возвращает пустую строку, если не передано значение', () => {
    const result = getByRegEx(undefined, /\d+/);

    expect(result).toEqual('');
  });
  it('возвращает результат выполнения регулярного выражения на строке', () => {
    const result = getByRegEx('10h', /\d+/);

    expect(result).toEqual('10');
  });
  it('возвращает переданный фолбэк, если не удалось ничего найти', () => {
    const result = getByRegEx('10h', /^\D+/, 'fallback');

    expect(result).toEqual('fallback');
  });
});
