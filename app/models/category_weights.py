def get_weight(duty):
    weights = {
        'PM': {
            'it_language': 0.2,
            'framework': 0.25,
            'library': 0.45,
            'tool': 0.1
        },
        '백엔드': {
            'it_language': 0.3,
            'framework': 0.45,
            'library': 0.3,
            'tool': 0.15
        },
        '데이터 직무': {
            'it_language': 0.1,
            'framework': 0.4,
            'library': 0.4,
            'tool': 0.1
        },
        '인프라 엔지니어': {
            'it_language': 0.2,
            'framework': 0.35,
            'library': 0.3,
            'tool': 0.15
        },
        '앱 개발자': {
            'it_language': 0.3,
            'framework': 0.45,
            'library': 0.1,
            'tool': 0.15
        },
        '게임': {
            'it_language': 0.3,
            'framework': 0.2,
            'library': 0.2,
            'tool': 0.3
        },
        'AI': {
            'it_language': 0.4,
            'framework': 0.1,
            'library': 0.4,
            'tool': 0.1
        },
        '임베디드': {
            'it_language': 0.4,
            'framework': 0.1,
            'library': 0.4,
            'tool': 0.1
        },
        '프론트 엔드': {
            'it_language': 0.3,
            'framework': 0.4,
            'library': 0.2,
            'tool': 0.1
        },
        'QA': {
            'it_language': 0.3,
            'framework': 0.3,
            'library': 0.2,
            'tool': 0.2
        },
        '데이터 분석': {
            'it_language': 0.4,
            'framework': 0.25,
            'library': 0.25,
            'tool': 0.1
        },
        'VR': {
            'it_language': 0.5,
            'framework': 0.1,
            'library': 0.1,
            'tool': 0.3
        },
        '시스템': {
            'it_language': 0.35,
            'framework': 0.2,
            'library': 0.35,
            'tool': 0.1
        },
        '블록체인': {
            'it_language': 0.2,
            'framework': 0.3,
            'library': 0.3,
            'tool': 0.2
        },
        'ERP': {
            'it_language': 0.4,
            'framework': 0.3,
            'library': 0.1,
            'tool': 0.2
        },
        '언어별 개발자': {
            'it_language': 0.7,
            'framework': 0.1,
            'library': 0.1,
            'tool': 0.1
        }
    }
    return weights.get(duty)