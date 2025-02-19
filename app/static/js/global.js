// 최대 재시도 횟수
export const maxRetries = 3; 

// 검색 시간 관련 변수
export let searchTimeout;
const globalState = {
    lastSelectionTime: 0
};
export default globalState; // ✅ 객체 형태로 관리
// 검색 진행 메시지
export const keywordInfo = "데이터 검색중입니다......";

// 연속 드래그 방지 시간 (500ms)
export const DOUBLE_CLICK_THRESHOLD = 500;

// 기술 데이터 매핑을 위한 초기 구조
export const techData = {
    job: [],
    language: [],
    framework: [],
    library: [],
    tool: [],
};




