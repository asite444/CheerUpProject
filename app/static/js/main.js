import { techData } from "./global.js";
import { mapTechStackData,handleSearch,displayTechList } from "./search.js";
import { initializeEvents,highlightUserSelectedRows,handleUserInputSubmission } from "./analysis.js";
import { handleMouseUp } from "./sticky_note.js";



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

    // 드래그 후 마우스 놓기 이벤트 바인딩
    $(document).on('mouseup', handleMouseUp);

    highlightUserSelectedRows();
}); // end







