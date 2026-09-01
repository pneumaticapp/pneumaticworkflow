import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { IntlProvider } from 'react-intl';

import { HighlightsFeed, IHighlightsFeedProps } from '../HighlightsFeed';
import { EHighlightsDateFilter } from '../../../types/highlights';
import { enMessages } from '../../../lang/locales/en_US';
import { ELocale } from '../../../types/redux';

/** +05:00 all year: the profile timezone the reporter used, five hours ahead of the test clock. */
const TIMEZONE = 'Asia/Yekaterinburg';

jest.mock('react-redux', () => ({
  ...jest.requireActual('react-redux'),
  useSelector: (selector: (state: unknown) => unknown) =>
    selector({
      authUser: {
        timezone: TIMEZONE,
        language: ELocale.English,
        dateFdw: '1',
      },
    }),
}));

/** Wednesday, 27 Nov 2024, 15:03 in +05:00 — while the browser clock is still on 10:03 UTC. */
const MIDDAY_IN_ZONE = '2024-11-27T10:03:00.000Z';

const START_OF_TODAY_IN_ZONE = '2024-11-26T19:00:00.000Z';
const END_OF_TODAY_IN_ZONE = '2024-11-27T18:59:59.000Z';

let nowSpy: jest.SpyInstance;

const renderFeed = (props: Partial<IHighlightsFeedProps> = {}) => {
  const defaultProps: IHighlightsFeedProps = {
    count: 0,
    isFeedLoading: false,
    isTemplatesTitlesLoading: false,
    items: [],
    workflowId: null,
    users: [],
    templatesTitles: [],
    timeRange: EHighlightsDateFilter.Today,
    // A stale range, as the store holds it after the bundle has been loaded on the previous day.
    startDate: new Date('2024-11-25T00:00:00.000Z'),
    endDate: new Date('2024-11-25T23:59:59.999Z'),
    usersFilter: [],
    templatesFilter: [],
    filtersChanged: false,
    loadHighlights: jest.fn(),
    openWorkflowLogPopup: jest.fn(),
    resetHightlightsStore: jest.fn(),
    loadTemplatesTitles: jest.fn(),
    setFilters: jest.fn(),
    setFiltersChanged: jest.fn(),
    ...props,
  };

  render(
    <IntlProvider locale="en" messages={enMessages as unknown as Record<string, string>}>
      <HighlightsFeed {...defaultProps} />
    </IntlProvider>,
  );

  return defaultProps;
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
    const { setFilters, loadHighlights } = renderFeed();

    expect(setFilters).toHaveBeenCalledWith({
      startDate: new Date(START_OF_TODAY_IN_ZONE),
      endDate: new Date(END_OF_TODAY_IN_ZONE),
    });
    expect(loadHighlights).toHaveBeenCalledWith({ onScroll: true });
    expect((setFilters as jest.Mock).mock.invocationCallOrder[0]).toBeLessThan(
      (loadHighlights as jest.Mock).mock.invocationCallOrder[0],
    );
  });

  it('keeps a Custom range untouched on mount', () => {
    const { setFilters } = renderFeed({ timeRange: EHighlightsDateFilter.Custom });

    expect(setFilters).not.toHaveBeenCalled();
  });

  it('applies the profile timezone and the profile week start when a preset is picked', () => {
    const { setFilters } = renderFeed();
    (setFilters as jest.Mock).mockClear();

    userEvent.click(screen.getByLabelText(enMessages['process-highlights.date-picker-week']));

    // The profile starts weeks on Monday, so the range opens on Mon 25 Nov 00:00 +05:00.
    expect(setFilters).toHaveBeenCalledTimes(1);
    expect(setFilters).toHaveBeenCalledWith({
      timeRange: EHighlightsDateFilter.Week,
      startDate: new Date('2024-11-24T19:00:00.000Z'),
      endDate: new Date('2024-12-01T18:59:59.000Z'),
    });
  });

  it('closes a preset range on a whole second so it cannot round up into the next day', () => {
    const { setFilters } = renderFeed();
    (setFilters as jest.Mock).mockClear();

    userEvent.click(screen.getByLabelText(enMessages['process-highlights.date-picker-yesterday']));

    const [{ startDate, endDate }] = (setFilters as jest.Mock).mock.calls[0];

    expect(startDate.toISOString()).toBe('2024-11-25T19:00:00.000Z');
    expect(endDate.toISOString()).toBe('2024-11-26T18:59:59.000Z');
    expect(endDate.getMilliseconds()).toBe(0);
  });

  it('switches to Custom without overwriting the picked range', () => {
    const { setFilters } = renderFeed();
    (setFilters as jest.Mock).mockClear();

    userEvent.click(screen.getByLabelText(enMessages['process-highlights.date-picker-custom']));

    expect(setFilters).toHaveBeenCalledWith({ timeRange: EHighlightsDateFilter.Custom });
  });
});
