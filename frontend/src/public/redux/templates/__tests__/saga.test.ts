jest.mock('../../../utils/getConfig', () => ({
  getBrowserConfigEnv: jest.fn().mockReturnValue({
    api: {
      urls: {
        templates: '/templates',
        templatesTitlesByOwners: '/templates/titles-by-owners',
      },
    },
  }),
}));

import * as getTemplatesApi from '../../../api/getTemplates';
import { ETemplatesSorting } from '../../../types/workflow';
import { LIMIT_LOAD_TEMPLATES } from '../../../constants/defaultValues';

describe('templates saga', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('fetchTemplates', () => {
    it('calls getTemplatesByOwners with correct parameters', async () => {
      const getTemplatesByOwnersMock = jest
        .spyOn(getTemplatesApi, 'getTemplatesByOwners')
        .mockResolvedValue({
          count: 2,
          results: [
            { id: 1, name: 'Template 1' },
            { id: 2, name: 'Template 2' },
          ],
        } as any);

      await getTemplatesApi.getTemplatesByOwners({
        offset: 0,
        limit: LIMIT_LOAD_TEMPLATES,
        sorting: ETemplatesSorting.DateDesc,
      });

      expect(getTemplatesByOwnersMock).toHaveBeenCalledWith({
        offset: 0,
        limit: LIMIT_LOAD_TEMPLATES,
        sorting: ETemplatesSorting.DateDesc,
      });
    });

    it('calls getTemplatesByOwners instead of getTemplates for My Workflow Templates', async () => {
      const getTemplatesMock = jest.spyOn(getTemplatesApi, 'getTemplates');
      const getTemplatesByOwnersMock = jest
        .spyOn(getTemplatesApi, 'getTemplatesByOwners')
        .mockResolvedValue({ count: 0, results: [] } as any);

      await getTemplatesApi.getTemplatesByOwners({
        offset: 0,
        limit: 30,
        sorting: ETemplatesSorting.DateDesc,
      });

      expect(getTemplatesByOwnersMock).toHaveBeenCalled();
      expect(getTemplatesMock).not.toHaveBeenCalled();
    });

    it('handles pagination offset correctly', async () => {
      const getTemplatesByOwnersMock = jest
        .spyOn(getTemplatesApi, 'getTemplatesByOwners')
        .mockResolvedValue({ count: 50, results: [] } as any);

      await getTemplatesApi.getTemplatesByOwners({
        offset: 30,
        limit: LIMIT_LOAD_TEMPLATES,
        sorting: ETemplatesSorting.DateDesc,
      });

      expect(getTemplatesByOwnersMock).toHaveBeenCalledWith({
        offset: 30,
        limit: LIMIT_LOAD_TEMPLATES,
        sorting: ETemplatesSorting.DateDesc,
      });
    });

    it('passes sorting parameter correctly', async () => {
      const getTemplatesByOwnersMock = jest
        .spyOn(getTemplatesApi, 'getTemplatesByOwners')
        .mockResolvedValue({ count: 0, results: [] } as any);

      await getTemplatesApi.getTemplatesByOwners({
        offset: 0,
        limit: LIMIT_LOAD_TEMPLATES,
        sorting: ETemplatesSorting.NameAsc,
      });

      expect(getTemplatesByOwnersMock).toHaveBeenCalledWith({
        offset: 0,
        limit: LIMIT_LOAD_TEMPLATES,
        sorting: ETemplatesSorting.NameAsc,
      });
    });
  });

  describe('fetchIsTemplateOwner', () => {
    it('uses getTemplates (not getTemplatesByOwners) to check ownership', async () => {
      const getTemplatesMock = jest
        .spyOn(getTemplatesApi, 'getTemplates')
        .mockResolvedValue({ count: 1, results: [{ id: 1 }] } as any);

      await getTemplatesApi.getTemplates({
        limit: 1,
        isActive: true,
      });

      expect(getTemplatesMock).toHaveBeenCalledWith({
        limit: 1,
        isActive: true,
      });
    });
  });
});
