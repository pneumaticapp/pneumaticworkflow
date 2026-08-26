import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ReactFlowProvider } from 'reactflow';
import { configure } from '@testing-library/react';

import { EExtraFieldType } from '../../../../../../types/template';
import { KickoffNode } from '../KickoffNode';

configure({ testIdAttribute: 'data-test-id' });

describe('KickoffNode', () => {
  it('should render kick-off label, plain description and field count', () => {
    render(
      <ReactFlowProvider>
        <KickoffNode
          id="kickoff"
          type="kickoff"
          data={{
            templateName: 'New Template',
            kickoff: {
              description: '<p>Nullam id ipsum et libero aliquet aliquet.</p>',
              fields: [
                {
                  apiName: 'field-1',
                  name: 'Client',
                  type: EExtraFieldType.String,
                  order: 0,
                  userId: null,
                  groupId: null,
                },
              ],
              fieldsets: [],
            },
          }}
          selected={false}
          isConnectable
          dragging={false}
          zIndex={1}
          xPos={0}
          yPos={0}
        />
      </ReactFlowProvider>,
    );

    expect(screen.getByText('Kick-off Form')).toBeInTheDocument();
    expect(screen.getByText('Nullam id ipsum et libero aliquet aliquet.')).toBeInTheDocument();
    expect(screen.getByText('1 field')).toBeInTheDocument();
  });

  it('should render without crashing when kickoff description is missing', () => {
    render(
      <ReactFlowProvider>
        <KickoffNode
          id="kickoff"
          type="kickoff"
          data={{
            templateName: 'New Template',
            kickoff: {
              description: undefined as unknown as string,
              fields: [],
              fieldsets: [],
            },
          }}
          selected={false}
          isConnectable
          dragging={false}
          zIndex={1}
          xPos={0}
          yPos={0}
        />
      </ReactFlowProvider>,
    );

    expect(screen.getByText('Kick-off Form')).toBeInTheDocument();
  });

  it('should call onEdit when the kebab is clicked', () => {
    const onEdit = jest.fn();

    render(
      <ReactFlowProvider>
        <KickoffNode
          id="kickoff"
          type="kickoff"
          data={{
            templateName: 'New Template',
            onEdit,
            kickoff: { description: '', fields: [], fieldsets: [] },
          }}
          selected={false}
          isConnectable
          dragging={false}
          zIndex={1}
          xPos={0}
          yPos={0}
        />
      </ReactFlowProvider>,
    );

    userEvent.click(screen.getByTestId('graph-node-edit'));

    expect(onEdit).toHaveBeenCalled();
  });

  it('should call onAddTask when the plus is clicked', () => {
    const onAddTask = jest.fn();

    render(
      <ReactFlowProvider>
        <KickoffNode
          id="kickoff"
          type="kickoff"
          data={{
            templateName: 'New Template',
            onAddTask,
            addTaskIntent: { kind: 'continue', afterId: 'kickoff' },
            kickoff: { description: '', fields: [], fieldsets: [] },
          }}
          selected={false}
          isConnectable
          dragging={false}
          zIndex={1}
          xPos={0}
          yPos={0}
        />
      </ReactFlowProvider>,
    );

    userEvent.click(screen.getByTestId('graph-add-task'));

    expect(onAddTask).toHaveBeenCalledWith({ kind: 'continue', afterId: 'kickoff' });
  });
});
