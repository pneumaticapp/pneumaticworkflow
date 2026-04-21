/* eslint-disable */
/* prettier-ignore */
import { insertId } from '../insertId';

describe('insertId', () => {
  it('test 1', () => {
    const mockInit = {
      a: '123',
      b: [1, 2, 3, 4],
      c: [
        {
          apiName: 'a',
          e: 1,
          f: [
            { apiName: 'aa' },
            { apiName: 'ab' },
            { apiName: 'ac' },
          ],
        },
        {
          apiName: 'b',
          e: 2,
          f: [
            { predicateApiName: 'ba' },
            { predicateApiName: 'bb' },
            { predicateApiName: 'bc' },
          ],
        },
      ],
      d: {
        e: 123,
      },
    };

    const mockSaved = {
      id: 1,
      a: '123',
      b: [1, 2, 3, 4],
      c: [
        {
          id: 1,
          apiName: 'a',
          e: 1,
          f: [
            { id: 1, apiName: 'aa' },
            { id: 2, apiName: 'ab' },
            { id: 3, apiName: 'ac' },
          ],
        },
        {
          id: 2,
          apiName: 'b',
          e: 2,
          f: [
            { predicateId: 1, predicateApiName: 'ba' },
            { predicateId: 2, predicateApiName: 'bb' },
            { predicateId: 3, predicateApiName: 'bc' },
          ],
        },
      ],
      d: {
        id: 1,
        e: 123,
      },
    };

    expect(insertId(mockInit, mockSaved)).toEqual(mockSaved);
  });

  it('test 2', () => {
    const mockInit = {
      arr: [
        { apiName: 'a' },
        { apiName: 'b' },
        { apiName: 'c' },
      ],
    };

    const mockSaved = {
      arr: [
        { id: 1, apiName: 'b' },
        { id: 2, apiName: 'd' },
      ],
    };

    expect(insertId(mockInit, mockSaved)).toStrictEqual({
      arr: [
        { apiName: 'a' },
        { id: 1, apiName: 'b' },
        { apiName: 'c' },
      ],
    });
  });
});
