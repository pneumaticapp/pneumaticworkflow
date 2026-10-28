import reducer, {
  closeCreatePerformerModal,
  createPerformerFailed,
  createPerformerStarted,
  openCreatePerformerModal,
} from '../slice';

jest.mock('../../../utils/history', () => ({
  history: { push: jest.fn() },
  checkSomeRouteIsActive: jest.fn(() => false),
}));

describe('team slice: create performer modal', () => {
  const initial = reducer(undefined, { type: 'init' });

  it('opens closed and idle', () => {
    expect(initial.createPerformerModal).toEqual({ isOpen: false, isSubmitting: false });
  });

  it('tracks submitting and keeps the modal open on failure', () => {
    const submitting = reducer(reducer(initial, openCreatePerformerModal()), createPerformerStarted());

    expect(submitting.createPerformerModal).toEqual({ isOpen: true, isSubmitting: true });
    expect(reducer(submitting, createPerformerFailed()).createPerformerModal).toEqual({
      isOpen: true,
      isSubmitting: false,
    });
  });

  it('resets submitting when the modal closes', () => {
    const submitting = reducer(reducer(initial, openCreatePerformerModal()), createPerformerStarted());

    expect(reducer(submitting, closeCreatePerformerModal()).createPerformerModal).toEqual({
      isOpen: false,
      isSubmitting: false,
    });
  });
});
