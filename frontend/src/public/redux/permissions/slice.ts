import { createAction, createSlice, PayloadAction } from '@reduxjs/toolkit';

import { IPermissionsStore } from '../../types/redux';
import { EPermissionObjectType } from '../../types/permissions';
import { EAuthActions, TAuthUserResult } from '../auth/actions';

import { ILoadObjectPermissionsPayload, ISetObjectPermissionsPayload } from './types';

const initialState: IPermissionsStore = {
  userId: null,
  [EPermissionObjectType.Workflow]: {},
};

export const loadObjectPermissions = createAction<ILoadObjectPermissionsPayload>('permissions/loadObjectPermissions');

const permissionsSlice = createSlice({
  name: 'permissions',
  initialState,
  reducers: {
    // Merge, never replace: pages arrive one by one and must keep earlier results.
    setObjectPermissions: (state, action: PayloadAction<ISetObjectPermissionsPayload>) => {
      const { objType, permissions } = action.payload;

      permissions.forEach(({ id, hasView, hasChange }) => {
        state[objType][id] = { hasView, hasChange };
      });
    },
  },
  extraReducers: (builder) => {
    // Supermode and tenant switching replace the signed-in user in place; their cached
    // permissions must not be read for the new one.
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
