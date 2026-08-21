import * as React from 'react';
import { render, screen } from '@testing-library/react';
import { configure } from '@testing-library/react';

import { ConditionEdgeInfo } from '../ConditionEdgeInfo';

configure({ testIdAttribute: 'data-test-id' });

jest.mock('../../../../../UI', () => ({
  Tooltip: ({ content, children }: { content: React.ReactNode; children: React.ReactNode }) => (
    <div>
      {children}
      <div>{content}</div>
    </div>
  ),
}));

describe('ConditionEdgeInfo', () => {
  it('should render an info icon for a default edge', () => {
    render(<ConditionEdgeInfo />);

    expect(screen.getByTestId('graph-edge-info')).toBeInTheDocument();
  });

  it('should expose the condition summary for a conditional edge', () => {
    render(<ConditionEdgeInfo summary="Client filled" isConditional />);

    expect(screen.getByTestId('graph-edge-info')).toBeInTheDocument();
    expect(screen.getByText('if: Client filled')).toBeInTheDocument();
  });
});
