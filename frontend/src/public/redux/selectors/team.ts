import type { IApplicationState } from '../store';
import { TeamPages } from '../team/types';

export const getTeamPage = (state: IApplicationState): TeamPages => state.team.page;
