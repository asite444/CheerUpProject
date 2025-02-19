import { maxRetries, searchTimeout, keywordInfo } from "./global.js";
import globalState from "./global.js";
/**
 * AJAX 요청을 처리하고 실패 시 재시도
 */
function processAjaxRequest(selectedText, mouseX, mouseY, retries = 0) {
    $.ajax({
        url: "/process_ajax/",
        type: "POST",
        data: { keywords: selectedText },
        xhrFields: { responseType: 'blob' }, // Blob 데이터 처리
        success: function (data, status, xhr) {
            const contentType = xhr.getResponseHeader("Content-Type");

            if (contentType.includes("application/json")) {
                // JSON 응답이 왔을 경우 처리
                data.text().then(text => {
                    try {
                        let jsonResponse = JSON.parse(text);
                        console.error("서버 오류:", jsonResponse.error);
                        $("#sticky-note").html("<p>데이터를 찾을 수 없습니다.</p>");
                    } catch (e) {
                        console.error("JSON 파싱 오류:", e);
                        $("#sticky-note").html("<p>서버 응답 오류 발생</p>");
                    }
                });
                return;
            }

            // 정상적인 Blob(이미지) 응답 처리
            const url = URL.createObjectURL(data);
            const img = new Image();
            img.src = url;
            img.style.maxWidth = "100%";

            img.onload = function () {
                $("#sticky-note").html(img);
                URL.revokeObjectURL(url);
            };

            img.onerror = function () {
                console.error("이미지 로드 실패");
                $("#sticky-note").html("<p>이미지를 불러오는 중 오류 발생</p>");
            };
        },
        error: function (xhr, status, error) {
            if (retries < maxRetries) {
                console.warn(`요청 실패. 재시도 중 (${retries + 1}/${maxRetries})...`);
                const retryDelay = 1000 * Math.pow(2, retries);
                setTimeout(() => {
                    processAjaxRequest(selectedText, mouseX, mouseY, retries + 1);
                }, retryDelay);
            } else {
                console.error(`최대 재시도 도달. 에러: ${error}`);
                $("#sticky-note").html("<p>데이터 검색 실패. 나중에 다시 시도해주세요.</p>");
            }
        }
    });
}


/**
 * 포스트잇 표시 함수 (화면 끝에서 넘치지 않도록 조정)
 */
function showStickyNote(mouseX, mouseY, text) {
    const stickyNote = $("#sticky-note");
    const windowWidth = $(window).width();
    const windowHeight = $(window).height();
    const footerOffset = $(".site-footer").offset().top; // 푸터 위치 가져오기
    const stickyWidth = stickyNote.outerWidth() || 300; // 포스트잇 예상 너비
    const stickyHeight = stickyNote.outerHeight() || 100; // 포스트잇 예상 높이
    let adjustedX = mouseX + 10; // 기본 위치 (마우스 오른쪽)
    let adjustedY = mouseY + 10; // 기본 위치 (마우스 아래쪽)

    // ✅ 오른쪽 끝을 벗어나면 왼쪽으로 조정
    if (adjustedX + stickyWidth > windowWidth) {
        adjustedX = mouseX - stickyWidth - 10;
    }

    // ✅ 아래쪽 끝을 벗어나면 위쪽으로 조정
    if (adjustedY + stickyHeight > footerOffset - 10) { // 푸터 영역을 침범하지 않도록 조정
        adjustedY = mouseY - stickyHeight - 10;
    }

    // ✅ 상단 끝을 벗어나면 다시 아래로 조정
    if (adjustedY < 0) {
        adjustedY = 10;
    }

    // ✅ 왼쪽 끝을 벗어나면 다시 오른쪽으로 조정
    if (adjustedX < 0) {
        adjustedX = 10;
    }

    // 최종 위치 설정 및 표시
    stickyNote.text(text)
        .css({
            top: adjustedY + "px",
            left: adjustedX + "px"
        })
        .fadeIn(200);
}




/**
 * 포스트잇 숨기기 함수
 */
function hideStickyNote() {
    clearTimeout(searchTimeout);
    $("#sticky-note").fadeOut(200);
}


// 드래그 후 텍스트 선택 처리 함수
export function handleMouseUp(event) {
    const selectedText = window.getSelection().toString().trim();
    const currentTime = new Date().getTime();

    // 1. 특정 영역에서만 검색 활성화
    if (!$(event.target).closest(".skill").length) {
        console.warn("지정된 영역 외부에서 드래그 감지됨. 검색 요청을 무시합니다.");
        hideStickyNote();
        return;
    }

    // 2. 너무 긴 텍스트는 무시
    const MAX_LENGTH = 50;
    if (selectedText.length > MAX_LENGTH) {
        console.warn("선택한 텍스트가 너무 깁니다. 요청을 무시합니다.");
        hideStickyNote();
        return;
    }


   // ✅ 객체 속성으로 변경
   globalState.lastSelectionTime = currentTime; // ✅ 정상 작동 (객체 속성 변경은 가능)

    // 4. 사용자가 텍스트를 드래그했을 경우 검색 요청 (단, 너무 짧은 텍스트 제외)
    if (selectedText.length > 0) {
        
        showStickyNote(event.pageX, event.pageY, keywordInfo);

        // 기존 검색 요청이 있다면 취소
        clearTimeout(searchTimeout);

       
            processAjaxRequest(selectedText, event.pageX, event.pageY);
       
    } else {
        hideStickyNote();
    }
}


