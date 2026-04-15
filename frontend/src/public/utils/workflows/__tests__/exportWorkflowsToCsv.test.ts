import {
  buildWorkflowsCsvBlob,
  downloadWorkflowsCsv,
  encodeWorkflowRowsToCsvString,
  escapeCsvCell,
  WORKFLOWS_CSV_DEFAULT_FILENAME,
  WORKFLOWS_CSV_MIME,
} from '../exportWorkflowsToCsv';

function readBlobAsUint8Array(blob: Blob): Promise<Uint8Array> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(new Uint8Array(reader.result as ArrayBuffer));
    reader.onerror = () => reject(reader.error);
    reader.readAsArrayBuffer(blob);
  });
}

describe('exportWorkflowsToCsv', () => {
  describe('escapeCsvCell', () => {
    it('returns plain value when no special characters', () => {
      expect(escapeCsvCell('hello')).toBe('hello');
    });

    it('wraps and escapes double quotes', () => {
      expect(escapeCsvCell('say "hi"')).toBe('"say ""hi"""');
    });

    it('wraps values containing comma', () => {
      expect(escapeCsvCell('a,b')).toBe('"a,b"');
    });

    it('wraps values containing newline', () => {
      expect(escapeCsvCell('line1\nline2')).toBe('"line1\nline2"');
    });

    it('wraps values containing carriage return', () => {
      expect(escapeCsvCell('a\rb')).toBe('"a\rb"');
    });
  });

  describe('encodeWorkflowRowsToCsvString', () => {
    it('joins rows with CRLF and cells with comma', () => {
      const csv = encodeWorkflowRowsToCsvString([
        ['A', 'B'],
        ['1', '2'],
      ]);
      expect(csv).toBe('A,B\r\n1,2');
    });

    it('escapes cells that need quoting', () => {
      const csv = encodeWorkflowRowsToCsvString([['a,b', 'plain']]);
      expect(csv).toBe('"a,b",plain');
    });
  });

  describe('buildWorkflowsCsvBlob', () => {
    it('includes UTF-8 BOM and sets csv mime type', async () => {
      const blob = buildWorkflowsCsvBlob([['X']]);
      expect(blob.type).toBe(WORKFLOWS_CSV_MIME);
      const u8 = await readBlobAsUint8Array(blob);
      expect(u8[0]).toBe(0xef);
      expect(u8[1]).toBe(0xbb);
      expect(u8[2]).toBe(0xbf);
      const body = Buffer.from(u8.subarray(3)).toString('utf8');
      expect(body).toBe('X');
    });
  });

  describe('downloadWorkflowsCsv', () => {
    it('creates csv blob and triggers download', async () => {
      const createObjectURL = jest.fn(() => 'blob:mock-url');
      const revokeObjectURL = jest.fn();
      const click = jest.fn();

      const originalCreateObjectURL = URL.createObjectURL;
      const originalRevokeObjectURL = URL.revokeObjectURL;
      URL.createObjectURL = createObjectURL;
      URL.revokeObjectURL = revokeObjectURL;

      const mockLink = {
        setAttribute: jest.fn(),
        style: {},
        click,
      };
      const createElement = jest.spyOn(document, 'createElement').mockImplementation((tag: string) => {
        if (tag === 'a') return mockLink as unknown as HTMLAnchorElement;
        return document.createElement(tag);
      });
      jest.spyOn(document.body, 'appendChild').mockImplementation(() => mockLink as never);
      jest.spyOn(document.body, 'removeChild').mockImplementation(() => mockLink as never);

      downloadWorkflowsCsv(
        [
          ['H1', 'H2'],
          ['v1', 'v2'],
        ],
        'custom.csv',
      );

      expect(createObjectURL).toHaveBeenCalledTimes(1);
      const blob = (createObjectURL as jest.Mock).mock.calls[0][0] as Blob;
      expect(blob.type).toBe(WORKFLOWS_CSV_MIME);
      const u8 = await readBlobAsUint8Array(blob);
      expect(u8[0]).toBe(0xef);
      expect(u8[1]).toBe(0xbb);
      expect(u8[2]).toBe(0xbf);
      const csvBody = Buffer.from(u8.subarray(3)).toString('utf8');
      expect(csvBody).toBe('H1,H2\r\nv1,v2');

      expect(mockLink.setAttribute).toHaveBeenCalledWith('href', 'blob:mock-url');
      expect(mockLink.setAttribute).toHaveBeenCalledWith('download', 'custom.csv');
      expect(click).toHaveBeenCalled();
      expect(revokeObjectURL).toHaveBeenCalledWith('blob:mock-url');

      createElement.mockRestore();
      URL.createObjectURL = originalCreateObjectURL;
      URL.revokeObjectURL = originalRevokeObjectURL;
    });

    it('uses default filename when omitted', async () => {
      const createObjectURL = jest.fn(() => 'blob:mock-url');
      const mockLink = { setAttribute: jest.fn(), style: {}, click: jest.fn() };
      const originalCreateObjectURL = URL.createObjectURL;
      const originalRevokeObjectURL = URL.revokeObjectURL;
      URL.createObjectURL = createObjectURL;
      URL.revokeObjectURL = jest.fn();
      jest.spyOn(document, 'createElement').mockImplementation((tag: string) => {
        if (tag === 'a') return mockLink as unknown as HTMLAnchorElement;
        return document.createElement(tag);
      });
      jest.spyOn(document.body, 'appendChild').mockImplementation(() => mockLink as never);
      jest.spyOn(document.body, 'removeChild').mockImplementation(() => mockLink as never);

      downloadWorkflowsCsv([['A']]);

      expect(mockLink.setAttribute).toHaveBeenCalledWith('download', WORKFLOWS_CSV_DEFAULT_FILENAME);

      URL.createObjectURL = originalCreateObjectURL;
      URL.revokeObjectURL = originalRevokeObjectURL;
    });
  });
});
