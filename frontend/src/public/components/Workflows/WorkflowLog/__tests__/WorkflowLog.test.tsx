// <reference types="jest" />

import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { WorkflowLog } from '../WorkflowLog';
import {
  EWorkflowLogEvent,
  EWorkflowsLogSorting,
  EWorkflowStatus,
  IWorkflowLogItem,
} from '../../../../types/workflow';
import { makeLogEvent, resetLogEventId } from '../../../../__stubs__/workflowLogEvents';
import { intlMock } from '../../../../__stubs__/intlMock';

jest.mock('react-redux', () => ({
  useSelector: () => [],
}));

jest.mock('../WorkflowLogEvents', () => ({
  WorkflowLogTaskComplete: () => <div data-testid="log-event" />,
  WorkflowLogTaskSkipped: () => <div data-testid="log-event" />,
  WorkflowLogTaskStart: () => <div data-testid="log-event" />,
  WorkflowLogDelay: () => <div data-testid="log-event" />,
  WorkflowLogProcessReturn: () => <div data-testid="log-event" />,
  WorkflowLogWorkflowEndedOnCondition: () => <div data-testid="log-event" />,
  WorkflowUrgent: () => <div data-testid="log-event" />,
  WorkflowSkippedTask: () => <div data-testid="log-event" />,
  WorkflowLogAddedPerformer: () => <div data-testid="log-event" />,
  WorkflowLogRemovedPerformer: () => <div data-testid="log-event" />,
  WorkflowLogWorkflowFinished: () => <div data-testid="log-event" />,
  WorkflowLogTaskCommentContainer: () => <div data-testid="log-event" />,
}));

jest.mock('../WorkflowLogSkeleton', () => ({
  WorkflowLogSkeleton: () => <div data-testid="skeleton" />,
}));

jest.mock('../WorkflowLogEvents/WorkflowLogWorkflowSnoozedManually', () => ({
  WorkflowLogWorkflowSnoozedManually: () => <div data-testid="log-event" />,
}));
jest.mock('../WorkflowLogEvents/WorkflowLogWorkflowResumed', () => ({
  WorkflowLogWorkflowResumed: () => <div data-testid="log-event" />,
}));
jest.mock('../WorkflowLogEvents/WorkflowLogDueDateChanged', () => ({
  WorkflowLogDueDateChanged: () => <div data-testid="log-event" />,
}));
jest.mock('../WorkflowLogEvents/WorkflowLogAddedPerformerGroup', () => ({
  WorkflowLogAddedPerformerGroup: () => <div data-testid="log-event" />,
}));
jest.mock('../WorkflowLogEvents/WorkflowLogRemovedPerformerGroup', () => ({
  WorkflowLogRemovedPerformerGroup: () => <div data-testid="log-event" />,
}));

jest.mock('../PopupCommentField', () => ({
  PopupCommentFieldContainer: () => null,
}));

jest.mock('../../../UI', () => ({
  SelectMenu: () => <div data-testid="select-menu" />,
  Tabs: () => <div data-testid="tabs" />,
}));

jest.mock('rc-switch', () => {
  const MockSwitch = (props: {
    onChange?: () => void;
    checked?: boolean;
    className?: string;
    'aria-label'?: string;
  }) => (
    <button
      role="switch"
      aria-checked={props.checked}
      aria-label={props['aria-label']}
      onClick={props.onChange}
      className={props.className}
    />
  );
  MockSwitch.displayName = 'MockSwitch';
  return {
    __esModule: true,
    default: MockSwitch,
  };
});

jest.mock('../../../IntlMessages', () => ({
  IntlMessages: ({ id, children }: { id: string; children?: (text: string) => React.ReactNode }) => {
    if (typeof children === 'function') {
      return <>{children(id)}</>;
    }
    return <span>{id}</span>;
  },
}));

jest.mock('../../../../utils/helpers', () => {
  const actual = jest.requireActual('../../../../utils/helpers');
  return { isArrayWithItems: actual.isArrayWithItems };
});

jest.mock('../../../../constants/sortings', () => ({
  workflowLogSortingValues: ['new', 'old'],
}));

const baseProps = {
  theme: 'white' as const,
  items: [] as IWorkflowLogItem[],
  sorting: EWorkflowsLogSorting.New,
  isCommentsShown: true,
  isCommentFieldHidden: true,
  isOnlyAttachmentsShown: false,
  isSkippedTasksShown: false,
  workflowId: 1,
  includeHeader: false,
  workflowStatus: EWorkflowStatus.Running,
  isLogMinimized: false,
  isLoading: false,
  areTasksClickable: false,
  areRightTogglesHidden: false,
  changeWorkflowLogViewSettings: jest.fn(),
  toggleSkippedTasksVisibility: jest.fn(),
  sendComment: jest.fn(),
};

describe('WorkflowLog', () => {
  const t = (id: string) => intlMock.formatMessage({ id });
  const SKIPPED_LABEL = t('workflows.log-skipped-tasks');

  beforeEach(() => {
    jest.clearAllMocks();
    resetLogEventId();
  });

  describe('Skipped tasks filtering', () => {
    const makeMixedItems = () => [
      makeLogEvent(EWorkflowLogEvent.TaskStart),
      makeLogEvent(EWorkflowLogEvent.TaskSkipped),
      makeLogEvent(EWorkflowLogEvent.TaskSkippedDueLackAssignedPerformers),
      makeLogEvent(EWorkflowLogEvent.TaskComplete),
    ];

    it('hides TaskSkipped and TaskSkippedDueLackAssignedPerformers when isSkippedTasksShown=false', () => {
      render(
        React.createElement(WorkflowLog, {
          ...baseProps,
          items: makeMixedItems(),
          isSkippedTasksShown: false,
        }),
      );

      const events = screen.getAllByTestId('log-event');
      expect(events).toHaveLength(2);
    });

    it('shows all events including skipped when isSkippedTasksShown=true', () => {
      render(
        React.createElement(WorkflowLog, {
          ...baseProps,
          items: makeMixedItems(),
          isSkippedTasksShown: true,
        }),
      );

      const events = screen.getAllByTestId('log-event');
      expect(events).toHaveLength(4);
    });
  });

  describe('Toggle visibility', () => {
    it('shows both toggles (skipped + comments) when areRightTogglesHidden=false', () => {
      render(
        React.createElement(WorkflowLog, {
          ...baseProps,
          includeHeader: true,
          areRightTogglesHidden: false,
        }),
      );

      expect(screen.getByText('workflows.log-skipped-tasks')).toBeInTheDocument();
      expect(screen.getByText('workflows.log-comments')).toBeInTheDocument();
    });

    it('hides both toggles when areRightTogglesHidden=true', () => {
      render(
        React.createElement(WorkflowLog, {
          ...baseProps,
          includeHeader: true,
          areRightTogglesHidden: true,
        }),
      );

      expect(screen.queryByText('workflows.log-skipped-tasks')).not.toBeInTheDocument();
      expect(screen.queryByText('workflows.log-comments')).not.toBeInTheDocument();
    });
  });

  describe('Toggle callback', () => {
    it('calls toggleSkippedTasksVisibility when skipped tasks switch is clicked', () => {
      const mockToggle = jest.fn();

      render(
        React.createElement(WorkflowLog, {
          ...baseProps,
          includeHeader: true,
          areRightTogglesHidden: false,
          toggleSkippedTasksVisibility: mockToggle,
        }),
      );

      const skippedSwitch = screen.getByRole('switch', { name: SKIPPED_LABEL });
      userEvent.click(skippedSwitch);

      expect(mockToggle).toHaveBeenCalledTimes(1);
    });
  });
});
