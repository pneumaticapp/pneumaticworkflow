// <reference types="jest" />
import {
  activateVacation,
  deactivateVacation,
} from '../vacation';
import { commonRequest } from '../commonRequest';

jest.mock('../commonRequest', () => ({
  commonRequest: jest.fn(),
}));

jest.mock('../../utils/mappers', () => ({
  mapRequestBody: jest.fn((body) => body),
}));

describe('vacation API', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('activateVacation', () => {
    it('отправляет POST с substitute_user_ids', () => {
      const body = {
        substituteUserIds: [10, 20],
        vacationStartDate: '2026-04-01',
        vacationEndDate: '2026-04-15',
      };

      activateVacation(body);

      expect(commonRequest).toHaveBeenCalledTimes(
        1,
      );
      expect(commonRequest).toHaveBeenCalledWith(
        'vacationActivate',
        {
          data: body,
          method: 'POST',
        },
      );
    });
  });

  describe('deactivateVacation', () => {
    it('отправляет DELETE без body', () => {
      deactivateVacation();

      expect(commonRequest).toHaveBeenCalledTimes(
        1,
      );
      expect(commonRequest).toHaveBeenCalledWith(
        'vacationDeactivate',
        {
          method: 'DELETE',
        },
      );
    });
  });
});
