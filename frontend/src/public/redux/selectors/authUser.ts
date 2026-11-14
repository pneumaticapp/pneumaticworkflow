import type { IAuthUser } from '../auth/types';
import type { RootState } from '../store';

export const getCurrentUser = (state: RootState): IAuthUser => state.authUser;

export const getTimezone = (state: RootState): string => state.authUser.timezone;

export const getAuthUserId = (state: RootState): number => state.authUser.id;
