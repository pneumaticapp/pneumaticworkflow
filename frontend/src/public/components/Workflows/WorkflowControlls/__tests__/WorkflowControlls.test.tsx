// <reference types="jest" />
import * as React from 'react';
import { render, screen } from '@testing-library/react';
import { useDispatch, useSelector } from 'react-redux';

import { TDropdownOption } from '../../../UI';
import { enMessages } from '../../../../lang/locales/en_US';
import { EWorkflowStatus, IWorkflowClient } from '../../../../types/workflow';

import { WorkflowControllsComponents } from '../WorkflowControlls';

jest.mock('../../utils/getSnoozeOptions', () => ({
  getSnoozeOptions: () => [],
}));

type TResumeCase = {
  name: string;
  status: EWorkflowStatus;
  isHidden: boolean;
};

describe('WorkflowControllsComponents', () => {
  const RESUME_LABEL = enMessages['workflows.card-resume'];
  const authUser = { id: 1, isAccountOwner: true, isAdmin: false };
  const createWorkflow = (status: EWorkflowStatus) => {
    const workflow: Partial<IWorkflowClient> = {
      id: 1,
      owners: [authUser.id],
      status,
      isUrgent: false,
      finalizable: true,
      template: null,
      completedTasks: [],
    };

    return workflow as IWorkflowClient;
  };

  const renderResumeOption = (status: EWorkflowStatus) => {
    render(
      <WorkflowControllsComponents
        workflow={createWorkflow(status)}
        timezone="UTC"
      >
        {(options: TDropdownOption[]) => {
          const option = options.find(({ label }) => label === RESUME_LABEL);

          expect(option).toBeDefined();

          return (
            <span
              aria-label={RESUME_LABEL}
              data-hidden={String(Boolean(option?.isHidden))}
            />
          );
        }}
      </WorkflowControllsComponents>,
    );
  };

  beforeEach(() => {
    (useDispatch as jest.Mock).mockReturnValue(jest.fn());
    (useSelector as jest.Mock).mockReturnValue({ authUser });
  });

  const cases: TResumeCase[] = [
    {
      name: 'finished',
      status: EWorkflowStatus.Finished,
      isHidden: false,
    },
    {
      name: 'snoozed',
      status: EWorkflowStatus.Snoozed,
      isHidden: false,
    },
    {
      name: 'running',
      status: EWorkflowStatus.Running,
      isHidden: true,
    },
  ];

  it.each(cases)(
    'sets resume hidden=$isHidden for $name workflow',
    ({ status, isHidden }: TResumeCase) => {
      renderResumeOption(status);

      expect(screen.getByLabelText(RESUME_LABEL)).toHaveAttribute(
        'data-hidden',
        String(isHidden),
      );
    },
  );
});
