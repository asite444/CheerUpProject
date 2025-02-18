
const maxRetries = 3; // 최대 재시도 횟수
let searchTimeout;
let lastSelectionTime = 0;
const keywordInfo = "데이터 검색중입니다......";
const DOUBLE_CLICK_THRESHOLD = 500; // 500ms 이내의 연속 드래그 방지
// 카테고리별 ID 매핑



// 기술 데이터 매핑을 위한 초기 구조
const techData = {
    job: [],
    language: [],
    framework: [],
    library: [],
    tool: [],
};

$(document).ready(function () {
    
       // 검색창 입력 이벤트
       $("#search-bar").on("input", function () {
        const searchKeyword = $(this).val().trim(); // 검색창 입력값 가져오기
        handleSearch(searchKeyword); // 검색 처리 함수 호출
    });
    // 기술 데이터를 매핑
    mapTechStackData();
    initializeEvents(techData);
    
    $('#result-button').on('click', function () {handleUserInputSubmission();});
       // 검색창 입력 이벤트
    $("#search-bar").on("input", function () {
        const searchKeyword = $(this).val().trim(); // 검색창 입력값 가져오기
        handleSearch(searchKeyword); // 검색 처리 함수 호출
    });
    
   
    //최초화면 로드시, 직업 카테고리 최초 선택처리
    displayTechList("job", techData);
    // 토글 버튼 클릭 이벤트 바인딩(사용중지)
    //$('.toggle-btn').on('click', handleToggleClick);

    // 드래그 후 마우스 놓기 이벤트 바인딩
    $(document).on('mouseup', handleMouseUp);

    highlightUserSelectedRows();
}); // end
// techStackData를 기반으로 techData를 동적으로 채우는 함수
function mapTechStackData() {
    techStackData.forEach((item) => {
        const category = item.category; // category 값 (job, language 등)
        const name = item.name;         // name 값 (예: Python, Java 등)

        // 유효한 카테고리인지 확인 후 데이터 추가
        if (techData[category]) {
            techData[category].push(name);
        }

    });
}


/**
 * 각 이벤트 초기화
 */
 function initializeEvents(techData) {
    // 버튼 클릭 이벤트 등록
    $(".category-buttons button").on("click", function () {
        $(".category-buttons button").removeClass("active");
        
        // 클릭한 버튼에 active 클래스 추가
        $(this).addClass("active");
        const category = $(this).attr("id").replace("-button", ""); // ID에서 카테고리 추출
    
        $("#search-bar").val("");

        displayTechList(category, techData);
    });

     // 분석된, 기술분야 버튼 클릭 이벤트 
     $(".analysis-btn").on("click", function () {
        // 모든 버튼에서 active 클래스 제거
        $(".analysis-btn").removeClass("active");
        // 클릭한 버튼에 active 클래스 추가
        $(this).addClass("active");

        
        let targetSection = $(this).data("target");

        // 모든 분석 결과 영역 숨기기
        $(".analysis-content").hide();

        // 해당하는 분석 결과 영역만 보이게 설정

        $("#" + targetSection).show();
        if(targetSection=="tech-results"){
            let selectedCategory = $(this).attr("id").replace("-analysis", "");
            $(".analysis-top5").hide();
            $("#report_top5_" + selectedCategory).show();
           

            //console.log("선택된 버튼 ID:", selectedCategory);
        }
    });

    // 기술 선택 이벤트 등록
    $(".tech-list").on("click", ".item", handleItemClick);

    // 기술 삭제 이벤트 등록
    $("#selected-tech-list").on("click", ".remove-item", handleRemoveItem);
}

/**
 * 검색 기능 처리
 * @param {string} searchKeyword - 검색어
 */
 function handleSearch(searchKeyword) {
    // 현재 활성화된 카테고리 버튼 가져오기


    /*
    언어면 language ,프레임워크면 framwork
    */
    const activeCategory = $(".category-buttons button.active").attr("id")?.replace("-button", "");

    


    // 검색 키워드를 소문자로 변환하여 필터링
    const filteredData = techData[activeCategory].filter((tech) =>
        tech.toLowerCase().includes(searchKeyword.toLowerCase())
    );

    // 검색된 데이터를 표시
    displayTechList(activeCategory, { [activeCategory]: filteredData });
}


/**
 * 카테고리 기술 목록 나열
 * @param {string} category - 클릭된 카테고리
 * @param {Object} techData - 기술 데이터 매핑 객체
 */
 function displayTechList(category, techData) {
   
    const techList = techData[category] || [];
    const techListContainer = $(".tech-list");


    //console.log("category:"+category)
    //console.log("techData:"+techList)
    // 기존 기술 제거
    techListContainer.empty();

    // 기술 목록 추가
    techList.forEach((tech) => {
        techListContainer.append(
            `<div class="item" data-category="${category}" data-value="${tech}">${tech}</div>`
        );
    });
}

/**
 * 기술 선택 및 중복 확인
 * @param {Event} event - 클릭 이벤트 객체
 */
 function handleItemClick(event) {
    const selectedCategory = $(event.currentTarget).data("category");
    const selectedValue = $(event.currentTarget).data("value");

    // 직무(`job`) 선택의 경우 하나만 허용
    if (selectedCategory === "job") {
        if ($("#selected-tech-list .selected-item[data-category='job']").length > 0) {
            Swal.fire({
                icon: "warning",
                title: "직무는 하나만 \n 선택할 수 있습니다.",
                
            });
            return;
        }

        
    } 
    // 중복 선택 방지
    if ($(`#selected-tech-list .selected-item[data-value='${selectedValue}']`).length > 0) {
        Swal.fire({
            icon: "warning",
            title: "이미 선택된 기술입니다.",
            text: `${selectedValue}은(는) 이미 추가되었습니다.`,
        });
        return;
    }

    // 선택된 기술 추가
    addSelectedItem(selectedCategory, selectedValue);
}


