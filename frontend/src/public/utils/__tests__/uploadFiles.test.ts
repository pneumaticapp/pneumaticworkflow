/* eslint-disable */
/* prettier-ignore */
import { getThumbnail } from '../uploadFiles';

describe('uploadFiles', () => {
  describe('getThumbnail', () => {
    it('returns null if uploaded file is not image', async () => {
      const mockTextFile = new File(['file contents'], 'fileName.txt', { type:  'text/plain'});

      const thumbnail = await getThumbnail(mockTextFile);

      expect(thumbnail).toBe(null);
    });
  });
});
