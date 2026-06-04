import { parseMarkdownToFiles } from '../parseMarkdownFiles';

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
    it('parses a single markdown link', () => {
      const input = '[document.pdf](https://files.example.com/abc-123)';

      const result = parseMarkdownToFiles(input);

      expect(result).toEqual([
        {
          id: 'abc-123',
          name: 'document.pdf',
          url: 'https://files.example.com/abc-123',
          size: 0,
        },
      ]);
    });

    it('extracts file id from last URL segment', () => {
      const input = '[file.txt](https://storage.pneumatic.app/files/uploads/550e8400-e29b-41d4-a716-446655440000)';

      const result = parseMarkdownToFiles(input);

      expect(result[0].id).toBe('550e8400-e29b-41d4-a716-446655440000');
    });
  });

  describe('multiple files parsing', () => {
    it('parses multiple comma-separated markdown links', () => {
      const input =
        '[doc.pdf](https://files.example.com/aaa), [photo.jpg](https://files.example.com/bbb)';

      const result = parseMarkdownToFiles(input);

      expect(result).toHaveLength(2);
      expect(result[0].name).toBe('doc.pdf');
      expect(result[0].url).toBe('https://files.example.com/aaa');
      expect(result[1].name).toBe('photo.jpg');
      expect(result[1].url).toBe('https://files.example.com/bbb');
    });

    it('parses three files', () => {
      const input = [
        '[a.pdf](https://files.example.com/1)',
        '[b.png](https://files.example.com/2)',
        '[c.docx](https://files.example.com/3)',
      ].join(', ');

      const result = parseMarkdownToFiles(input);

      expect(result).toHaveLength(3);
      expect(result.map((f) => f.name)).toEqual(['a.pdf', 'b.png', 'c.docx']);
    });
  });

  describe('edge cases', () => {
    it('handles filenames with spaces', () => {
      const input = '[my document file.pdf](https://files.example.com/abc)';

      const result = parseMarkdownToFiles(input);

      expect(result[0].name).toBe('my document file.pdf');
    });

    it('handles filenames with parentheses', () => {
      const input = '[file (copy).pdf](https://files.example.com/abc)';

      const result = parseMarkdownToFiles(input);

      expect(result[0].name).toBe('file (copy).pdf');
    });

    it('handles filenames with special characters', () => {
      const input = '[отчёт_2024.pdf](https://files.example.com/abc)';

      const result = parseMarkdownToFiles(input);

      expect(result[0].name).toBe('отчёт_2024.pdf');
    });

    it('returns empty array for plain text without markdown links', () => {
      expect(parseMarkdownToFiles('just some text')).toEqual([]);
    });

    it('returns empty array for malformed markdown', () => {
      expect(parseMarkdownToFiles('[name only')).toEqual([]);
      expect(parseMarkdownToFiles('(url only)')).toEqual([]);
    });

    it('sets size to 0 for all parsed files', () => {
      const input = '[a.pdf](https://x.com/1), [b.pdf](https://x.com/2)';

      const result = parseMarkdownToFiles(input);

      result.forEach((file) => {
        expect(file.size).toBe(0);
      });
    });

    it('handles URL without path segments (uses full URL as id)', () => {
      const input = '[file.txt](https://example.com)';

      const result = parseMarkdownToFiles(input);

      expect(result[0].id).toBe('example.com');
    });
  });
});
