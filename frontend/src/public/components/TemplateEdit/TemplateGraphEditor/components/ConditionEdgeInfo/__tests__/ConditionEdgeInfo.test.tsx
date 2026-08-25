import * as React from 'react';
import { render, screen } from '@testing-library/react';
import { configure } from '@testing-library/react';

import { ConditionEdgeInfo } from '../ConditionEdgeInfo';
import { KICKOFF_START_AFTER } from '../../../utils/templateToGraph';

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
    render(<ConditionEdgeInfo isConditional />);

    expect(screen.getByTestId('graph-edge-info')).toBeInTheDocument();
    expect(screen.getByText('check if: condition')).toBeInTheDocument();
  });

  it('should expose the condition summary in the mockup tooltip', () => {
    render(<ConditionEdgeInfo summary="Client filled" isConditional />);

    expect(screen.getByTestId('graph-edge-info')).toBeInTheDocument();
    expect(screen.getByTestId('graph-edge-tooltip')).toBeInTheDocument();
    expect(screen.getByText('check if: Client filled')).toBeInTheDocument();
  });

  it('should describe a plain edge as a start dependency', () => {
    render(<ConditionEdgeInfo startAfter={['Prepare layout']} />);

    expect(screen.getByText('start after: Prepare layout')).toBeInTheDocument();
  });

  it('should list every source of a merged start dependency', () => {
    render(<ConditionEdgeInfo startAfter={['Prepare layout', 'Collect assets']} />);

    expect(screen.getByText('start after: Prepare layout, Collect assets')).toBeInTheDocument();
  });

  it('should localize the kick-off form as a start dependency source', () => {
    render(<ConditionEdgeInfo startAfter={[KICKOFF_START_AFTER]} />);

    expect(screen.getByText('start after: Kick-off Form')).toBeInTheDocument();
  });
});
