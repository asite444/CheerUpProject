import {  techData } from "./global.js";


/**
 * 검색 기능 처리
 * @param {string} searchKeyword - 검색어
 */
export function handleSearch(searchKeyword) {
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

// techStackData를 기반으로 techData를 동적으로 채우는 함수
export function mapTechStackData() {
    techStackData.forEach((item) => {
        const category = item.category; // category 값 (job, language 등)
        const name = item.name;         // name 값 (예: Python, Java 등)

        // 유효한 카테고리인지 확인 후 데이터 추가
        if (techData[category]) {
            techData[category].push(name);
        }

    });
}

