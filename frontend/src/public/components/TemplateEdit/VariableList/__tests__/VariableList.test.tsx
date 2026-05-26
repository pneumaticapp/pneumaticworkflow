/// <reference types="jest" />
import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { intlMock } from '../../../../__stubs__/intlMock';
import { VariableList, IVariableListProps } from '../VariableList';
import { TTaskVariable } from '../../types';
import { EExtraFieldType } from '../../../../types/template';
import {
  WORKFLOW_STARTER_VARIABLE_API_NAME,
  WORKFLOW_STARTER_VARIABLE_TITLE,
  SYSTEM_VARIABLE_SUBTITLE,
} from '../../TaskForm/utils/getTaskVariables';

jest.mock('reactstrap', () => ({
  Tooltip: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

jest.mock('react-perfect-scrollbar', () => {
  const Scrollbar = ({ children }: { children: React.ReactNode }) => <div>{children}</div>;
  Object.assign(Scrollbar, { __esModule: true, default: Scrollbar });
  return Scrollbar;
});

jest.mock('react-outside-click-handler', () => {
  const OutsideClick = ({ children }: { children: React.ReactNode }) => <div>{children}</div>;
  return {
    __esModule: true,
    default: OutsideClick,
  };
});

jest.mock('../../../UI', () => ({
  Tooltip: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  CustomTooltip: () => null,
}));

jest.mock('../../../icons', () => ({
  ExpandIcon: () => null,
}));

jest.mock('react-responsive', () => ({
  useMediaQuery: () => false,
}));

jest.mock('../../TooltipRichContent', () => ({
  TooltipRichContent: () => null,
}));

const formatMsg = (id: string) => intlMock.formatMessage({ id });

const LOCALIZED_WF_STARTER_TITLE = formatMsg('kickoff.system-varibale-workflow-starter');
const LOCALIZED_SYSTEM_SUBTITLE = formatMsg('kickoff.system-varibale');

describe('VariableList', () => {
  const mockOnVariableClick = jest.fn(() => jest.fn());
  const mockFocusEditor = jest.fn();

  const baseProps: IVariableListProps = {
    variables: [],
    tooltipText: 'Insert a variable',
    onVariableClick: mockOnVariableClick,
    focusEditor: mockFocusEditor,
  };

  const systemVariable: TTaskVariable = {
    apiName: WORKFLOW_STARTER_VARIABLE_API_NAME,
    title: WORKFLOW_STARTER_VARIABLE_TITLE,
    subtitle: SYSTEM_VARIABLE_SUBTITLE,
    type: EExtraFieldType.String,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('displays localized title and subtitle for system variable (workflow-starter)', () => {
    render(
      React.createElement(VariableList, {
        ...baseProps,
        variables: [systemVariable],
      }),
    );

    const button = screen.getByRole('button');
    userEvent.click(button);

    expect(screen.getByText(LOCALIZED_WF_STARTER_TITLE)).toBeInTheDocument();
    expect(screen.getByText(LOCALIZED_SYSTEM_SUBTITLE)).toBeInTheDocument();
  });

  it('displays original title for regular (non-system) variable', () => {
    const regularVariable: TTaskVariable = {
      apiName: 'client-name-3967',
      title: 'Client name',
      subtitle: 'Kick-off form',
      type: EExtraFieldType.String,
    };

    render(
      React.createElement(VariableList, {
        ...baseProps,
        variables: [regularVariable],
      }),
    );

    const button = screen.getByRole('button');
    userEvent.click(button);

    expect(screen.getByText('Client name')).toBeInTheDocument();
    expect(screen.getByText('Kick-off form')).toBeInTheDocument();
  });
});
