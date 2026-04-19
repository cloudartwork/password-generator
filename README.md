# 비밀번호 난수 생성기

🔗 https://cloudartwork.github.io/password-generator/

[![Deploy to GitHub Pages](https://github.com/cloudartwork/password-generator/actions/workflows/deploy.yml/badge.svg)](https://github.com/cloudartwork/password-generator/actions/workflows/deploy.yml)

여러 개의 비밀번호를 한 번에 생성할 수 있는 간단한 웹 앱입니다. 브라우저에서 `crypto.getRandomValues`를 사용해 암호학적으로 안전한 난수로 비밀번호를 만들고, 어떤 값도 서버로 보내지 않습니다.

지원 기능:

- 비밀번호 길이 조절 (4–64자)
- 생성 개수 선택 (최대 1만 개)
- 숫자, 소문자, 대문자, 기호 포함 여부 설정
- 유사 문자 제외 (예: `o, O, 0, i, I, l, 1, L`)
- 애매한 문자 제외 (예: `,.;:'``~()/{}[]`)
- 같은 요청 안에서 중복 없이 생성
- 결과를 줄바꿈 텍스트로 표시 · 전체 클립보드 복사

## 로컬에서 확인하기

이 저장소는 단일 정적 페이지(`index.html`)입니다. 파일을 바로 열거나 간단한 정적 서버로 열면 됩니다.

```bash
python3 -m http.server 8000
# 브라우저에서 http://localhost:8000/ 접속
```

## GitHub Pages 배포

`main` 브랜치에 푸시하면 `.github/workflows/deploy.yml`이 자동으로 GitHub Pages에 배포합니다.

처음 한 번은 저장소 **Settings → Pages → Source**를 **"GitHub Actions"**로 설정해야 워크플로우가 반영됩니다.
