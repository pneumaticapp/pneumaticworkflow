// <reference types="jest" />
import { recalculateDuplicateErrors, handleSelectionBlur } from '../handleSelectionBlur';
import { IExtraFieldSelection } from '../../../../../types/template';

describe('recalculateDuplicateErrors', () => {
  it('returns empty object when no duplicates', () => {
    const selections: IExtraFieldSelection[] = [
      { value: 'A', apiName: 'sel-1' },
      { value: 'B', apiName: 'sel-2' },
    ];
    expect(recalculateDuplicateErrors(selections)).toEqual({});
  });

  it('returns error for the second occurrence of a case-insensitive duplicate', () => {
    const selections: IExtraFieldSelection[] = [
      { value: 'A', apiName: 'sel-1' },
      { value: 'a', apiName: 'sel-2' },
    ];
    const errors = recalculateDuplicateErrors(selections);
    expect(errors).toHaveProperty('sel-2');
    expect(errors).not.toHaveProperty('sel-1');
  });
});

describe('handleSelectionBlur', () => {
  it('calls setDuplicateErrors when a duplicate is found', () => {
    const setDuplicateErrors = jest.fn();
    const selections: IExtraFieldSelection[] = [
      { value: 'Apple', apiName: 'sel-1' },
      { value: 'Apple', apiName: 'sel-2' },
    ];

    const blurHandler = handleSelectionBlur(setDuplicateErrors, selections);
    blurHandler('sel-2')();

    expect(setDuplicateErrors).toHaveBeenCalledTimes(1);
    expect(setDuplicateErrors).toHaveBeenCalledWith(expect.any(Function));
  });
});
