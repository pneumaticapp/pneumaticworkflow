import * as React from 'react';
import { render } from '@testing-library/react';
import { useDispatch, useSelector } from 'react-redux';

import { useDatasetOptions } from '../useDatasetOptions';
import { EExtraFieldType, IExtraField } from '../../../../../types/template';
import { IDatasetListItem } from '../../../../../types/dataset';
import { loadAllDatasets } from '../../../../../redux/datasets/slice';
import { makeExtraField } from '../../../../../__stubs__/fields.factory';

jest.mock('../../../../../redux/datasets/slice', () => ({
  loadAllDatasets: jest.fn(() => ({ type: 'datasets/loadAllDatasets' })),
}));

interface ITestHookProps {
  fields: IExtraField[];
  onOptions?: (options: { label: string; value: string }[]) => void;
}

const TestComponent = ({ fields, onOptions }: ITestHookProps) => {
  const options = useDatasetOptions(fields);

  React.useEffect(() => {
    onOptions?.(options);
  }, [options, onOptions]);

  return <div data-testid="options-count">{options.length}</div>;
};

const makeDataset = (id: number, name: string, itemsCount: number): IDatasetListItem => ({
  id,
  name,
  description: '',
  dateCreatedTsp: 100,
  itemsCount,
});

describe('useDatasetOptions', () => {
  const mockDispatch = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useDispatch as jest.Mock).mockReturnValue(mockDispatch);
  });

  describe('filtering empty datasets (itemsCount === 0)', () => {
    it('does not display empty datasets in the options list, leaving only datasets with items', () => {
      let capturedOptions: { label: string; value: string }[] = [];
      const datasets = [makeDataset(1, 'Empty dataset', 0), makeDataset(2, 'Non-empty dataset', 5)];

      const state = {
        datasets: {
          allDatasetsList: datasets,
          isAllDatasetsLoaded: true,
          isAllDatasetsLoading: false,
        },
      };
      (useSelector as jest.Mock).mockImplementation((selector) => selector(state));

      render(
        React.createElement(TestComponent, {
          fields: [makeExtraField({ type: EExtraFieldType.Radio })],
          onOptions: (options) => {
            capturedOptions = options;
          },
        }),
      );

      expect(capturedOptions).toHaveLength(1);
      expect(capturedOptions[0]).toEqual({ label: 'Non-empty dataset', value: '2' });
    });
  });

  describe('natural numeric sorting of datasets list', () => {
    it('sorts datasets with numeric names in natural order (1, 2, 10 instead of 1, 10, 2)', () => {
      let capturedOptions: { label: string; value: string }[] = [];
      const datasets = [
        makeDataset(1, '1', 1),
        makeDataset(10, '10', 1),
        makeDataset(2, '2', 1),
        makeDataset(20, '20', 1),
        makeDataset(100, '100', 1),
      ];

      const state = {
        datasets: {
          allDatasetsList: datasets,
          isAllDatasetsLoaded: true,
          isAllDatasetsLoading: false,
        },
      };
      (useSelector as jest.Mock).mockImplementation((selector) => selector(state));

      render(
        React.createElement(TestComponent, {
          fields: [makeExtraField({ type: EExtraFieldType.Checkbox })],
          onOptions: (options) => {
            capturedOptions = options;
          },
        }),
      );

      const labels = capturedOptions.map((option) => option.label);
      expect(labels).toEqual(['1', '2', '10', '20', '100']);
    });
  });

  describe('loading datasets via saga', () => {
    it('dispatches loadAllDatasets when fields contain dataset types and datasets are not yet loaded', () => {
      const state = {
        datasets: {
          allDatasetsList: [],
          isAllDatasetsLoaded: false,
          isAllDatasetsLoading: false,
        },
      };
      (useSelector as jest.Mock).mockImplementation((selector) => selector(state));

      render(
        React.createElement(TestComponent, {
          fields: [makeExtraField({ type: EExtraFieldType.Creatable })],
        }),
      );

      expect(mockDispatch).toHaveBeenCalledWith(loadAllDatasets());
    });
  });
});
