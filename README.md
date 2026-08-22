# 우리 지역 체크인

방문한 지역과 만족도를 기록하고 확인할 수 있는 위치 기반 체크인 서비스입니다.
FastAPI 백엔드가 기록을 저장·집계하고, Streamlit 프런트엔드가 지도와 통계로 시각화해 보여줍니다.
지역/만족도/키워드로 기록을 검색하고 CSV로 내보낼 수도 있습니다.

## 기능 목록

- 지역, 만족도(1~5), 한 줄 메모로 방문 기록 남기기
- 이름으로 내 기록 조회 및 삭제
- 지역별/전체 만족도 통계 대시보드 (총 기록 수, 참여자 수, 평균 만족도, 지역별 그래프)
- 지역 · 최소 만족도 · 메모 키워드로 기록 검색 필터링
- 검색 조건에 맞는 기록을 CSV로 내보내기
- 지역별 랜덤 좌표를 지도에 표시하는 데모 시각화

## 로컬에서 실행하는 방법

### 1. conda 환경 만들기

```bash
conda create -n my_service python=3.11
conda activate my_service
```

### 2. 의존성 설치 (pip install)

```bash
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
```

### 3. 백엔드 실행

```bash
cd backend
./run.sh
```

- 백엔드: http://localhost:8000
- API 문서(Swagger): http://localhost:8000/docs

### 4. 프런트엔드 실행 (새 터미널에서, 백엔드를 먼저 켜둔 상태로)

```bash
cd frontend
./run.sh
```

- 프런트엔드: http://localhost:8501

> Docker로 한 번에 실행하려면 프로젝트 루트에서 `docker compose up --build`를 사용할 수도 있습니다.
