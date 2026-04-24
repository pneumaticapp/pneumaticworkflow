import { ECustomEditorEntities } from '../types';
import { getAttachmentEntityType } from '../getAttachmentEntityType';

jest.mock('../../../Attachments/utils/getAttachmentType', () => ({
  getAttachmentTypeByUrl: jest.fn(),
}));

const {
  getAttachmentTypeByUrl,
}: { getAttachmentTypeByUrl: jest.Mock } = require('../../../Attachments/utils/getAttachmentType');

describe('getAttachmentEntityType', () => {
  beforeEach(() => {
    getAttachmentTypeByUrl.mockReset();
  });

  it('returns File when getAttachmentTypeByUrl returns null', () => {
    getAttachmentTypeByUrl.mockReturnValue(null);
    expect(getAttachmentEntityType('https://example.com/file.xyz')).toBe(
      ECustomEditorEntities.File,
    );
  });

  it('returns File when type is file', () => {
    getAttachmentTypeByUrl.mockReturnValue('file');
    expect(getAttachmentEntityType('https://example.com/doc.pdf')).toBe(
      ECustomEditorEntities.File,
    );
  });

  it('returns Image when type is image', () => {
    getAttachmentTypeByUrl.mockReturnValue('image');
    expect(getAttachmentEntityType('https://example.com/photo.jpg')).toBe(
      ECustomEditorEntities.Image,
    );
  });

  it('returns Video when type is video', () => {
    getAttachmentTypeByUrl.mockReturnValue('video');
    expect(getAttachmentEntityType('https://example.com/video.mp4')).toBe(
      ECustomEditorEntities.Video,
    );
  });

  it('calls getAttachmentTypeByUrl with the given url', () => {
    getAttachmentTypeByUrl.mockReturnValue('file');
    getAttachmentEntityType('https://storage.example.com/abc.pdf');
    expect(getAttachmentTypeByUrl).toHaveBeenCalledWith(
      'https://storage.example.com/abc.pdf',
    );
  });

  describe('edge cases', () => {
    it('returns File for empty url string when getAttachmentTypeByUrl returns null', () => {
      getAttachmentTypeByUrl.mockReturnValue(null);
      expect(getAttachmentEntityType('')).toBe(ECustomEditorEntities.File);
      expect(getAttachmentTypeByUrl).toHaveBeenCalledWith('');
    });

    it('returns File for unknown type in entitiesMap', () => {
      getAttachmentTypeByUrl.mockReturnValue('file');
      expect(getAttachmentEntityType('https://example.com/file.xyz')).toBe(
        ECustomEditorEntities.File,
      );
    });
  });
});
