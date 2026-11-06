import type { RootState } from '../store';
import type { ETeamPages } from '../team/types';

export const getTeamPage = (state: RootState): ETeamPages => state.team.page;
