import { getFromArray } from '../getFromArray';

describe('getFromArray', () => {
  it('возвращает заданный ключ из 1 элемента массива', () => {
    const data = [{id: 1, name: 'Ivan'}, {id: 2, name: 'Peter'}];

    const result = getFromArray('name', data);

    expect(result).toEqual('Ivan');
  });

  it('возвращает переданный фолбэк, если в массиве нет такого элемента', () => {
    const data: {id: number; name?: string}[] = [{ id: 1 }];

    const result = getFromArray('name', data, 'Unknown');

    expect(result).toEqual('Unknown');
  });
});
