import { IApplicationState } from '../../types/redux';
import { IGroup } from '../team/types';

export const getGroups = (state: IApplicationState): IGroup[] => state.groups.list;
