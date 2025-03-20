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

export function job_recommended_html(response) {
    // 추천 공고 리스트 처리
    if (response.report_job_recommended && response.report_job_recommended.length > 0) {
        let jobHtml = `
            <h3 class="job-title">🚀 추천 채용 공고</h3>
            <div class="job-list">
        `;

        response.report_job_recommended.forEach(job => {
            let deadlineText = job.deadline || '상시 채용';
            let deadlineClass = deadlineText.includes('상시') ? 'deadline-open' : 'deadline-warning';

            let skillTags = job.skills
                .split(" ")
                .map(skill => `<span class="job-skill-tag">${skill}</span>`)
                .join(" ");

            jobHtml += `
                <div class="job-card">
                    <h4 class="job-card-title">
                        <a href="${job.url}" target="_blank">${job.title}</a>
                    </h4>
                    <p class="job-card-company">🏢 ${job.company}</p>
                    <p class="job-card-deadline ${deadlineClass}">📌 마감일: ${deadlineText}</p>
                    <div class="job-card-skills">
                        🛠 기술 스택: ${skillTags}
                    </div>
                </div>
            `;
        });

        jobHtml += `</div>`; // job-list 닫기
        $('#report-job-recommended').html(jobHtml);
    } else {
        $('#report-job-recommended').html('<p class="no-job">❌ 추천 공고가 없습니다.</p>');
    }
}
