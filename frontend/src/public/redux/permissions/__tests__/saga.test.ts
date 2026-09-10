import { runSaga } from 'redux-saga';
import { call } from 'redux-saga/effects';

import { getUserObjectPermissions } from '../../../api/getUserObjectPermissions';
import { EPermissionObjectType } from '../../../types/permissions';
import { fetchObjectPermissions } from '../saga';
import { loadObjectPermissions, setObjectPermissions } from '../slice';

jest.mock('../../../api/getUserObjectPermissions', () => ({
  getUserObjectPermissions: jest.fn(),
}));

const runFetch = async (objIds: number[]) => {
  const dispatched: unknown[] = [];

  function* wrapper() {
    yield call(fetchObjectPermissions, loadObjectPermissions({ objType: EPermissionObjectType.Workflow, objIds }));
  }

  await runSaga({ dispatch: (action) => dispatched.push(action) }, wrapper).toPromise();

  return dispatched;
};

describe('fetchObjectPermissions', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('stores the permissions returned for the requested ids', async () => {
    const permissions = [
      { id: 1, hasView: true, hasChange: true },
      { id: 2, hasView: true, hasChange: false },
    ];
    (getUserObjectPermissions as jest.Mock).mockResolvedValue(permissions);

    const dispatched = await runFetch([1, 2]);

    expect(getUserObjectPermissions).toHaveBeenCalledWith({
      objType: EPermissionObjectType.Workflow,
      objIds: [1, 2],
    });
    expect(dispatched).toEqual([setObjectPermissions({ objType: EPermissionObjectType.Workflow, permissions })]);
  });

  it('collapses duplicate ids into a single request', async () => {
    (getUserObjectPermissions as jest.Mock).mockResolvedValue([]);

    await runFetch([1, 1, 2]);

    expect(getUserObjectPermissions).toHaveBeenCalledWith({
      objType: EPermissionObjectType.Workflow,
      objIds: [1, 2],
    });
  });

  it('does not call the API for an empty list', async () => {
    const dispatched = await runFetch([]);

    expect(getUserObjectPermissions).not.toHaveBeenCalled();
    expect(dispatched).toEqual([]);
  });

  it('keeps quiet when the request fails so the list stays usable', async () => {
    (getUserObjectPermissions as jest.Mock).mockRejectedValue(new Error('network'));

    const dispatched = await runFetch([1]);

    expect(dispatched).toEqual([]);
  });
});
