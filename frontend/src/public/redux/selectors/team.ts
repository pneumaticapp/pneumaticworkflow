import { IApplicationState } from '../../types/redux';
import { TeamPages } from '../team/types';

export const getTeamPage = (state: IApplicationState): TeamPages => state.team.page;

export const getTeamCreatePerformerModalIsOpen = (state: IApplicationState): boolean =>
  state.team.createPerformerModal.isOpen;

export const getTeamCreatePerformerModalIsSubmitting = (state: IApplicationState): boolean =>
  state.team.createPerformerModal.isSubmitting;
