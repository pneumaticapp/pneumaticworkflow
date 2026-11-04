import type { RootState } from '../store';
import { TeamPages } from '../team/types';

export const getTeamPage = (state: RootState): TeamPages => state.team.page;
