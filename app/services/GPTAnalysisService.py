from app.models.user_input_data import UserInputData
def analyze_stack_top5(user_data:UserInputData):
            # 데이터 처리 및 HTML 텍스트 생성
        """ top5"""
        report=f"""
                <ul>
                        <li><strong>Python (자격 조건: 10.51%, 우대 조건: 15.99%)</strong><br>
                        데이터 분석, 인공지능, 웹 개발 등에 활용되는 다목적 프로그래밍 언어. Django 및 Flask와 함께 백엔드 개발에 많이 사용됨.
                        </li>
                        <li><strong>Java (자격 조건: 14.27%, 우대 조건: 9.30%)</strong><br>
                        객체 지향 프로그래밍 언어로, 엔터프라이즈 애플리케이션과 대규모 시스템 개발에서 널리 사용되며, Spring 프레임워크와 함께 활용됨.
                        </li>
                        <li><strong>JavaScript (자격 조건: 2.77%, 우대 조건: 4.94%)</strong><br>
                        웹 개발의 필수 언어로, 프론트엔드와 백엔드(Node.js) 개발 모두 가능하며, 다양한 프레임워크 및 라이브러리를 지원함.
                        </li>
                        <li><strong>HTML/CSS (자격 조건: 2.97%, 우대 조건: 0.87%)</strong><br>
                        웹 페이지의 구조(HTML)와 디자인(CSS)을 구성하는 기본 요소로, 백엔드 개발에서도 프론트엔드와의 연계를 위해 필요함.
                        </li>
                </ul>

                
                <ul>
                        <li>Top 5 기술 중에서 1, 2위의 기술이 사용자의 기술 스택에 없다면 공부할 것을 권장 (확률과 함께 제공)</li>
                        <li>사용자가 입력한 프레임워크에 대해 확률이 높은 3개의 기술 조합 추천</li>
                </ul>

        """
        
        return report

def analyze_user_tech(user_data:UserInputData):
            # 데이터 처리 및 HTML 텍스트 생성
        """GPT에게 사용자 스택을 분석 요청"""
        report=f"""
                <ul>
                        <li>Top 5 기술 중에서 1, 2위의 기술이 사용자의 기술 스택에 없다면 공부할 것을 권장 (확률과 함께 제공)</li>
                        <li>사용자가 입력한 프레임워크에 대해 확률이 높은 3개의 기술 조합 추천</li>
                </ul>

        """
        
        return report

def analyze_security(user_data:UserInputData):
            # 데이터 처리 및 HTML 텍스트 생성
        """보안사항"""
        report=f"""
                <ul>
                        <li>Top 5 기술 중에서 1, 2위의 기술이 사용자의 기술 스택에 없다면 공부할 것을 권장 (확률과 함께 제공)</li>
                        <li>사용자가 입력한 프레임워크에 대해 확률이 높은 3개의 기술 조합 추천</li>
                </ul>

        """
        
        return report

def analyze_conclusion(user_data:UserInputData):
            # 데이터 처리 및 HTML 텍스트 생성
        """결론"""
        report=f"""
                <ul>
                        <li>Top 5 기술 중에서 1, 2위의 기술이 사용자의 기술 스택에 없다면 공부할 것을 권장 (확률과 함께 제공)</li>
                        <li>사용자가 입력한 프레임워크에 대해 확률이 높은 3개의 기술 조합 추천</li>
                </ul>

        """
        
        return report