import * as React from 'react';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { IntlProvider } from 'react-intl';

import { enMessages } from '../../../../../lang/locales/en_US';
import { TUploadedFile, uploadFiles } from '../../../../../utils/uploadFiles';
import { AttachmentField } from '../AttachmentField';
import { getImageDimensions } from '../utils/getImageDimensions';

jest.mock('../../../../../utils/uploadFiles', () => ({
  uploadFiles: jest.fn(),
  MAX_FILE_SIZE: 100 * 1024 * 1024,
}));

jest.mock('../utils/getImageDimensions', () => ({
  getImageDimensions: jest.fn(),
}));

jest.mock('../../../../TemplateEdit/ExtraFields/File/ExtraFieldFilesGrid', () => ({
  ExtraFieldFilesGrid: ({
    attachments,
    deleteFile,
  }: {
    attachments: TUploadedFile[];
    deleteFile?(id: string): () => void;
  }) => (
    <div>
      {attachments
        .filter((file) => !file.isRemoved && file.thumbnailUrl)
        .map((file) => (
          <div key={file.id}>
            <img alt={file.name || file.url} src={file.thumbnailUrl} />
            {deleteFile && (
              <button type="button" onClick={deleteFile(file.id)}>
                remove
              </button>
            )}
          </div>
        ))}
    </div>
  ),
}));

const mockedUploadFiles = uploadFiles as jest.MockedFunction<typeof uploadFiles>;
const mockedGetImageDimensions = getImageDimensions as jest.MockedFunction<typeof getImageDimensions>;

const savedLogo: TUploadedFile = {
  id: 'saved-logo',
  name: 'old-logo.png',
  url: 'https://example.com/old-logo.png',
  thumbnailUrl: 'https://example.com/old-logo.png',
  size: 10,
};

const uploadedLogo: TUploadedFile = {
  id: 'new-logo',
  name: 'new-logo.png',
  url: 'https://example.com/new-logo.png',
  thumbnailUrl: 'https://example.com/new-logo.png',
  size: 20,
};

const renderField = (
  props: Partial<React.ComponentProps<typeof AttachmentField>> = {},
) => {
  const setUploadedFiles = props.setUploadedFiles || jest.fn();

  return {
    setUploadedFiles,
    ...render(
      <IntlProvider locale="en" messages={enMessages}>
        <AttachmentField
          accountId={1}
          uploadedFiles={[savedLogo]}
          setUploadedFiles={setUploadedFiles}
          acceptedType="image"
          expectedImageWidth={80}
          expectedImageHeight={80}
          {...props}
        />
      </IntlProvider>,
    ),
  };
};

describe('AttachmentField', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedGetImageDimensions.mockResolvedValue({ width: 80, height: 80 });
  });

  it('should show the uploaded image before the parent saves the new url', async () => {
    mockedUploadFiles.mockResolvedValue([uploadedLogo]);
    const { setUploadedFiles, container } = renderField();

    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['logo'], 'new-logo.png', { type: 'image/png' });

    await act(async () => {
      fireEvent.change(fileInput, { target: { files: [file] } });
    });

    expect(await screen.findByAltText(uploadedLogo.name)).toBeInTheDocument();
    expect(screen.queryByAltText(savedLogo.name)).not.toBeInTheDocument();
    expect(setUploadedFiles).toHaveBeenCalledWith([
      expect.objectContaining({ url: uploadedLogo.url, thumbnailUrl: uploadedLogo.url }),
    ]);
  });

  it('should hide the image after delete before the parent saves', async () => {
    const { setUploadedFiles } = renderField();

    expect(screen.getByAltText(savedLogo.name)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'remove' }));

    await waitFor(() => {
      expect(screen.queryByAltText(savedLogo.name)).not.toBeInTheDocument();
    });
    expect(setUploadedFiles).toHaveBeenCalledWith([
      expect.objectContaining({ id: savedLogo.id, isRemoved: true }),
    ]);
  });

  it('should keep the local preview when the parent re-renders with the previously saved file', async () => {
    mockedUploadFiles.mockResolvedValue([uploadedLogo]);
    const { rerender, container } = renderField();

    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['logo'], 'new-logo.png', { type: 'image/png' });

    await act(async () => {
      fireEvent.change(fileInput, { target: { files: [file] } });
    });

    expect(await screen.findByAltText(uploadedLogo.name)).toBeInTheDocument();

    rerender(
      <IntlProvider locale="en" messages={enMessages}>
        <AttachmentField
          accountId={1}
          uploadedFiles={[{ ...savedLogo }]}
          setUploadedFiles={jest.fn()}
          acceptedType="image"
          expectedImageWidth={80}
          expectedImageHeight={80}
        />
      </IntlProvider>,
    );

    expect(screen.getByAltText(uploadedLogo.name)).toBeInTheDocument();
    expect(screen.queryByAltText(savedLogo.name)).not.toBeInTheDocument();
  });
});
