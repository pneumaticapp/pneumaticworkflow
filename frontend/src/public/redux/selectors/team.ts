import type { RootState } from '../store';
import type { ETeamPages } from '../team/types';

export const getTeamPage = (state: RootState): ETeamPages => state.team.page;

export const getTeamCreatePerformerModalIsOpen = (state: RootState): boolean => state.team.createPerformerModal.isOpen;

export const getTeamCreatePerformerModalIsSubmitting = (state: RootState): boolean =>
  state.team.createPerformerModal.isSubmitting;
