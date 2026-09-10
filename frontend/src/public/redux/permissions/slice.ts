import { createAction, createSlice, PayloadAction } from '@reduxjs/toolkit';

import { IPermissionsStore } from '../../types/redux';
import { EPermissionObjectType, IObjectPermissionResponseItem } from '../../types/permissions';
import { EAuthActions, TAuthUserResult } from '../auth/actions';

const initialState: IPermissionsStore = {
  userId: null,
  [EPermissionObjectType.Workflow]: {},
};

export interface ILoadObjectPermissionsPayload {
  objType: EPermissionObjectType;
  objIds: number[];
}

export interface ISetObjectPermissionsPayload {
  objType: EPermissionObjectType;
  permissions: IObjectPermissionResponseItem[];
}

export const loadObjectPermissions = createAction<ILoadObjectPermissionsPayload>('permissions/loadObjectPermissions');

const permissionsSlice = createSlice({
  name: 'permissions',
  initialState,
  reducers: {
    /**
     * Merged, never replaced: list pages arrive one after another and each page must keep the
     * permissions already resolved for the pages before it.
     */
    setObjectPermissions: (state, action: PayloadAction<ISetObjectPermissionsPayload>) => {
      const { objType, permissions } = action.payload;

      permissions.forEach(({ id, hasView, hasChange }) => {
        state[objType][id] = { hasView, hasChange };
      });
    },
  },
  extraReducers: (builder) => {
    /**
     * Only a logout resets the whole store, but supermode and tenant switching replace the
     * signed-in user in place. Answers cached for the previous principal would then be read for
     * the new one until its own request lands, so they are dropped as soon as the user changes.
     */
    builder.addMatcher(
      (action): action is PayloadAction<TAuthUserResult> => action.type === EAuthActions.AuthUserSuccess,
      (state, action) => {
        const { id } = action.payload;

        if (state.userId === id) {
          return;
        }

        state.userId = id;
        Object.values(EPermissionObjectType).forEach((objType) => {
          state[objType] = {};
        });
      },
    );
  },
});

export const { setObjectPermissions } = permissionsSlice.actions;

export default permissionsSlice.reducer;