/**
 * 선택된 기술 추가
 * @param {string} category - 선택된 기술의 카테고리
 * @param {string} value - 선택된 기술 값
 */
function addSelectedItem(category, value) {
    $("#selected-tech-list").append(
        `<li class="selected-item" data-category="${category}" data-value="${value}">
            ${value}
            <button class="remove-item">X</button>
        </li>`
    );
}

/**
 * 선택된 기술 삭제
 * @param {Event} event - 클릭 이벤트 객체
 */
function handleRemoveItem(event) {
    $(event.currentTarget).closest(".selected-item").remove();
}




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


function handleUserInputSubmission() {
    // 선택된 항목 수집
    const dataToSend = {
        languages: collectSelectedItems('.selected-item[data-category="language"]').sort((a, b) => a.localeCompare(b)),
        frameworks: collectSelectedItems('.selected-item[data-category="framework"]').sort((a, b) => a.localeCompare(b)),
        libraries: collectSelectedItems('.selected-item[data-category="library"]').sort((a, b) => a.localeCompare(b)),
        devtools: collectSelectedItems('.selected-item[data-category="tool"]').sort((a, b) => a.localeCompare(b)),
        jobs: collectSelectedItems('.selected-item[data-category="job"]').sort((a, b) => a.localeCompare(b)),
    };

      // **직무 선택 필수 검사**
      if (dataToSend.jobs.length === 0) {
        Swal.fire({
            icon: 'warning',
            title: '직무를 선택하세요',
            text: '분석을 진행하려면 반드시 하나의 직무를 선택해야 합니다.',
        });
        return; // 함수 종료 (서버 요청 방지)
    }

    // 데이터 유효성 검사 및 서버로 전송
    if (validateSelectedData(dataToSend)) {
        Swal.fire({
            title: '분석을 진행하시겠습니까?',
            icon: 'question',
            showCancelButton: true,
            confirmButtonColor: '#3085d6',
            cancelButtonColor: '#d33',
            confirmButtonText: '확인',
            cancelButtonText: '취소',
        }).then((result) => {
            if (result.isConfirmed) {
                  // 로딩 메시지 표시
                Swal.fire({
                    title: '분석 중입니다...',
                    text: '잠시만 기다려 주세요.',
                    allowOutsideClick: false,
                    didOpen: () => {
                        Swal.showLoading();
                    }
                });


                submitDataToServer(dataToSend);
            }
        });
    } 
}

/**
 * 선택된 항목 수집
 * @param {string} selector - 선택된 항목을 찾기 위한 셀렉터
 * @returns {Array} 선택된 항목 값 배열
 */
function collectSelectedItems(selector) {
    const selectedItems = [];
    $(selector).each(function () {
        selectedItems.push($(this).data('value')); // 선택된 항목의 데이터를 배열로 수집
    });
    return selectedItems;
}

/**
 * 데이터 유효성 검사
 * @param {Object} data - 수집된 데이터
 * @returns {boolean} 데이터 유효 여부
 */
function validateSelectedData(data) {
    return Object.values(data).some((category) => category.length > 0);
}

/**
 * 서버로 데이터 전송
 * @param {Object} data - 서버로 전송할 데이터
 */
function submitDataToServer(data) {
    $.ajax({
        url: '/user-input-data',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(data),
        success: function (response) {

            // 언어, 프레임워크, 라이브러리, 툴 각각의 결과를 표시
            $('#report_top5_it_language').html(response.report_top5_language);
            $('#report_top5_framework').html(response.report_top5_framework);
            $('#report_top5_library').html(response.report_top5_library);
            $('#report_top5_tool').html(response.report_top5_tool);

            //$('#result-top5').html(response.report_top5);
            $('#result-user-tech').html(response.report_user_tech);
            $('#report_improvement').html(response.report_improvement);
            $('#result-conclusion').html(response.report_conclusion);
            $('#result-graph-career').html(response.report_graph_career);
            $('#result-graph-degree').html(response.report_graph_degree);
            $('#result-graph-language').html(response.report_graph_language);
            // 분석 완료 후 분석 결과 영역 표시
            $("#analysis-result-section").slideDown();

            Swal.close();
            Swal.fire({
                title: '분석이 완료되었습니다',
                icon: 'success',
            });
        },
        error: function (xhr, status, error) {
            console.error('오류 발생:', error);
            Swal.close(); // 로딩 메시지 닫기
            Swal.fire({
                icon: 'error',
                title: '오류 발생',
                text: '데이터 전송 중 문제가 발생했습니다.',
            });
        },
    });
}



// 토글 애니메이션 처리 함수(사용중지)
function handleToggleClick(event) {
    const content = $(event.currentTarget).next(".toggle-content");
    content.slideToggle(300); // 부드러운 토글 애니메이션
}



// 드래그 후 텍스트 선택 처리 함수
function handleMouseUp(event) {
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


    lastSelectionTime = currentTime; // 현재 선택 시간 저장

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


/**
 * 사용자가 선택한 기술 강조 애니메이션 함수
 */
function highlightUserSelectedRows() {
    $(".analysis_top5 tr.user-selected").each(function () {
        let row = $(this);
        setInterval(() => {
            row.fadeOut(500).fadeIn(500);
        }, 1500);
    });
}