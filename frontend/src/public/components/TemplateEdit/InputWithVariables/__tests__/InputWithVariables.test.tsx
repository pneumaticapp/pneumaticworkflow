// <reference types="jest" />
import * as React from 'react';
import { render } from '@testing-library/react';

import { InputWithVariables } from '../InputWithVariables';
import { VariableList } from '../../VariableList';

jest.mock('../../VariableList', () => ({
  VariableList: jest.fn(() => React.createElement('div', { 'data-testid': 'variable-list' })),
}));

jest.mock('../../../RichEditor', () => ({
  RichEditor: React.forwardRef(
    ({ children }: { children?: React.ReactNode }, _ref: React.Ref<unknown>) =>
      React.createElement('div', { 'data-testid': 'rich-editor' }, children),
  ),
}));

jest.mock('../../../../utils/escapeMarkdown', () => ({
  escapeMarkdown: (v: string | undefined) => v ?? '',
}));

describe('InputWithVariables', () => {
  const baseProps = {
    listVariables: [],
    templateVariables: [],
    value: '',
    toolipText: 'tooltip',
    onChange: jest.fn(() => Promise.resolve('')),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders VariableList when showInsertButton=true', () => {
    render(React.createElement(InputWithVariables, { ...baseProps, showInsertButton: true }));

    expect(VariableList as jest.Mock).toHaveBeenCalledTimes(1);
  });

  it('does not render VariableList when showInsertButton=false', () => {
    render(React.createElement(InputWithVariables, { ...baseProps, showInsertButton: false }));

    expect(VariableList as jest.Mock).toHaveBeenCalledTimes(0);
  });

  it('does not render VariableList when showInsertButton=undefined', () => {
    render(
      React.createElement(InputWithVariables, {
        ...baseProps,
        showInsertButton: undefined as unknown as boolean,
      }),
    );

    expect(VariableList as jest.Mock).toHaveBeenCalledTimes(0);
  });
});
