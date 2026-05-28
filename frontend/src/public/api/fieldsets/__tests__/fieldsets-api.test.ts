
const MOCK_URLS = {
  templateFieldsets: '/templates/:id/fieldsets',
  fieldset: '/fieldsets/:id',
};

jest.mock('../../../utils/getConfig', () => ({
  getBrowserConfigEnv: jest.fn().mockReturnValue({
    api: { urls: MOCK_URLS },
  }),
}));

jest.mock('../../commonRequest');

jest.mock('../../../utils/mappers', () => ({
  mapRequestBody: jest.fn((obj: object) => JSON.stringify(obj)),
}));

import { commonRequest } from '../../commonRequest';
import { mapRequestBody } from '../../../utils/mappers';
import { createFieldset } from '../createFieldset';
import { getFieldset } from '../getFieldset';
import { getFieldsets } from '../getFieldsets';
import { updateFieldset } from '../updateFieldset';
import { deleteFieldset } from '../deleteFieldset';
import { EFieldsetsSorting } from '../../../types/fieldset';

describe('fieldsets API clients', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('createFieldset', () => {
    it('calls commonRequest with POST, correct URL and body via mapRequestBody', async () => {
      const mockResponse = { id: 1, name: 'Test' };
      (commonRequest as jest.Mock).mockResolvedValue(mockResponse);

      const params = {
        templateId: 42,
        name: 'New Fieldset',
        description: 'Desc',
        rules: [],
        fields: [],
      };

      const result = await createFieldset(params);

      expect(commonRequest).toHaveBeenCalledTimes(1);
      expect(commonRequest).toHaveBeenCalledWith(
        '/templates/42/fieldsets',
        {
          method: 'POST',
          data: expect.any(String),
        },
        { shouldThrow: true },
      );

      expect(mapRequestBody).toHaveBeenCalledTimes(1);
      expect(mapRequestBody).toHaveBeenCalledWith({
        name: 'New Fieldset',
        description: 'Desc',
        rules: [],
        fields: [],
      });

      expect(result).toBe(mockResponse);
    });
  });

  describe('getFieldset', () => {
    it('calls commonRequest with GET, correct URL and signal in requestOptions', async () => {
      const mockResponse = { id: 5, name: 'My Fieldset' };
      (commonRequest as jest.Mock).mockResolvedValue(mockResponse);

      const abortController = new AbortController();
      const result = await getFieldset({ id: 5, signal: abortController.signal });

      expect(commonRequest).toHaveBeenCalledTimes(1);
      expect(commonRequest).toHaveBeenCalledWith(
        '/fieldsets/5',
        {
          method: 'GET',
          signal: abortController.signal,
        },
        { shouldThrow: true },
      );
      expect(result).toBe(mockResponse);
    });
  });

  describe('getFieldsets', () => {
    it('builds URL without query params when ordering/limit/offset are absent', async () => {
      (commonRequest as jest.Mock).mockResolvedValue({ count: 0, results: [] });

      await getFieldsets({ templateId: 10 });

      expect(commonRequest).toHaveBeenCalledTimes(1);
      expect(commonRequest).toHaveBeenCalledWith(
        '/templates/10/fieldsets',
        expect.objectContaining({ method: 'GET' }),
        { shouldThrow: true },
      );
    });

    it('adds limit and offset to query string', async () => {
      (commonRequest as jest.Mock).mockResolvedValue({ count: 0, results: [] });

      await getFieldsets({ templateId: 10, limit: 30, offset: 0 });

      expect(commonRequest).toHaveBeenCalledTimes(1);
      const calledUrl = (commonRequest as jest.Mock).mock.calls[0][0] as string;
      expect(calledUrl).toContain('limit=30');
      expect(calledUrl).toContain('offset=0');
    });

    it.each([
      [EFieldsetsSorting.NameAsc, 'ordering=name'],
      [EFieldsetsSorting.NameDesc, 'ordering=-name'],
      [EFieldsetsSorting.DateAsc, 'ordering=date'],
      [EFieldsetsSorting.DateDesc, 'ordering=-date'],
    ])('maps %s to backend ordering %s', async (sorting, expected) => {
      (commonRequest as jest.Mock).mockResolvedValue({ count: 0, results: [] });

      await getFieldsets({ templateId: 10, ordering: sorting });

      expect(commonRequest).toHaveBeenCalledTimes(1);
      const calledUrl = (commonRequest as jest.Mock).mock.calls[0][0] as string;
      expect(calledUrl).toContain(expected);
    });

    it('passes unknown ordering as fallback', async () => {
      (commonRequest as jest.Mock).mockResolvedValue({ count: 0, results: [] });

      await getFieldsets({ templateId: 10, ordering: 'custom-sort' });

      expect(commonRequest).toHaveBeenCalledTimes(1);
      const calledUrl = (commonRequest as jest.Mock).mock.calls[0][0] as string;
      expect(calledUrl).toContain('ordering=custom-sort');
    });

    it('combines all params into one query string and passes signal', async () => {
      (commonRequest as jest.Mock).mockResolvedValue({ count: 0, results: [] });
      const abortController = new AbortController();

      await getFieldsets({
        templateId: 10,
        ordering: EFieldsetsSorting.DateDesc,
        limit: 20,
        offset: 40,
        signal: abortController.signal,
      });

      expect(commonRequest).toHaveBeenCalledTimes(1);

      const calledUrl = (commonRequest as jest.Mock).mock.calls[0][0] as string;
      expect(calledUrl).toContain('ordering=-date');
      expect(calledUrl).toContain('limit=20');
      expect(calledUrl).toContain('offset=40');

      expect(commonRequest).toHaveBeenCalledWith(
        calledUrl,
        expect.objectContaining({ signal: abortController.signal }),
        { shouldThrow: true },
      );
    });
  });

  describe('updateFieldset', () => {
    it('calls commonRequest with PATCH, id in URL, signal in requestOptions, data via mapRequestBody', async () => {
      const mockResponse = { id: 7, name: 'Updated' };
      (commonRequest as jest.Mock).mockResolvedValue(mockResponse);

      const abortController = new AbortController();
      const result = await updateFieldset({
        id: 7,
        name: 'Updated',
        description: 'New desc',
        signal: abortController.signal,
      });

      expect(commonRequest).toHaveBeenCalledTimes(1);
      expect(commonRequest).toHaveBeenCalledWith(
        '/fieldsets/7',
        {
          method: 'PATCH',
          data: expect.any(String),
          signal: abortController.signal,
        },
        { shouldThrow: true },
      );

      expect(mapRequestBody).toHaveBeenCalledTimes(1);
      expect(mapRequestBody).toHaveBeenCalledWith({
        name: 'Updated',
        description: 'New desc',
      });

      expect(result).toBe(mockResponse);
    });
  });

  describe('deleteFieldset', () => {
    it('calls commonRequest with DELETE, correct URL and responseType empty', async () => {
      (commonRequest as jest.Mock).mockResolvedValue(undefined);

      await deleteFieldset({ id: 99 });

      expect(commonRequest).toHaveBeenCalledTimes(1);
      expect(commonRequest).toHaveBeenCalledWith(
        '/fieldsets/99',
        { method: 'DELETE' },
        { shouldThrow: true, responseType: 'empty' },
      );
    });
  });
});
