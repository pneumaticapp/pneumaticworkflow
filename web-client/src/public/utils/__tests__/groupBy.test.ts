/* eslint-disable */
/* prettier-ignore */
import { groupBy } from '../groupBy';

describe('groupBy', () => {
  it('groups the array by the passed value', () => {
    const data = [
      {name: 'foo', score: 100},
      {name: 'bar', score: 99},
      {name: 'baz', score: 111},
      {name: 'bar', score: 100},
      {name: 'foo', score: 102},
    ];

    const result = groupBy(data, 'name');

    expect(result).toEqual({
      foo: [
        {name: 'foo', score: 100},
        {name: 'foo', score: 102},
      ],
      bar: [
        {name: 'bar', score: 99},
        {name: 'bar', score: 100},
      ],
      baz: [
        {name: 'baz', score: 111},
      ],
    });
  });
});
