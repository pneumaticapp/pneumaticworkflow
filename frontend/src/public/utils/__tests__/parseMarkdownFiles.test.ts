import { parseMarkdownToFiles } from '../parseMarkdownFiles';

const FILE_SERVICE_URL = 'https://app.pneumatic.app/files';

jest.mock('../getConfig', () => ({
  getBrowserConfigEnv: () => ({
    api: {
      fileServiceUrl: FILE_SERVICE_URL,
    },
  }),
}));

describe('parseMarkdownToFiles', () => {
  describe('null/undefined/empty handling', () => {
    it('returns empty array for null', () => {
      expect(parseMarkdownToFiles(null)).toEqual([]);
    });

    it('returns empty array for undefined', () => {
      expect(parseMarkdownToFiles(undefined)).toEqual([]);
    });

    it('returns empty array for empty string', () => {
      expect(parseMarkdownToFiles('')).toEqual([]);
    });
  });

  describe('single file parsing', () => {
    it('parses a single file-service markdown link', () => {
      const input = `[document.pdf](${FILE_SERVICE_URL}/abc-123)`;

      const result = parseMarkdownToFiles(input);

      expect(result).toEqual([
        {
          id: 'abc-123',
          name: 'document.pdf',
          url: `${FILE_SERVICE_URL}/abc-123`,
          size: 0,
          thumbnailUrl: undefined,
        },
      ]);
    });

    it('extracts file id from last URL segment', () => {
      const input = `[file.txt](${FILE_SERVICE_URL}/550e8400-e29b-41d4-a716-446655440000)`;

      const result = parseMarkdownToFiles(input);

      expect(result[0].id).toBe('550e8400-e29b-41d4-a716-446655440000');
    });
  });

  describe('multiple files parsing', () => {
    it('parses multiple comma-separated file-service links', () => {
      const input =
        `[doc.pdf](${FILE_SERVICE_URL}/aaa), [photo.jpg](${FILE_SERVICE_URL}/bbb)`;

      const result = parseMarkdownToFiles(input);

      expect(result).toHaveLength(2);
      expect(result[0].name).toBe('doc.pdf');
      expect(result[0].url).toBe(`${FILE_SERVICE_URL}/aaa`);
      expect(result[0].thumbnailUrl).toBeUndefined();
      expect(result[1].name).toBe('photo.jpg');
      expect(result[1].url).toBe(`${FILE_SERVICE_URL}/bbb`);
      expect(result[1].thumbnailUrl).toBe(`${FILE_SERVICE_URL}/bbb`);
    });

    it('parses three files', () => {
      const input = [
        `[a.pdf](${FILE_SERVICE_URL}/1)`,
        `[b.png](${FILE_SERVICE_URL}/2)`,
        `[c.docx](${FILE_SERVICE_URL}/3)`,
      ].join(', ');

      const result = parseMarkdownToFiles(input);

      expect(result).toHaveLength(3);
      expect(result.map((f) => f.name)).toEqual(['a.pdf', 'b.png', 'c.docx']);
    });
  });

  describe('domain filtering', () => {
    it('ignores external links (Google Docs)', () => {
      const input = '[Spreadsheet](https://docs.google.com/spreadsheets/d/abc123)';

      const result = parseMarkdownToFiles(input);

      expect(result).toEqual([]);
    });

    it('ignores links to other domains', () => {
      const input = '[External](https://example.com/files/abc-123)';

      const result = parseMarkdownToFiles(input);

      expect(result).toEqual([]);
    });

    it('filters mixed links — keeps only file-service URLs', () => {
      const input = [
        `[uploaded.pdf](${FILE_SERVICE_URL}/abc-123)`,
        '[Google Doc](https://docs.google.com/doc/xyz)',
        `[photo.jpg](${FILE_SERVICE_URL}/def-456)`,
        '[Wiki](https://en.wikipedia.org/wiki/Test)',
      ].join(', ');

      const result = parseMarkdownToFiles(input);

      expect(result).toHaveLength(2);
      expect(result[0].name).toBe('uploaded.pdf');
      expect(result[0].id).toBe('abc-123');
      expect(result[1].name).toBe('photo.jpg');
      expect(result[1].id).toBe('def-456');
    });

    it('does not match partial domain prefix', () => {
      const input = '[file.pdf](https://app.pneumatic.app/files-evil/abc)';

      const result = parseMarkdownToFiles(input);

      expect(result).toEqual([]);
    });
  });

  describe('edge cases', () => {
    it('handles filenames with spaces', () => {
      const input = `[my document file.pdf](${FILE_SERVICE_URL}/abc)`;

      const result = parseMarkdownToFiles(input);

      expect(result[0].name).toBe('my document file.pdf');
    });

    it('handles filenames with special characters', () => {
      const input = `[report_(Q1)_2024.pdf](${FILE_SERVICE_URL}/abc)`;

      const result = parseMarkdownToFiles(input);

      expect(result[0].name).toBe('report_(Q1)_2024.pdf');
    });

    it('returns empty array for plain text without markdown links', () => {
      expect(parseMarkdownToFiles('just some text')).toEqual([]);
    });

    it('returns empty array for malformed markdown', () => {
      expect(parseMarkdownToFiles('[name only')).toEqual([]);
      expect(parseMarkdownToFiles('(url only)')).toEqual([]);
    });

    it('sets size to 0 for all parsed files', () => {
      const input = `[a.pdf](${FILE_SERVICE_URL}/1), [b.pdf](${FILE_SERVICE_URL}/2)`;

      const result = parseMarkdownToFiles(input);

      result.forEach((file) => {
        expect(file.size).toBe(0);
      });
    });
  });

  describe('URL cleaning', () => {
    it('strips query parameters from file URL', () => {
      const input = `[file.pdf](${FILE_SERVICE_URL}/abc-123?token=xyz&v=2)`;

      const result = parseMarkdownToFiles(input);

      expect(result[0].id).toBe('abc-123');
    });

    it('strips hash fragment from file URL', () => {
      const input = `[file.pdf](${FILE_SERVICE_URL}/abc-123#section)`;

      const result = parseMarkdownToFiles(input);

      expect(result[0].id).toBe('abc-123');
    });

    it('strips both query and hash from file URL', () => {
      const input = `[file.pdf](${FILE_SERVICE_URL}/abc-123?token=x#top)`;

      const result = parseMarkdownToFiles(input);

      expect(result[0].id).toBe('abc-123');
    });

    it('preserves original URL with query in the url field', () => {
      const fullUrl = `${FILE_SERVICE_URL}/abc-123?token=xyz`;
      const input = `[file.pdf](${fullUrl})`;

      const result = parseMarkdownToFiles(input);

      expect(result[0].url).toBe(fullUrl);
      expect(result[0].id).toBe('abc-123');
    });
  });

  describe('thumbnailUrl detection', () => {
    it.each([
      ['photo.jpg', true],
      ['image.jpeg', true],
      ['logo.png', true],
      ['icon.gif', true],
      ['vector.svg', true],
      ['banner.webp', true],
      ['IMAGE.JPG', true],
      ['photo.PNG', true],
    ])('sets thumbnailUrl for image file %s', (filename, _isImage) => {
      const input = `[${filename}](${FILE_SERVICE_URL}/abc-123)`;

      const result = parseMarkdownToFiles(input);

      expect(result[0].thumbnailUrl).toBe(`${FILE_SERVICE_URL}/abc-123`);
    });

    it.each([
      ['document.pdf'],
      ['report.docx'],
      ['data.xlsx'],
      ['archive.zip'],
      ['script.js'],
      ['readme.txt'],
    ])('does not set thumbnailUrl for non-image file %s', (filename) => {
      const input = `[${filename}](${FILE_SERVICE_URL}/abc-123)`;

      const result = parseMarkdownToFiles(input);

      expect(result[0].thumbnailUrl).toBeUndefined();
    });

    it('sets thumbnailUrl only for image files in mixed list', () => {
      const input = [
        `[report.pdf](${FILE_SERVICE_URL}/1)`,
        `[photo.jpg](${FILE_SERVICE_URL}/2)`,
        `[data.csv](${FILE_SERVICE_URL}/3)`,
        `[logo.png](${FILE_SERVICE_URL}/4)`,
      ].join(', ');

      const result = parseMarkdownToFiles(input);

      expect(result[0].thumbnailUrl).toBeUndefined();
      expect(result[1].thumbnailUrl).toBe(`${FILE_SERVICE_URL}/2`);
      expect(result[2].thumbnailUrl).toBeUndefined();
      expect(result[3].thumbnailUrl).toBe(`${FILE_SERVICE_URL}/4`);
    });

    it('handles image filename with underscores and thumbnailUrl', () => {
      const input = `[photo_report-final.jpg](${FILE_SERVICE_URL}/abc)`;

      const result = parseMarkdownToFiles(input);

      expect(result[0].thumbnailUrl).toBe(`${FILE_SERVICE_URL}/abc`);
    });
  });
});
