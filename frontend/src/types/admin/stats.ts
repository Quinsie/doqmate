/**
 * 챗봇별 질의 수
 */
export interface ChatbotQueryCount {
  chatbot_id: string;
  chatbot_name?: string;
  queries: number;
}

/**
 * 날짜별 질의 수
 */
export interface DateQueryCount {
  date: string;
  queries: number;
}

/**
 * 전체 통계 응답 데이터
 * GET /api/stats/overview
 */
export interface OverviewStatsResponseData {
  total_queries: number;
  unique_clients: number;
  by_chatbot: ChatbotQueryCount[];
  by_date: DateQueryCount[];
}

/**
 * 챗봇별 통계 응답 데이터
 * GET /api/stats/chatbot/{chatbot_id}
 */
export interface ChatbotStatsResponseData {
  chatbot_id: string;
  chatbot_name?: string;
  total_queries: number;
  unique_clients: number;
  by_date: DateQueryCount[];
}

/**
 * 날짜별 통계 응답 데이터
 * GET /api/stats/date/{date}
 */
export interface DateStatsResponseData {
  date: string;
  total_queries: number;
  unique_clients: number;
  by_chatbot: ChatbotQueryCount[];
}
