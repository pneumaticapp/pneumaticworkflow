import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useDispatch, useSelector } from 'react-redux';

import { TemplateEditorContainer } from '../TemplateEditorContainer';
import { useTemplateEditorController } from '../../../../hooks/useTemplateEditorController';
import { selectIsGraphCanvas, selectTemplateSelectedTaskApiName } from '../../../../redux/selectors/templateGraphView';
import { setSelectedTask } from '../../../../redux/templateGraphView/slice';
import { ITemplateClient } from '../../../../types/template';
import { ITemplateEditorController } from '../../types';
import { IAuthUser } from '../../../../types/redux';

jest.mock('../../../../hooks/useTemplateEditorController');
jest.mock('../../AutoSaveStatus', () => ({ AutoSaveStatusContainer: () => null }));
jest.mock('../../TemplateSettings', () => ({ TemplateSettings: () => <div>settings</div> }));
jest.mock('../../TemplateLeavingGuard', () => ({ TemplateLeavingGuard: () => null }));
jest.mock('../../ConditionsBanner', () => ({ ConditionsBanner: () => <div>conditions-banner</div> }));
jest.mock('../../TemplateLineEditorView/TemplateLineEditorView', () => ({
  TemplateLineEditorView: () => <div>line-view</div>,
}));
jest.mock('../../TemplateGraphEditorView/TemplateGraphEditorView', () => ({
  TemplateGraphEditorView: ({ selectTask }: { selectTask(apiName: string | null): void }) => (
    <div>
      graph-view
      <button type="button" onClick={() => selectTask('task-1')}>
        select graph task
      </button>
    </div>
  ),
}));

const template = {
  id: 1,
  name: 'Template',
  tasks: [],
  kickoff: { description: '', fields: [], fieldsets: [] },
} as unknown as ITemplateClient;

const controller: ITemplateEditorController = {
  sortedTasks: [],
  openedTasks: {},
  openedDelays: {},
  setKickoff: jest.fn(),
  addTask: jest.fn(),
  addTaskBefore: jest.fn(),
  addTaskFromGraph: jest.fn(() => null),
  removeTask: jest.fn(),
  cloneTask: jest.fn(),
  moveTask: jest.fn(),
  addDelay: jest.fn(),
  editDelay: jest.fn(),
  deleteDelay: jest.fn(),
  toggleTask: jest.fn(),
  toggleDelay: jest.fn(),
};

const renderContainer = (accessConditions = true) =>
  render(
    <TemplateEditorContainer
      template={template}
      authUser={{ id: 1 } as IAuthUser}
      users={[]}
      isSubscribed
      accessConditions={accessConditions}
      shouldOpenFirstTask={false}
      saveTemplate={jest.fn()}
      setTemplate={jest.fn()}
      setTemplateStatus={jest.fn()}
    />,
  );

describe('TemplateEditorContainer', () => {
  const dispatch = jest.fn();
  let isGraphCanvas = false;
  let selectedTaskApiName: string | null = null;

  beforeEach(() => {
    jest.clearAllMocks();
    isGraphCanvas = false;
    selectedTaskApiName = null;
    (useDispatch as jest.Mock).mockReturnValue(dispatch);
    (useSelector as jest.Mock).mockImplementation((selector: unknown) => {
      if (selector === selectIsGraphCanvas) return isGraphCanvas;
      if (selector === selectTemplateSelectedTaskApiName) return selectedTaskApiName;
      return undefined;
    });
    (useTemplateEditorController as jest.Mock).mockReturnValue(controller);
  });

  it('should render the line view when graph mode is disabled', () => {
    renderContainer();

    expect(screen.getByText('line-view')).toBeInTheDocument();
    expect(screen.queryByText('graph-view')).not.toBeInTheDocument();
  });

  it('should render the graph view when graph mode is enabled', () => {
    isGraphCanvas = true;

    renderContainer();

    expect(screen.getByText('graph-view')).toBeInTheDocument();
    expect(screen.queryByText('line-view')).not.toBeInTheDocument();
  });

  it('should dispatch the shared editor selection from graph view', () => {
    isGraphCanvas = true;
    renderContainer();

    userEvent.click(screen.getByRole('button', { name: 'select graph task' }));

    expect(dispatch).toHaveBeenCalledWith(setSelectedTask('task-1'));
  });

  it('should render the conditions banner when conditions are unavailable', () => {
    renderContainer(false);

    expect(screen.getByText('conditions-banner')).toBeInTheDocument();
  });

  it('should pass the current template state to the editor controller', () => {
    renderContainer();

    expect(useTemplateEditorController).toHaveBeenCalledWith(
      expect.objectContaining({
        template,
        accessConditions: true,
        shouldOpenFirstTask: false,
        setTemplateStatus: expect.any(Function),
      }),
    );
  });
});
