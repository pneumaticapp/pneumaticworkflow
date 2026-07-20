import { ETaskListCompletionStatus, ETaskStatus } from '../../../../types/tasks';
import {
  shouldDecrementCounterOnDeleted,
  shouldRemoveTaskOnDeleted,
} from '../shouldRemoveTaskOnDeleted';

describe('shouldRemoveTaskOnDeleted', () => {
  it('always removes active tasks', () => {
    expect(
      shouldRemoveTaskOnDeleted({
        status: ETaskStatus.Active,
        completionStatus: ETaskListCompletionStatus.Active,
      }),
    ).toBe(true);

    expect(
      shouldRemoveTaskOnDeleted({
        status: ETaskStatus.Active,
        completionStatus: ETaskListCompletionStatus.Completed,
      }),
    ).toBe(true);
  });

  it('removes completed tasks only on Completed tab', () => {
    expect(
      shouldRemoveTaskOnDeleted({
        status: ETaskStatus.Completed,
        completionStatus: ETaskListCompletionStatus.Completed,
      }),
    ).toBe(true);

    expect(
      shouldRemoveTaskOnDeleted({
        status: ETaskStatus.Completed,
        completionStatus: ETaskListCompletionStatus.Active,
      }),
    ).toBe(false);
  });

  it('removes snoozed tasks only on Completed tab', () => {
    expect(
      shouldRemoveTaskOnDeleted({
        status: ETaskStatus.Snoozed,
        completionStatus: ETaskListCompletionStatus.Completed,
      }),
    ).toBe(true);

    expect(
      shouldRemoveTaskOnDeleted({
        status: ETaskStatus.Snoozed,
        completionStatus: ETaskListCompletionStatus.Active,
      }),
    ).toBe(false);
  });
});

describe('shouldDecrementCounterOnDeleted', () => {
  it('decrements only for active tasks', () => {
    expect(shouldDecrementCounterOnDeleted(ETaskStatus.Active)).toBe(true);
    expect(shouldDecrementCounterOnDeleted(ETaskStatus.Completed)).toBe(false);
    expect(shouldDecrementCounterOnDeleted(ETaskStatus.Snoozed)).toBe(false);
  });
});
