/**
 * 테스트용 더미 데이터 및 응답 함수
 */

import type { Chatbot } from '../types/admin/chatbot';
import type { Admin } from '../types/auth/auth';

// 더미 챗봇 데이터
export const dummyChatbots: Chatbot[] = [
  {
    chatbot_id: 'default-doqmate',
    name: 'DoQ-Mate',
    description: '로컬푸드 관련 정보를 제공하는 챗봇',
    is_public: true,
    created_at: new Date().toISOString(),
  },
];

// 더미 관리자 데이터
export const dummyAdmins: Admin[] = [
  {
    admin_id: 'admin_0001',
    username: 'admin1',
    name: '김관리',
    created_at: '2024-01-15T10:30:00Z',
  },
  {
    admin_id: 'admin_0002',
    username: 'admin2',
    name: '이관리',
    created_at: '2024-02-20T14:20:00Z',
  },
  {
    admin_id: 'admin_0003',
    username: 'admin3',
    name: '박관리',
    created_at: '2024-03-10T09:15:00Z',
  },
];

// 더미 봇 응답 목록
const dummyBotResponses = [
  "안녕하세요! 무엇을 도와드릴까요?",
  "좋은 질문이네요. 제가 도움을 드리겠습니다.",
  "네, 그 내용에 대해 설명드리겠습니다.\n\n관련 정보를 찾아보니 다음과 같습니다:\n1. 첫 번째 포인트\n2. 두 번째 포인트\n3. 세 번째 포인트",
  "죄송하지만 해당 정보는 현재 제공할 수 없습니다. 다른 질문이 있으신가요?",
  "알겠습니다. 추가로 궁금하신 사항이 있으시면 언제든지 물어보세요!",
  "매우 흥미로운 주제입니다!\n\n이에 대해 자세히 설명드리자면, 여러 측면에서 고려해볼 수 있습니다. 먼저 기본적인 개념부터 시작하여 점진적으로 깊이 있는 내용을 다뤄보겠습니다.",
  "이 질문에 답변하기 위해서는 몇 가지 배경 지식이 필요합니다. 간단히 요약하면 다음과 같습니다.",
  "좋은 지적이십니다. 추가로 다음 사항도 고려해보시면 좋을 것 같습니다.",
];

// 주제별 더미 응답
const topicResponses: Record<string, string[]> = {
  인사: [
    "안녕하세요! DoQ-Mate입니다. 무엇을 도와드릴까요?",
    "반갑습니다! 오늘 하루는 어떠신가요?",
    "안녕하세요! 궁금하신 점을 말씀해주세요.",
  ],
  로컬푸드: [
    "로컬푸드(Local Food)란 장거리 운송을 거치지 않고 생산지로부터 반경 50km 이내의 가까운 지역에서 소비되는 농산물을 의미합니다.\n\n[주요 특징 및 장점]\n1. 신선도와 안전성: 복잡한 유통 과정을 생략하여 수확 후 소비까지의 시간이 짧아 신선하며, 누가 생산했는지 알 수 있어 신뢰할 수 있습니다.\n2. 환경 보호: 이동 거리를 뜻하는 '푸드 마일리지'가 줄어들어 운송 과정에서 발생하는 이산화탄소 배출을 억제합니다.\n3. 지역 경제 상생: 유통 마진을 줄임으로써 생산자에게는 정당한 소득을, 소비자에게는 합리적인 가격을 제공하여 지역 경제를 활성화합니다.",
  ],
  기능: [
    "현재 다음과 같은 기능을 사용하실 수 있습니다:\n\n✅ 채팅 생성 및 관리\n✅ 채팅 제목 변경\n✅ 채팅 고정/해제\n✅ 채팅 기록 저장 (로컬)\n✅ 메시지 수정\n\n궁금하신 기능이 있으시면 말씀해주세요!",
  ],
};

/**
 * 랜덤 더미 봇 응답 생성
 */
export function getRandomBotResponse(): string {
  const randomIndex = Math.floor(Math.random() * dummyBotResponses.length);
  return dummyBotResponses[randomIndex];
}

/**
 * 키워드 기반 더미 봇 응답 생성
 */
export function getSmartBotResponse(userMessage: string): string {
  const lowerMessage = userMessage.toLowerCase();

  // 인사 감지
  if (
    lowerMessage.includes('안녕') ||
    lowerMessage.includes('하이') ||
    lowerMessage.includes('hello') ||
    lowerMessage.includes('hi')
  ) {
    const responses = topicResponses.인사;
    return responses[Math.floor(Math.random() * responses.length)];
  }

  // 로컬푸드 관련
  if (
    lowerMessage.includes('로컬푸드') ||
    lowerMessage.includes('지역') ||
    lowerMessage.includes('농산물')
  ) {
    return topicResponses.로컬푸드[0];
  }

  // 기능 문의
  if (
    lowerMessage.includes('기능') ||
    lowerMessage.includes('할 수') ||
    lowerMessage.includes('도움')
  ) {
    return topicResponses.기능[0];
  }

  // 일반 응답
  return getRandomBotResponse();
}

/**
 * 응답 시뮬레이션 (타이핑 효과를 위한 딜레이)
 */
export function simulateBotResponse(
  userMessage: string,
  callback: (response: string) => void,
  delay: number = 1000
): void {
  setTimeout(() => {
    const response = getSmartBotResponse(userMessage);
    callback(response);
  }, delay);
}

/**
 * 스트리밍 응답 시뮬레이션
 */
export async function* streamBotResponse(userMessage: string): AsyncGenerator<string> {
  const response = getSmartBotResponse(userMessage);
  const words = response.split(' ');

  for (let i = 0; i < words.length; i++) {
    await new Promise((resolve) => setTimeout(resolve, 50));
    yield words.slice(0, i + 1).join(' ');
  }
}
