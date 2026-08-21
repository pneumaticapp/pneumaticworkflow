import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { EGraphViewMode, ITemplateGraphViewState } from '../../components/TemplateEdit/TemplateGraphEditor/types';

const initialState: ITemplateGraphViewState = {
  viewMode: EGraphViewMode.List,
  selectedTaskApiName: null,
};

const templateGraphViewSlice = createSlice({
  name: 'templateGraphView',
  initialState,
  reducers: {
    setViewMode(state, action: PayloadAction<EGraphViewMode>) {
      state.viewMode = action.payload;
      state.selectedTaskApiName = null;
    },
    setSelectedTask(state, action: PayloadAction<string | null>) {
      state.selectedTaskApiName = action.payload;
    },
    resetGraphView() {
      return initialState;
    },
  },
});

export const { setViewMode, setSelectedTask, resetGraphView } = templateGraphViewSlice.actions;
export default templateGraphViewSlice.reducer;
