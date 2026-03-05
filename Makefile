# 게시판 프로젝트 자동화 명령어 모음
# 사용법: make <명령어>
#   make install          - 패키지 설치
#   make run              - 개발 서버 실행
#   make push msg="메시지" - 변경사항 커밋 후 GitHub 푸시

# .env 파일에서 GITHUB_TOKEN, GITHUB_USERNAME 등 환경 변수 로드
ifneq (,$(wildcard .env))
    include .env
    export
endif

.PHONY: install run push

## 패키지 설치
install:
	pip install -r requirements.txt

## 개발 서버 실행 (http://127.0.0.1:5000)
run:
	python app.py

## 변경사항 전체 커밋 후 GitHub 푸시 (.env의 토큰 자동 사용)
## 사용법: make push msg="커밋 메시지"
push:
ifndef msg
	$(error msg 를 입력해주세요.  예: make push msg="기능 추가")
endif
ifndef GITHUB_TOKEN
	$(error .env 파일에 GITHUB_TOKEN 이 없습니다)
endif
ifndef GITHUB_USERNAME
	$(error .env 파일에 GITHUB_USERNAME 이 없습니다)
endif
	@REPO=$$(git remote get-url origin | sed 's|https://||; s|.*@||') && \
	git remote set-url origin "https://$(GITHUB_USERNAME):$(GITHUB_TOKEN)@$$REPO" && \
	git add -A && \
	git commit -m "$(msg)" && \
	git push && \
	git remote set-url origin "https://$$REPO"
	@echo ""
	@echo "푸시 완료!"
