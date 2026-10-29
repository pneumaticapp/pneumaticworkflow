import React from 'react';
import { Provider } from 'react-redux';
import { AnyAction, configureStore, Middleware } from '@reduxjs/toolkit';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { IntlProvider } from 'react-intl';

import { HighlightsFeed } from '../HighlightsFeed';
import highlightsReducer, {
  loadHighlights,
  loadHighlightsTemplatesTitles,
  setHighlightsFilters,
} from '../../../redux/highlights/slice';
import { EHighlightsDateFilter } from '../../../types/highlights';
import { ELocale } from '../../../types/redux';
import { enMessages } from '../../../lang/locales/en_US';

jest.unmock('react-redux');

const TIMEZONE = 'Asia/Yekaterinburg';

const MIDDAY_IN_ZONE = '2024-11-27T10:03:00.000Z';

const START_OF_TODAY_IN_ZONE = '2024-11-26T19:00:00.000Z';
const END_OF_TODAY_IN_ZONE = '2024-11-27T18:59:59.000Z';

let nowSpy: jest.SpyInstance;

const renderFeed = (timeRange = EHighlightsDateFilter.Today) => {
  const dispatched: AnyAction[] = [];
  const recordActions: Middleware = () => (next) => (action) => {
    dispatched.push(action as AnyAction);

    return next(action);
  };

  const store = configureStore({
    reducer: {
      highlights: highlightsReducer,
      authUser: () => ({ timezone: TIMEZONE, language: ELocale.English, dateFdw: '1' }),
      accounts: () => ({ users: [] }),
      workflows: () => ({ workflowLog: { isLoading: false, workflowId: null } }),
    },
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware({ serializableCheck: false, immutableCheck: false }).concat(recordActions),
  });

  store.dispatch(
    setHighlightsFilters({
      timeRange,
      startDate: new Date('2024-11-25T00:00:00.000Z'),
      endDate: new Date('2024-11-25T23:59:59.999Z'),
    }),
  );
  dispatched.length = 0;

  render(
    <Provider store={store}>
      <IntlProvider locale="en" messages={enMessages as unknown as Record<string, string>}>
        <HighlightsFeed />
      </IntlProvider>
    </Provider>,
  );

  const getFiltersPayloads = () => dispatched.filter(setHighlightsFilters.match).map(({ payload }) => payload);

  return { dispatched, getFiltersPayloads };
};

describe('HighlightsFeed date filters', () => {
  beforeAll(() => {
    nowSpy = jest.spyOn(Date, 'now');
  });

  beforeEach(() => {
    nowSpy.mockReturnValue(new Date(MIDDAY_IN_ZONE).getTime());
  });

  afterAll(() => {
    nowSpy.mockRestore();
  });

  it('recomputes the active preset in the profile timezone before the first fetch', () => {
    const { dispatched } = renderFeed();

    const rangeIndex = dispatched.findIndex(
      (action) =>
        setHighlightsFilters.match(action) &&
        action.payload.startDate?.toISOString() === START_OF_TODAY_IN_ZONE &&
        action.payload.endDate?.toISOString() === END_OF_TODAY_IN_ZONE,
    );
    const fetchIndex = dispatched.findIndex(
      (action) => loadHighlights.match(action) && action.payload.onScroll === true,
    );

    expect(rangeIndex).toBeGreaterThanOrEqual(0);
    expect(fetchIndex).toBeGreaterThan(rangeIndex);
  });

  it('requests template titles last with the corrected range', () => {
    const { dispatched } = renderFeed();

    const titlesRequests = dispatched.filter(loadHighlightsTemplatesTitles.match);

    expect(titlesRequests[titlesRequests.length - 1].payload).toEqual({
      eventDateFrom: new Date(START_OF_TODAY_IN_ZONE),
      eventDateTo: new Date(END_OF_TODAY_IN_ZONE),
    });
  });

  it('keeps a Custom range untouched on mount', () => {
    const { getFiltersPayloads } = renderFeed(EHighlightsDateFilter.Custom);

    expect(getFiltersPayloads()).toEqual([]);
  });

  it('applies the profile timezone and the profile week start when a preset is picked', () => {
    const { dispatched, getFiltersPayloads } = renderFeed();
    dispatched.length = 0;

    userEvent.click(screen.getByLabelText(enMessages['process-highlights.date-picker-week']));

    expect(getFiltersPayloads()).toEqual([
      {
        timeRange: EHighlightsDateFilter.Week,
        startDate: new Date('2024-11-24T19:00:00.000Z'),
        endDate: new Date('2024-12-01T18:59:59.000Z'),
      },
    ]);
  });

  it('closes a preset range on a whole second, like the date picker', () => {
    const { dispatched, getFiltersPayloads } = renderFeed();
    dispatched.length = 0;

    userEvent.click(screen.getByLabelText(enMessages['process-highlights.date-picker-yesterday']));

    const [{ startDate, endDate }] = getFiltersPayloads();

    expect(startDate?.toISOString()).toBe('2024-11-25T19:00:00.000Z');
    expect(endDate?.toISOString()).toBe('2024-11-26T18:59:59.000Z');
    expect(endDate?.getMilliseconds()).toBe(0);
  });

  it('switches to Custom without overwriting the picked range', () => {
    const { dispatched, getFiltersPayloads } = renderFeed();
    dispatched.length = 0;

    userEvent.click(screen.getByLabelText(enMessages['process-highlights.date-picker-custom']));

    expect(getFiltersPayloads()).toEqual([{ timeRange: EHighlightsDateFilter.Custom }]);
  });
});
