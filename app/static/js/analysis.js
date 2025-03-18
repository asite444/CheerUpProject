import { handleItemClick,handleRemoveItem,validateSelectedData,collectSelectedItems } from "./selection.js";
 
/**
 * 각 이벤트 초기화
 */
export function initializeEvents(techData) {
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



export function handleUserInputSubmission() {
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

             // 추천 공고 리스트 처리
             if (response.report_job_recommended && response.report_job_recommended.length > 0) {
                let jobHtml = '<h3>추천 채용 공고</h3><ul>';
                
                response.report_job_recommended.forEach(job => {
                    jobHtml += `
                        <li>
                            <a href="${job.url}" target="_blank"><strong>${job.title}</strong></a> 
                            - ${job.company} (📌 마감일: ${job.deadline || '상시 채용'})
                            <br>🛠 기술 스택: ${job.skills}
                        </li>
                    `;
                });

                jobHtml += '</ul>';
                $('#report-job-recommended').html(jobHtml);
            } else {
                $('#report-job-recommended').html('<p>추천 공고가 없습니다.</p>');
            }


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

/**
 * 카테고리 기술 목록 나열
 * @param {string} category - 클릭된 카테고리
 * @param {Object} techData - 기술 데이터 매핑 객체
 */
export function displayTechList(category, techData) {
   
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
 * 사용자가 선택한 기술 강조 애니메이션 함수
 */
export function highlightUserSelectedRows() {
    $(".analysis_top5 tr.user-selected").each(function () {
        let row = $(this);
        setInterval(() => {
            row.fadeOut(500).fadeIn(500);
        }, 1500);
    });
}