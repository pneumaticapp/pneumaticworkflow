import reducer, {
  loadHighlightsTemplatesTitles,
  resetHighlightsStore,
  setHighlights,
  setHighlightsFilters,
  setHighlightsFiltersChanged,
} from '../slice';
import { EGeneralActions } from '../../general/actions';
import { EHighlightsDateFilter, IHighlightsItem } from '../../../types/highlights';

const NOW = '2024-11-27T10:03:00.000Z';

describe('highlights slice', () => {
  let nowSpy: jest.SpyInstance;

  beforeEach(() => {
    nowSpy = jest.spyOn(Date, 'now').mockReturnValue(new Date(NOW).getTime());
  });

  afterEach(() => {
    nowSpy.mockRestore();
  });

  const getState = () => reducer(undefined, { type: 'INIT' });

  it('builds the initial Today range from the current clock', () => {
    const { filters } = getState();

    expect(filters.timeRange).toBe(EHighlightsDateFilter.Today);
    expect(filters.startDate.getTime()).toBeLessThanOrEqual(Date.now());
    expect(filters.endDate.getTime()).toBeGreaterThan(Date.now());
  });

  it('merges partial filters', () => {
    const state = reducer(getState(), setHighlightsFilters({ usersFilter: [1, 2] }));

    expect(state.filters.usersFilter).toEqual([1, 2]);
    expect(state.filters.timeRange).toBe(EHighlightsDateFilter.Today);
  });

  it('marks template titles as loading when they are requested', () => {
    const state = reducer(getState(), loadHighlightsTemplatesTitles({}));

    expect(state.isTemplatesTitlesLoading).toBe(true);
  });

  it('keeps filters when the store is reset', () => {
    const withData = reducer(
      reducer(getState(), setHighlightsFilters({ templatesFilter: [7] })),
      setHighlights({ count: 1, results: [{ id: 1 } as IHighlightsItem] }),
    );

    const state = reducer(withData, resetHighlightsStore());

    expect(state.items).toEqual([]);
    expect(state.count).toBe(0);
    expect(state.filters.templatesFilter).toEqual([7]);
  });

  it('resets filters to today on clearing app filters', () => {
    const changed = reducer(
      reducer(getState(), setHighlightsFilters({ timeRange: EHighlightsDateFilter.Month, usersFilter: [3] })),
      setHighlightsFiltersChanged(),
    );

    const state = reducer(changed, { type: EGeneralActions.ClearAppFilters });

    expect(state.filters.timeRange).toBe(EHighlightsDateFilter.Today);
    expect(state.filters.usersFilter).toEqual([]);
    expect(state.filters.hasChangedFilters).toBe(false);
  });
});
