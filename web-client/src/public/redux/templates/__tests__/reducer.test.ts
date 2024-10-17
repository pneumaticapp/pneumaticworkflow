/* eslint-disable */
/* prettier-ignore */
import { INIT_STATE, reducer } from '../../templates/reducer';
import { changeTemplatesList, loadTemplates, loadTemplatesFailed, TTemplatesActions } from '../../actions';

describe('reducer', () => {
  it('возвращает изначальный стейт, если не был передан action', () => {
    const result = reducer(undefined, {} as TTemplatesActions);

    expect(result).toEqual(INIT_STATE);
  });
  it('возвращает изменённый листинг шаблонов', () => {
    const payload = {
      count: 1,
      offset: 0,
      items: [
        {
          id: 1,
          name: 'Test',
          tasksCount: 2,
          performersCount: 1,
          templateOwners: [],
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
  it('добавляет статус "загружается" в стор при получении шаблона', () => {
    const state = { ...INIT_STATE, isListLoading: false };
    const action = loadTemplates(6);

    const result = reducer(state, action);

    expect(result).toHaveProperty('isListLoading', true);
  });
  it('убирает статус "загружается" из стора при ошибке получения шаблона', () => {
    const state = { ...INIT_STATE, isListLoading: true };
    const action = loadTemplatesFailed();

    const result = reducer(state, action);

    expect(result).toHaveProperty('isListLoading', false);
  });
});
