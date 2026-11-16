import { EPermissionObjectType } from '../../../types/permissions';
import { EAuthActions } from '../../auth/actions';
import reducer, { setObjectPermissions } from '../slice';

const initialState = reducer(undefined, { type: '@@INIT' });

const signIn = (id: number) => ({ type: EAuthActions.AuthUserSuccess, payload: { id } });

const withPermissions = (state: typeof initialState, id: number, hasChange: boolean) =>
  reducer(
    state,
    setObjectPermissions({
      objType: EPermissionObjectType.Workflow,
      permissions: [{ id, hasView: true, hasChange }],
    }),
  );

describe('permissions slice', () => {
  it('starts with no known permissions', () => {
    expect(initialState[EPermissionObjectType.Workflow]).toEqual({});
  });

  it('keys the permissions by object id', () => {
    const state = reducer(
      initialState,
      setObjectPermissions({
        objType: EPermissionObjectType.Workflow,
        permissions: [{ id: 7, hasView: true, hasChange: true }],
      }),
    );

    expect(state[EPermissionObjectType.Workflow]).toEqual({
      7: { hasView: true, hasChange: true },
    });
  });

  it('merges a later page into the permissions already resolved', () => {
    const firstPage = reducer(
      initialState,
      setObjectPermissions({
        objType: EPermissionObjectType.Workflow,
        permissions: [{ id: 1, hasView: true, hasChange: true }],
      }),
    );

    const secondPage = reducer(
      firstPage,
      setObjectPermissions({
        objType: EPermissionObjectType.Workflow,
        permissions: [{ id: 2, hasView: true, hasChange: false }],
      }),
    );

    expect(secondPage[EPermissionObjectType.Workflow]).toEqual({
      1: { hasView: true, hasChange: true },
      2: { hasView: true, hasChange: false },
    });
  });

  it('overwrites a stale answer for the same object', () => {
    const granted = reducer(
      initialState,
      setObjectPermissions({
        objType: EPermissionObjectType.Workflow,
        permissions: [{ id: 1, hasView: true, hasChange: true }],
      }),
    );

    const revoked = reducer(
      granted,
      setObjectPermissions({
        objType: EPermissionObjectType.Workflow,
        permissions: [{ id: 1, hasView: true, hasChange: false }],
      }),
    );

    expect(revoked[EPermissionObjectType.Workflow][1]).toEqual({ hasView: true, hasChange: false });
  });

  it('drops the cached answers when another user signs in', () => {
    const firstUser = withPermissions(reducer(initialState, signIn(1)), 42, true);

    const secondUser = reducer(firstUser, signIn(2));

    expect(secondUser[EPermissionObjectType.Workflow]).toEqual({});
    expect(secondUser.userId).toBe(2);
  });

  it('keeps the cache when the same user is refreshed', () => {
    const state = withPermissions(reducer(initialState, signIn(1)), 42, true);

    const refreshed = reducer(state, signIn(1));

    expect(refreshed[EPermissionObjectType.Workflow][42]).toEqual({ hasView: true, hasChange: true });
  });
});
