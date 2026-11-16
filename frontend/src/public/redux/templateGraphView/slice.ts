import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { EGraphViewMode, ITemplateGraphViewState } from '../../components/TemplateEdit/TemplateGraphEditor/types';
import {
  getGraphViewMode,
  saveGraphViewMode,
} from '../../components/TemplateEdit/TemplateGraphEditor/utils/graphViewModeStorage';

const createInitialState = (): ITemplateGraphViewState => ({
  viewMode: getGraphViewMode(),
  selectedTaskApiName: null,
});

const templateGraphViewSlice = createSlice({
  name: 'templateGraphView',
  initialState: createInitialState(),
  reducers: {
    setViewMode(state, action: PayloadAction<EGraphViewMode>) {
      saveGraphViewMode(action.payload);
      state.viewMode = action.payload;
      state.selectedTaskApiName = null;
    },
    setSelectedTask(state, action: PayloadAction<string | null>) {
      state.selectedTaskApiName = action.payload;
    },
    resetGraphView() {
      return createInitialState();
    },
  },
});

export const { setViewMode, setSelectedTask, resetGraphView } = templateGraphViewSlice.actions;
export default templateGraphViewSlice.reducer;
