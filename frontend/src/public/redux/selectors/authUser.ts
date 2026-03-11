import { IApplicationState, IAuthUser } from '../../types/redux';

export const getCurrentUser = (state: IApplicationState): IAuthUser => state.authUser;

export const getTimezone = (state: IApplicationState): string => state.authUser.timezone;

export const getAuthUserId = (state: IApplicationState): number => state.authUser.id;