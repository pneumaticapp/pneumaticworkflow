// <reference types="jest" />
import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { OutputFieldContent } from '../OutputFieldContent';
import { IOutputFieldContentProps } from '../types';
import { intlMock } from '../../../../../../__stubs__/intlMock';
import { getEmptySelection } from '../../../../KickoffRedux/utils/getEmptySelection';

jest.mock('react-responsive', () => ({
  useMediaQuery: () => false,
}));

jest.mock('../TruncatedTooltip', () => ({
  TruncatedTooltip: jest.fn(({ children }: any) => children),
}));

jest.mock('../../../../KickoffRedux/utils/getEmptySelection', () => ({
  getEmptySelection: jest.fn(() => ({ id: 'empty', value: '', isSelected: false })),
}));

describe('OutputFieldContent', () => {
  const mockEditField = jest.fn();
  const formatMsg = (id: string) => intlMock.formatMessage({ id });

  const CLEAR_LABEL = formatMsg('template.field-dataset-clear');

  const customField = {
    dataset: null,
    selections: [{ id: 's1', value: 'opt1', isSelected: true, apiName: 'opt1' }],
  };

  const datasetField = {
    dataset: 5,
    selections: undefined,
  };

  const baseProps: IOutputFieldContentProps = {
    field: customField as any,
    editField: mockEditField,
    isDisabled: false,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('shows children when dataset is not set', () => {
    const childText = 'Custom Options Here';
    render(React.createElement(OutputFieldContent, baseProps,
      React.createElement('div', { 'data-testid': 'children' }, childText),
    ));

    expect(screen.getByTestId('children')).toBeInTheDocument();
    expect(screen.getByTestId('children')).toHaveTextContent(childText);
  });

  it('shows dataset name when dataset is set', () => {
    render(React.createElement(OutputFieldContent, {
      ...baseProps,
      field: datasetField as any,
      datasetName: 'My Dataset',
    }));

    expect(screen.queryByTestId('children')).not.toBeInTheDocument();
    expect(screen.getByText('My Dataset')).toBeInTheDocument();
  });

  it('calls editField with saved selections on Clear button click', () => {
    const { rerender } = render(React.createElement(OutputFieldContent, baseProps));

    rerender(React.createElement(OutputFieldContent, {
      ...baseProps,
      field: datasetField as any,
      datasetName: 'My Dataset',
    }));

    userEvent.click(screen.getByText(CLEAR_LABEL));

    expect(mockEditField).toHaveBeenCalledTimes(1);
    expect(mockEditField).toHaveBeenCalledWith({
      dataset: null,
      selections: [{ id: 's1', value: 'opt1', isSelected: true, apiName: 'opt1' }],
    });
  });

  it('does not show Clear button when isDisabled=true', () => {
    render(React.createElement(OutputFieldContent, {
      ...baseProps,
      field: datasetField as any,
      datasetName: 'My Dataset',
      isDisabled: true,
    }));

    expect(screen.queryByText(CLEAR_LABEL)).not.toBeInTheDocument();
  });

  it('calls editField with empty selection when no selections were saved', () => {
    render(React.createElement(OutputFieldContent, {
      ...baseProps,
      field: datasetField as any,
      datasetName: 'My Dataset',
    }));

    userEvent.click(screen.getByText(CLEAR_LABEL));

    expect(mockEditField).toHaveBeenCalledWith({
      dataset: null,
      selections: [getEmptySelection()],
    });
  });
});
