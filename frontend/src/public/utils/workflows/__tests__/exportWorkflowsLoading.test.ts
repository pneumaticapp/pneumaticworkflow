describe('workflow export dependencies', () => {
  afterEach(() => {
    jest.resetModules();
    jest.dontMock('exceljs');
  });

  it('loads the spreadsheet engine only when creating an XLSX file', async () => {
    const addRow = jest.fn();
    const writeBuffer = jest.fn().mockResolvedValue(new ArrayBuffer(8));
    const loadExcel = jest.fn(() => ({
      Workbook: jest.fn().mockImplementation(() => ({
        addWorksheet: jest.fn().mockReturnValue({ addRow }),
        xlsx: { writeBuffer },
      })),
    }));
    jest.resetModules();
    jest.doMock('exceljs', loadExcel);

    const { buildWorkflowsXlsxBuffer } = await import('../exportWorkflowsToExcel');
    expect(loadExcel).not.toHaveBeenCalled();

    const rows = [['Name'], ['Workflow One']];
    const buffer = await buildWorkflowsXlsxBuffer(rows);

    expect(loadExcel).toHaveBeenCalledTimes(1);
    expect(addRow.mock.calls).toEqual(rows.map((row) => [row]));
    expect(writeBuffer).toHaveBeenCalledTimes(1);
    expect(buffer.byteLength).toBe(8);
  });
});
