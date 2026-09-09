import * as React from 'react';
import { render, screen } from '@testing-library/react';
import { configure } from '@testing-library/react';

import { EConditionLogicOperations, EConditionOperators } from '../../../../TaskForm/Conditions';
import { ConditionEdgeInfo } from '../ConditionEdgeInfo';

configure({ testIdAttribute: 'data-test-id' });

jest.mock('../../../../../UI', () => ({
  Tooltip: ({
    content,
    children,
    className,
    contentClassName,
  }: {
    content: React.ReactNode;
    children: React.ReactNode;
    className?: string;
    contentClassName?: string;
  }) => (
    <div data-test-id="graph-edge-tooltip" className={className}>
      {children}
      <div className={contentClassName}>{content}</div>
    </div>
  ),
}));

describe('ConditionEdgeInfo', () => {
  it('should render a fallback tooltip when the condition has no summary', () => {
    render(<ConditionEdgeInfo />);

    expect(screen.getByTestId('graph-edge-info')).toBeInTheDocument();
    expect(screen.getByText('check if: condition')).toBeInTheDocument();
  });

  it('should expose the condition summary in the mockup tooltip', () => {
    render(<ConditionEdgeInfo summary="Client filled" />);

    expect(screen.getByTestId('graph-edge-info')).toBeInTheDocument();
    expect(screen.getByTestId('graph-edge-tooltip')).toBeInTheDocument();
    expect(screen.getByText('check if: Client filled')).toBeInTheDocument();
  });

  it('should describe a check-if clause with the localized operator', () => {
    render(
      <ConditionEdgeInfo
        clauses={[
          {
            fieldLabel: 'Client',
            operator: EConditionOperators.Exist,
            logicOperation: EConditionLogicOperations.And,
          },
        ]}
      />,
    );

    expect(screen.getByText('check if: Client Exists')).toBeInTheDocument();
  });
});
