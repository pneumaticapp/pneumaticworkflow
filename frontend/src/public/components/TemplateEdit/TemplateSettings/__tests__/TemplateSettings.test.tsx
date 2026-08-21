import * as React from 'react';
import { render, screen } from '@testing-library/react';
import { useDispatch, useSelector } from 'react-redux';
import { configure } from '@testing-library/react';

import { TemplateSettings } from '../TemplateSettings';
import { EGraphViewMode } from '../../TemplateGraphEditor';
import { ITemplateClient } from '../../../../types/template';

configure({ testIdAttribute: 'data-test-id' });

jest.mock('../../../UI', () => ({
  EditableText: ({ text }: { text: string }) => <h1>{text}</h1>,
}));

jest.mock('../../../RichEditor', () => ({
  RichEditor: () => <div data-test-id="template-description-editor" />,
}));

jest.mock('../../TemplateControlls', () => ({
  TemplateControllsContainer: () => <div data-test-id="template-controls" />,
}));

jest.mock('../../TemplateLastUpdateInfo', () => ({
  TemplateLastUpdateInfo: () => <div data-test-id="template-last-update" />,
}));

jest.mock('../../InfoWarningsModal', () => ({
  InfoWarningsModal: () => null,
}));

jest.mock('react-sticky-box', () => ({
  __esModule: true,
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

const mockTemplate: ITemplateClient = {
  name: 'New Template New Template',
  description: 'Should be hidden in graph mode',
  isActive: false,
  finalizable: false,
  completionNotification: false,
  reminderNotification: false,
  dateUpdated: '2024-01-01',
  updatedBy: 1,
  owners: [],
  kickoff: { description: '', fields: [], fieldsets: [] },
  tasks: [],
  isPublic: false,
  publicUrl: null,
  publicSuccessUrl: null,
  isEmbedded: false,
  embedUrl: null,
  wfNameTemplate: null,
  tasksCount: 0,
  performersCount: 0,
};

const mockDispatch = jest.fn();

const renderSettings = (viewMode: EGraphViewMode, selectedTaskApiName: string | null = null) => {
  (useDispatch as jest.Mock).mockReturnValue(mockDispatch);
  (useSelector as jest.Mock).mockImplementation((selector: (state: unknown) => unknown) =>
    selector({
      template: { data: mockTemplate },
      templateGraphView: { viewMode, selectedTaskApiName },
    }),
  );

  return render(<TemplateSettings />);
};

describe('TemplateSettings', () => {
  it('should keep the title and hide extras in graph mode', () => {
    renderSettings(EGraphViewMode.Graph);

    expect(screen.getByText('New Template New Template')).toBeInTheDocument();
    expect(screen.queryByTestId('template-description-editor')).not.toBeInTheDocument();
    expect(screen.queryByTestId('template-controls')).not.toBeInTheDocument();
    expect(screen.queryByTestId('template-last-update')).not.toBeInTheDocument();
  });

  it('should show description and controls in line mode', () => {
    renderSettings(EGraphViewMode.List);

    expect(screen.getByTestId('template-description-editor')).toBeInTheDocument();
    expect(screen.getByTestId('template-controls')).toBeInTheDocument();
    expect(screen.getByTestId('template-last-update')).toBeInTheDocument();
  });

  it('should keep title-only settings when editing a task from graph', () => {
    renderSettings(EGraphViewMode.Graph, 'task-1');

    expect(screen.getByText('New Template New Template')).toBeInTheDocument();
    expect(screen.queryByTestId('template-description-editor')).not.toBeInTheDocument();
    expect(screen.queryByTestId('template-controls')).not.toBeInTheDocument();
  });
});
