import reducer, {
  clearTemplateValidationErrors,
  initialState,
  removeTemplateValidationErrors,
  setTemplateValidationErrors,
} from '../slice';
import { ETemplateActions } from '../../template/actions';
import type { ITemplateValidationError } from '../types';

const makeError = (apiName: string): ITemplateValidationError => ({
  apiName,
  message: 'Fill in the condition',
  target: { taskUuid: 'task-uuid', section: null, elementApiName: apiName },
  entitySnapshot: '{}',
});

describe('templateValidation slice', () => {
  it('starts a new batch focused on the first error', () => {
    const state = reducer(initialState, setTemplateValidationErrors([makeError('a'), makeError('b')]));

    expect(state.errors.map(({ apiName }) => apiName)).toEqual(['a', 'b']);
    expect(state.batchId).toBe(1);
    expect(state.focusElementApiName).toBe('a');
  });

  it('removes fixed errors without starting a new batch', () => {
    const withErrors = reducer(initialState, setTemplateValidationErrors([makeError('a'), makeError('b')]));
    const state = reducer(withErrors, removeTemplateValidationErrors(['a']));

    expect(state.errors.map(({ apiName }) => apiName)).toEqual(['b']);
    expect(state.batchId).toBe(1);
    expect(state.focusElementApiName).toBe('a');
  });

  it('clears errors explicitly and when the template store is reset', () => {
    const withErrors = reducer(initialState, setTemplateValidationErrors([makeError('a')]));

    expect(reducer(withErrors, clearTemplateValidationErrors()).errors).toEqual([]);
    expect(reducer(withErrors, { type: ETemplateActions.ResetTemplateStore }).errors).toEqual([]);
  });
});
