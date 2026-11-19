import { mergePersistedState } from '../mergePersistedState';

describe('mergePersistedState', () => {
  const makeOriginalState = () => ({
    dashboard: {
      mode: 'today',
    },
    tasks: {
      tasksSettings: {
        isHasFilter: false,
        sorting: 'new',
      },
    },
  });

  it('does not mutate the original state object and its nested objects', () => {
    const original = makeOriginalState();
    const inbound = {
      tasks: {
        tasksSettings: {
          isHasFilter: false,
          sorting: 'overdue',
        },
      },
    };

    const result = mergePersistedState(inbound, original);

    expect(result).not.toBe(original);
    expect(result.tasks.tasksSettings).not.toBe(original.tasks.tasksSettings);
    expect(original.tasks.tasksSettings.sorting).toBe('new');
  });

  it('applies nested tasks.tasksSettings.sorting field from inbound state', () => {
    const original = makeOriginalState();
    const inbound = {
      tasks: {
        tasksSettings: {
          sorting: 'overdue',
        },
      },
    };

    const result = mergePersistedState(inbound, original);

    expect(result.tasks.tasksSettings.sorting).toBe('overdue');
  });

  it('preserves sibling fields in tasks.tasksSettings and other store branches', () => {
    const original = makeOriginalState();
    const inbound = {
      tasks: {
        tasksSettings: {
          sorting: 'overdue',
        },
      },
    };

    const result = mergePersistedState(inbound, original);

    expect(result.tasks.tasksSettings.isHasFilter).toBe(false);
    expect(result.dashboard.mode).toBe('today');
  });
});
