/* eslint-disable */
/* prettier-ignore */
import { getPluralNoun, TGetPluralNounParams } from '../helpers';

describe('getPluralNoun', () => {
  const cases: [TGetPluralNounParams, string][] = [
    [
      { counter: 5, single: 'user', plural: 'users' },
      'users',
    ],
    [
      { counter: 1, single: 'user', plural: 'users' },
      'user',
    ],
    [
      { counter: 1, single: 'user', plural: 'users', includeCounter: true },
      '1 user',
    ],
    [
      { counter: 5, single: 'user', plural: 'users', includeCounter: true },
      '5 users',
    ],
  ];

  test.each(cases)('%p -> %s', (params, expected) => {
    expect(getPluralNoun(params)).toBe(expected);
  });
});
