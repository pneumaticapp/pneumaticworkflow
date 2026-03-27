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

jest.mock('../../utils/getConfig', () => ({
  getBrowserConfigEnv: () => ({
    api: {
      urls: {
        vacationActivate: '/accounts/user/activate-vacation',
        vacationDeactivate: '/accounts/user/deactivate-vacation',
        vacationUserActivate: '/accounts/users/:id/activate-vacation',
        vacationUserDeactivate: '/accounts/users/:id/deactivate-vacation',
      },
    },
  }),
}));

describe('vacation API', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('activateVacation', () => {
    it('отправляет POST на свой URL без userId', () => {
      const body = {
        substituteUserIds: [10, 20],
        vacationStartDate: '2026-04-01',
        vacationEndDate: '2026-04-15',
      };

      activateVacation(body);

      expect(commonRequest).toHaveBeenCalledTimes(1);
      expect(commonRequest).toHaveBeenCalledWith(
        '/accounts/user/activate-vacation',
        {
          data: body,
          method: 'POST',
        },
      );
    });

    it('отправляет POST на URL другого пользователя с userId', () => {
      const body = {
        substituteUserIds: [10],
        vacationStartDate: '2026-04-01',
        vacationEndDate: '2026-04-15',
      };

      activateVacation(body, 42);

      expect(commonRequest).toHaveBeenCalledTimes(1);
      expect(commonRequest).toHaveBeenCalledWith(
        '/accounts/users/42/activate-vacation',
        {
          data: body,
          method: 'POST',
        },
      );
    });
  });

  describe('deactivateVacation', () => {
    it('отправляет POST без body на свой URL', () => {
      deactivateVacation();

      expect(commonRequest).toHaveBeenCalledTimes(1);
      expect(commonRequest).toHaveBeenCalledWith(
        '/accounts/user/deactivate-vacation',
        {
          method: 'POST',
        },
      );
    });

    it('отправляет POST на URL другого пользователя с userId', () => {
      deactivateVacation(42);

      expect(commonRequest).toHaveBeenCalledTimes(1);
      expect(commonRequest).toHaveBeenCalledWith(
        '/accounts/users/42/deactivate-vacation',
        {
          method: 'POST',
        },
      );
    });
  });
});
