import * as React from 'react';
import { act, render } from '@testing-library/react';

import { TemplateEntity } from '../TemplateEntity';
import { WorkflowTaskFormContainer } from '../../TaskForm';
import { useOpenOnValidationError } from '../../TemplateValidationError';
import { makeTemplateTaskClient } from '../../../../__stubs__/templates.factory';
import { ITemplateEntityProps } from '../TemplateEntity.props';

jest.mock('../../TaskForm', () => ({ WorkflowTaskFormContainer: jest.fn(() => null) }));
jest.mock('../../TaskItem', () => ({ TaskItem: () => null }));
jest.mock('../../TaskMenu', () => ({ TaskMenu: () => null }));
jest.mock('../../AddEntityButton', () => ({ AddEntityButton: () => null, EEntityTitle: {} }));
jest.mock('../../Delay', () => ({ Delay: () => null }));
jest.mock('../../TemplateValidationError', () => ({ useOpenOnValidationError: jest.fn() }));

const makeProps = (overrides: Partial<ITemplateEntityProps> = {}): ITemplateEntityProps => ({
  index: 0,
  task: makeTemplateTaskClient({ uuid: 'task-uuid' }),
  users: [],
  tasksCount: 1,
  isSubscribed: false,
  isTaskOpen: false,
  isDelayOpen: false,
  addDelay: jest.fn(),
  addTaskBefore: jest.fn(),
  deleteDelay: jest.fn(() => jest.fn()),
  editDelay: jest.fn(),
  toggleDelay: jest.fn(),
  handleMoveTask: jest.fn(() => jest.fn()),
  removeTask: jest.fn(),
  toggleIsOpenTask: jest.fn(),
  cloneTask: jest.fn(),
  ...overrides,
});

const getLastFormProps = () => {
  const { calls } = (WorkflowTaskFormContainer as unknown as jest.Mock).mock;

  return calls[calls.length - 1][0];
};

const openByValidation = () => {
  const { calls } = (useOpenOnValidationError as jest.Mock).mock;
  act(() => calls[calls.length - 1][1]());
};

describe('TemplateEntity', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('marks the task form as opened by validation so it does not take over the scroll', () => {
    const toggleIsOpenTask = jest.fn();
    const { rerender } = render(<TemplateEntity {...makeProps({ toggleIsOpenTask })} />);

    openByValidation();
    rerender(<TemplateEntity {...makeProps({ toggleIsOpenTask, isTaskOpen: true })} />);

    expect(toggleIsOpenTask).toHaveBeenCalledTimes(1);
    expect(getLastFormProps().isOpenedByValidation).toBe(true);
  });

  it('opens the task normally after it was closed', () => {
    const { rerender } = render(<TemplateEntity {...makeProps()} />);

    openByValidation();
    rerender(<TemplateEntity {...makeProps({ isTaskOpen: true })} />);
    rerender(<TemplateEntity {...makeProps({ isTaskOpen: false })} />);
    rerender(<TemplateEntity {...makeProps({ isTaskOpen: true })} />);

    expect(getLastFormProps().isOpenedByValidation).toBe(false);
  });

  it('does not toggle a task that is already open', () => {
    const toggleIsOpenTask = jest.fn();
    render(<TemplateEntity {...makeProps({ toggleIsOpenTask, isTaskOpen: true })} />);

    openByValidation();

    expect(toggleIsOpenTask).not.toHaveBeenCalled();
    expect(getLastFormProps().isOpenedByValidation).toBe(false);
  });
});
