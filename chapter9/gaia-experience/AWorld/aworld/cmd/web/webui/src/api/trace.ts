import { request } from '@/utils/http';

export const fetchTraceData = (traceId: string) => {
  return request(`/api/trace/agent?trace_id=${traceId}`);
};
