import * as React from 'react';
import { render, screen } from '@testing-library/react';
import { configure } from '@testing-library/react';
import { Position, ReactFlowProvider } from 'reactflow';

import { GraphConditionEdge } from '../GraphConditionEdge';

configure({ testIdAttribute: 'data-test-id' });

jest.mock('reactflow', () => {
  const actual = jest.requireActual('reactflow');

  return {
    ...actual,
    EdgeLabelRenderer: ({ children }: { children: React.ReactNode }) => children,
  };
});

jest.mock('../../../../../UI', () => ({
  Tooltip: ({ content, children }: { content: React.ReactNode; children: React.ReactNode }) => (
    <div>
      {children}
      <div>{content}</div>
    </div>
  ),
}));

const renderEdge = (data?: {
  summary?: string;
  isConditional?: boolean;
  startAfter?: string[];
  focus?: 'highlighted' | 'dimmed';
}) =>
  render(
    <ReactFlowProvider>
      <svg>
        <GraphConditionEdge
          id="edge-1"
          source="task-a"
          target="task-b"
          sourceX={0}
          sourceY={0}
          targetX={0}
          targetY={80}
          sourcePosition={Position.Bottom}
          targetPosition={Position.Top}
          data={data}
        />
      </svg>
    </ReactFlowProvider>,
  );

describe('GraphConditionEdge', () => {
  it('should hide the badge on an edge without a dependency to describe', () => {
    renderEdge({ isConditional: false });

    expect(screen.queryByTestId('graph-edge-label')).not.toBeInTheDocument();
  });

  it('should show the condition badge and tooltip on a conditional edge', () => {
    renderEdge({ isConditional: true, summary: 'Client filled' });

    expect(screen.getByTestId('graph-edge-label')).toBeInTheDocument();
    expect(screen.getByText('check if: Client filled')).toBeInTheDocument();
  });

  it('should show the start dependency badge on a plain edge', () => {
    renderEdge({ isConditional: false, startAfter: ['Prepare layout'] });

    expect(screen.getByTestId('graph-edge-label')).toBeInTheDocument();
    expect(screen.getByText('start after: Prepare layout')).toBeInTheDocument();
  });

  it('should hide the badge on a dashed segment that has nothing to describe', () => {
    renderEdge({ isConditional: true });

    expect(screen.queryByTestId('graph-edge-label')).not.toBeInTheDocument();
  });

  it('should dim the badge when the line is out of focus', () => {
    renderEdge({ isConditional: true, summary: 'Client filled', focus: 'dimmed' });

    expect(screen.getByTestId('graph-edge-label').getAttribute('class')).toContain('dimmed');
  });

  it('should keep the badge bright when the line is highlighted', () => {
    renderEdge({ isConditional: true, summary: 'Client filled', focus: 'highlighted' });

    expect(screen.getByTestId('graph-edge-label').getAttribute('class')).not.toContain('dimmed');
  });

  it('should draw from routed anchors instead of React Flow handle coordinates', () => {
    const { container } = render(
      <ReactFlowProvider>
        <svg>
          <GraphConditionEdge
            id="edge-1"
            source="task-a"
            target="task-b"
            sourceX={0}
            sourceY={0}
            targetX={0}
            targetY={80}
            sourcePosition={Position.Bottom}
            targetPosition={Position.Top}
            sourceHandleId="source-right"
            targetHandleId="target-left"
            data={{
              sourceAnchor: { x: 100, y: 40 },
              targetAnchor: { x: 220, y: 40 },
            }}
          />
        </svg>
      </ReactFlowProvider>,
    );
    const path = container.querySelector('.react-flow__edge-path');

    expect(path?.getAttribute('d')).toBe('M 100,40 L 220,40');
  });
});
