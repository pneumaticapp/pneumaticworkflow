// <reference types="jest" />
import { runSaga } from 'redux-saga';
import { call } from 'redux-saga/effects';

import { loadFieldsetsSaga } from '../saga';
import { getFieldsets } from '../../../api/fieldsets/getFieldsets';
import { loadFieldsets, loadFieldsetsFailed } from '../slice';
import { history } from '../../../utils/history';
import { ERoutes } from '../../../constants/routes';

jest.mock('../../../utils/getConfig', () => ({
  getBrowserConfigEnv: jest.fn().mockReturnValue({
    api: {
      urls: {
        templateFieldsets: '/templates/:id/fieldsets',
      },
    },
  }),
}));

jest.mock('../../../api/fieldsets/getFieldsets', () => ({
  getFieldsets: jest.fn(),
}));

jest.mock('../../../utils/history', () => ({
  history: { replace: jest.fn(), push: jest.fn() },
}));

jest.mock('../../../components/UI/Notifications', () => ({
  NotificationManager: { warning: jest.fn() },
}));

jest.mock('../../../utils/logger', () => ({
  logger: { error: jest.fn() },
}));

describe('loadFieldsetsSaga', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const makeMockState = () => ({
    fieldsets: {
      fieldsetsList: { items: [], count: 0, offset: 0 },
      fieldsetsListSorting: '-date',
      templateId: null,
      catalogLoadedForTemplateId: null,
    },
  });

  interface IDispatchedAction {
    type: string;
    payload?: unknown;
  }

  const runLoadFieldsets = async (
    templateId: number,
    offset: number = 0,
  ) => {
    const dispatched: IDispatchedAction[] = [];
    const mockState = makeMockState();
    const action = loadFieldsets({ templateId, offset });

    function* wrapper() {
      yield call(loadFieldsetsSaga, action);
    }

    const saga = runSaga(
      {
        dispatch: (dispatchedAction: IDispatchedAction) => {
          dispatched.push(dispatchedAction);
        },
        getState: () => mockState,
      },
      wrapper,
    );

    await saga.toPromise();

    return dispatched;
  };

  describe('Redirect on non-existent template', () => {
    it('redirects to templates list on 404 API response', async () => {
      const error404 = { status: 404, message: 'Not found' };
      (getFieldsets as jest.Mock).mockRejectedValue(error404);

      const dispatched = await runLoadFieldsets(9999);

      expect(getFieldsets).toHaveBeenCalledTimes(1);

      const failedAction = dispatched.find(
        (a) => a.type === loadFieldsetsFailed.type,
      );
      expect(failedAction).toBeDefined();

      expect(history.replace).toHaveBeenCalledTimes(1);
      expect(history.replace).toHaveBeenCalledWith(ERoutes.Templates);
    });

    it('does not redirect on non-404 errors', async () => {
      const error500 = { status: 500, message: 'Internal server error' };
      (getFieldsets as jest.Mock).mockRejectedValue(error500);

      const dispatched = await runLoadFieldsets(42);

      const failedAction = dispatched.find(
        (a) => a.type === loadFieldsetsFailed.type,
      );
      expect(failedAction).toBeDefined();

      expect(history.replace).not.toHaveBeenCalled();
    });
  });
});
