import { INIT_STATE, reducer } from '../../templates/reducer';
import {
  changeTemplatesList,
  loadTemplates,
  loadTemplatesFailed,
  loadTemplateVariablesSuccess,
  saveTemplateTasks,
  TTemplatesActions,
} from '../../actions';
import { TTransformedTask } from '../../../types/template';
import { TTaskVariable } from '../../../components/TemplateEdit/types';
import { EExtraFieldType } from '../../../types/template';

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
          isEditable: true,
        },
      ],
    };
    const state = { ...INIT_STATE, isListLoading: true };
    const action = changeTemplatesList(payload);

    const result = reducer(state, action);

    expect(result).toHaveProperty('isListLoading', false);
    expect(result).toHaveProperty('templatesList', payload);
  });
  it('adds a "loading" status to the store when fetching the template', () => {
    const state = { ...INIT_STATE, isListLoading: false };
    const action = loadTemplates(6);

    const result = reducer(state, action);

    expect(result).toHaveProperty('isListLoading', true);
  });
  it('removes the "loading" status from the store upon an error while fetching the template', () => {
    const state = { ...INIT_STATE, isListLoading: true };
    const action = loadTemplatesFailed();

    const result = reducer(state, action);

    expect(result).toHaveProperty('isListLoading', false);
  });
});

describe('LoadTemplateVariablesSuccess — template variables merge', () => {
  const makeVariable = (apiName: string, title = `Var ${apiName}`): TTaskVariable => ({
    apiName,
    title,
    type: EExtraFieldType.String,
  });

  const TEMPLATE_ID = 42;

  it('writes variables to an empty map on first call', () => {
    const variables = [makeVariable('var-1'), makeVariable('var-2')];
    const state = { ...INIT_STATE, templatesVariablesMap: {} };
    const action = loadTemplateVariablesSuccess({ templateId: TEMPLATE_ID, variables });

    const result = reducer(state, action);

    expect(result.templatesVariablesMap[TEMPLATE_ID]).toHaveLength(2);
    expect(result.templatesVariablesMap[TEMPLATE_ID]).toEqual(variables);
  });

  it('replaces variables with matching apiName and preserves unique old ones', () => {
    const oldVariables = [makeVariable('var-1', 'Old V1'), makeVariable('var-2', 'Old V2')];
    const newVariables = [makeVariable('var-1', 'New V1'), makeVariable('var-3', 'New V3')];

    const state = {
      ...INIT_STATE,
      templatesVariablesMap: { [TEMPLATE_ID]: oldVariables },
    };
    const action = loadTemplateVariablesSuccess({ templateId: TEMPLATE_ID, variables: newVariables });

    const result = reducer(state, action);

    expect(result.templatesVariablesMap[TEMPLATE_ID]).toHaveLength(3);
    expect(result.templatesVariablesMap[TEMPLATE_ID].find((v) => v.apiName === 'var-1')?.title)
      .toBe('New V1');
    expect(result.templatesVariablesMap[TEMPLATE_ID].find((v) => v.apiName === 'var-2')?.title)
      .toBe('Old V2');
    expect(result.templatesVariablesMap[TEMPLATE_ID].find((v) => v.apiName === 'var-3')?.title)
      .toBe('New V3');
  });

  it('does not clear existing variables on pre-flush with empty array', () => {
    const existingVariables = [makeVariable('var-1'), makeVariable('var-2')];
    const state = {
      ...INIT_STATE,
      templatesVariablesMap: { [TEMPLATE_ID]: existingVariables },
    };
    const action = loadTemplateVariablesSuccess({ templateId: TEMPLATE_ID, variables: [] });

    const result = reducer(state, action);

    expect(result.templatesVariablesMap[TEMPLATE_ID]).toEqual(existingVariables);
  });
});

describe('SaveTemplateTasks — transformedTasks with fieldsets', () => {
  const TEMPLATE_ID = 42;

  const makeTransformedTask = (apiName: string, name: string): TTransformedTask => ({
    apiName,
    name,
    mergedOutputs: [],
  });

  it('writes transformedTasks to templatesTasksMap', () => {
    const tasks = [makeTransformedTask('-2', 'System'), makeTransformedTask('task-1', 'Task One')];
    const state = { ...INIT_STATE, templatesTasksMap: {} };
    const action = saveTemplateTasks({ templateId: TEMPLATE_ID, transformedTasks: tasks });

    const result = reducer(state, action);

    expect(result.templatesTasksMap[TEMPLATE_ID]).toEqual(tasks);
  });

  it('overwrites transformedTasks on subsequent calls', () => {
    const oldTasks = [makeTransformedTask('-2', 'System'), makeTransformedTask('task-1', 'Old Task')];
    const newTasks = [
      makeTransformedTask('-2', 'System'),
      makeTransformedTask('task-1', 'Updated Task'),
      makeTransformedTask('task-2', 'New Task'),
    ];
    const state = {
      ...INIT_STATE,
      templatesTasksMap: { [TEMPLATE_ID]: oldTasks },
    };
    const action = saveTemplateTasks({ templateId: TEMPLATE_ID, transformedTasks: newTasks });

    const result = reducer(state, action);

    expect(result.templatesTasksMap[TEMPLATE_ID]).toEqual(newTasks);
    expect(result.templatesTasksMap[TEMPLATE_ID]).toHaveLength(3);
  });
});
