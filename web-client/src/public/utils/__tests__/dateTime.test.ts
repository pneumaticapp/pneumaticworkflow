import {
  DELAY_TITLE_TEMPLATE,
  formatDelayRequest,
  formatDuration,
  getSeconds,
  parseDuration,
} from '../dateTime';

describe('dateTime', () => {
  const mockDuration = '12 05:30:00';
  const mockDurationWithoutDays = '00 00:12:00';
  const mockSplittedDuration = { days: 12, hours: 5, minutes: 120 };

  describe('parseDuration', () => {
    it('Parses duration from the back end correctly', () => {
      const result = parseDuration(mockDuration);
      const expected = { days: 12, hours: 5, minutes: 30 };

      expect(result).toEqual(expected);
    });
  });

  describe('getSeconds', () => {
    it('Returns correct seconds count', () => {
      const result = getSeconds(mockSplittedDuration);
      const expected = 1062000;

      expect(result).toEqual(expected);
    });
  });

  describe('formatDuration', () => {
    it('Formats duration correctly #1', () => {
      const result = formatDuration(mockDuration, DELAY_TITLE_TEMPLATE);
      const expected = '12d 5h 30m';

      expect(result).toEqual(expected);
    });
  });

  describe('formatDuration', () => {
    it('Formats duration correctly #2', () => {
      const result = formatDuration(mockDurationWithoutDays, DELAY_TITLE_TEMPLATE);
      const expected = '12m';

      expect(result).toEqual(expected);
    });
  });

  describe('formatDelayRequest', () => {
    it('Formats duration for the request correctly', () => {
      const result = formatDelayRequest(mockSplittedDuration);
      const expected = '12 07:00:00';

      expect(result).toEqual(expected);
    });
  });
});
