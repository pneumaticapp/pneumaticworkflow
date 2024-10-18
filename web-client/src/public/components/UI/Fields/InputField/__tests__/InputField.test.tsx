/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import { render, fireEvent } from '@testing-library/react';

import { PageObject } from './PageObject';

import { InputField } from '../InputField';

describe('InputField', () => {
  it('Renders closing button if onClear prop is passed and click handling is correct', () => {
    const onClearMock = jest.fn();

    render(
      <InputField
        value={'value'}
        onChange={() => {}}
        onClear={onClearMock}
      />,
    );

    const clearButton = PageObject.getClearButton();
    fireEvent.click(clearButton);

    expect(clearButton).toBeInTheDocument();
    expect(onClearMock).toHaveBeenCalled();
  });
});
