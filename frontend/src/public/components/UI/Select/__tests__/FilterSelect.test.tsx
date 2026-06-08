/// <reference types="jest" />

type TTestOption = {
  id: number;
  displayName: string;
  type: string;
};

const getSelectionKey = (option: TTestOption) => `${option.type}-${option.id}`;

describe('FilterSelect selection key logic', () => {
  it('does not treat user and group with the same id as the same selected option', () => {
    const selectedOptions = ['user-5'];
    const groupOption: TTestOption = { id: 5, displayName: 'Group Five', type: 'group' };

    expect(selectedOptions.includes(getSelectionKey(groupOption))).toBe(false);
  });

  it('adds group selection without removing user selection when ids collide', () => {
    const selectedOptions = ['user-5'];
    const groupOption: TTestOption = { id: 5, displayName: 'Group Five', type: 'group' };
    const selectionKey = getSelectionKey(groupOption);

    const newSelectedOptions = [...selectedOptions, selectionKey];

    expect(newSelectedOptions).toEqual(['user-5', 'group-5']);
  });
});
