import { INIT_STATE, reducer } from '../../templates/reducer';
import { changeTemplatesList, loadTemplates, loadTemplatesFailed, TTemplatesActions } from '../../actions';

describe('reducer', () => {
  it('returns the initial state if no action was passed', () => {
    const result = reducer(undefined, {} as TTemplatesActions);

    expect(result).toEqual(INIT_STATE);
  });
  it('returns the modified template listing', () => {
    const payload = {
      count: 1,
      offset: 0,
      items: [
        {
          id: 1,
          name: 'Test',
          tasksCount: 2,
          performersCount: 1,
          owners: [],
          kickoff: null,
          isActive: true,
          isPublic: false,
        },
      ],
    };
    const state = { ...INIT_STATE, isListLoading: true };
    const action = changeTemplatesList(payload);

    const result = reducer(state, action);

    expect(result).toHaveProperty('isListLoading', false);
    expect(result).toHaveProperty('templatesList', payload);
  });
  it('adds a “loading” status to the store when fetching the template', () => {
    const state = { ...INIT_STATE, isListLoading: false };
    const action = loadTemplates(6);

    const result = reducer(state, action);

    expect(result).toHaveProperty('isListLoading', true);
  });
  it('removes the “loading” status from the store upon an error while fetching the template', () => {
    const state = { ...INIT_STATE, isListLoading: true };
    const action = loadTemplatesFailed();

    const result = reducer(state, action);

    expect(result).toHaveProperty('isListLoading', false);
  });
});
