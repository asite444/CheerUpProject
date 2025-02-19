
/**
 * 기술 선택 및 중복 확인
 * @param {Event} event - 클릭 이벤트 객체
 */
export function handleItemClick(event) {
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
export function handleRemoveItem(event) {
    $(event.currentTarget).closest(".selected-item").remove();
}


/**
 * 선택된 항목 수집
 * @param {string} selector - 선택된 항목을 찾기 위한 셀렉터
 * @returns {Array} 선택된 항목 값 배열
 */
export function collectSelectedItems(selector) {
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
export function validateSelectedData(data) {
    return Object.values(data).some((category) => category.length > 0);
}
