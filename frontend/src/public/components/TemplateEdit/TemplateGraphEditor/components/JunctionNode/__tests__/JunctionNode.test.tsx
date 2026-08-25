import * as React from 'react';
import { render, screen } from '@testing-library/react';
import { ReactFlowProvider } from 'reactflow';
import { configure } from '@testing-library/react';

import { JunctionNode } from '../JunctionNode';

configure({ testIdAttribute: 'data-test-id' });

const nodeProps = {
  id: 'junction-fork-task-a',
  type: 'junction',
  selected: false,
  isConnectable: false,
  dragging: false,
  zIndex: 1,
  xPos: 0,
  yPos: 0,
};

describe('JunctionNode', () => {
  it('should render a fork node', () => {
    render(
      <ReactFlowProvider>
        <JunctionNode {...nodeProps} data={{ kind: 'fork' }} />
      </ReactFlowProvider>,
    );

    expect(screen.getByTestId('graph-junction-node')).toHaveAttribute('data-kind', 'fork');
  });

  it('should render a join node', () => {
    render(
      <ReactFlowProvider>
        <JunctionNode
          {...nodeProps}
          id="junction-join-task-d"
          data={{ kind: 'join' }}
        />
      </ReactFlowProvider>,
    );

    expect(screen.getByTestId('graph-junction-node')).toHaveAttribute('data-kind', 'join');
  });

  it('should keep docking handles invisible and centred on the node', () => {
    const { container } = render(
      <ReactFlowProvider>
        <JunctionNode {...nodeProps} data={{ kind: 'fork' }} />
      </ReactFlowProvider>,
    );
    const handles = container.querySelectorAll('.react-flow__handle');

    expect(handles).toHaveLength(8);
    handles.forEach((handle) => {
      expect(handle).toHaveStyle({ opacity: '0', top: '50%', left: '50%' });
    });
  });
});
