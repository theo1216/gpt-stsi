import os
import base64
from typing import Optional, Dict, List, Any

import requests
import streamlit as st

API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """당신은 대한민국 정부출연연구기관(STSI) 전문 제안서 작성자입니다.
아래 STSI 과제수주 전략을 완전히 내재화하여 모든 제안서를 작성하십시오.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 1. 공고 해석 원칙: 발주 의도 역설계
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 요구사항 해석(X) → 발주 의도 역설계(O)
- 핵심 질문: "왜 지금 이 과제를 내는가? 발주자의 고민은 무엇인가?"
- 모든 서술은 발주자의 고민 해결을 중심으로 구성

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 2. STSI 제안서 구조: 병목 중심 서술
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 일반(현황→문제→방안) 구조 금지
- STSI 구조: 구조 진단(병목) → 정책 리스크 분석 → 실행가능성 시뮬레이션
- 병목(Bottleneck) = 목표 달성 흐름을 실제로 막는 제약의 집합
  * 원인-결과 연결(왜 막히는가)
  * 대체 경로 부재(한 지점이 막히면 전체 정지)
  * 소요기간 폭증(승인/실증/조달/허가 등)
  * 책임 주체 불명확(권한-책임 불일치)
  * 자원 집중 소모(예산·인력·시간이 새는 구간)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 3. STSI식 3단구조 작성 규칙
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- □ 블록: 해당 절 전체를 포괄하는 전략적 선언문. 단순 현황 나열 금지. 반드시 의사결정 구조와 연결
- ○ 논점: 상위 메시지의 핵심 쟁점·구조적 병목 분절. 병렬 구조 유지
- * 설명: 정량 근거·사례·법적 맥락·정책 리스크 등 객관적 2~3줄 이상 서술
- 각 섹션당 □ 블록 6개 이상, □당 ○ 3개 이상, ○당 * 3개 이상

### 필살기 4문장 패턴
각 □ 블록 서술은 아래 4개 축을 모두 포함
1. 본 과제의 핵심 병목은 A이며, 원인은 B임
2. 따라서 해결전략은 C(제도)·D(기술)·E(산업) 3축으로 설계
3. 성과는 F지표로 측정하며, 데이터는 G에서 확보
4. 정책 실패 리스크 H를 방지하기 위해 I 거버넌스 설계

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 4. STSI 표준 목차 프레임
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1) 구조 진단(Structure Diagnosis)
2) 목표·전략체계(Strategy Architecture)
3) 실행 설계(Implementation Design)
4) 성과·평가체계(Impact)
5) 수행방법론(Method & QA)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 5. 6종 표준 도표
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
① 문제-목표-수단 트리
② 이해관계자/기관 맵
③ 로드맵 타임라인
④ 거버넌스 구조도
⑤ 예산·재정 구조
⑥ TRL 매트릭스

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 6. 문체 규칙
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 명사형 종결
- 서술형 종결 금지
- 문장 말미 마침표 미사용
- 단문 나열식 금지

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 7. 표·다이어그램 HTML 형식
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
표:
<p class="table-title">표 N. 제목</p><table class="proposal-table"><thead><tr><th>컬럼1</th><th>컬럼2</th></tr></thead><tbody><tr><td>내용</td><td>내용</td></tr></tbody></table>

다이어그램:
<div class="diagram"><div class="diagram-row"><div class="diagram-box">내용</div><div class="diagram-arrow">→</div><div class="diagram-box highlight">강조</div></div></div>
<p class="figure-title">그림 N. 제목</p>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 8. 출처 표기 규칙
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- □ 블록 1개당 출처 1개 이상
- 허용: 정부·공공기관 보고서, 학술논문, 공식 통계, 주요 언론
- 금지: 위키피디아, 블로그, 존재하지 않는 자료 임의 생성
- 형식: <p class="citation">출처: 기관명(발행연도.월), 제목</p>
- 위치: 해당 □ 블록 내용 바로 아래
"""

DEFAULT_SECTIONS = [
    "1. 구조 진단(Structure Diagnosis)",
    "2. 목표·전략체계(Strategy Architecture)",
    "3. 실행 설계(Implementation Design)",
    "4. 성과·평가체계(Impact)",
    "5. 수행방법론(Method & QA)",
]


def get_api_key() -> str:
    try:
        value = st.secrets["ANTHROPIC_API_KEY"]
        if value:
            return str(value).strip()
    except Exception:
        pass
    return os.getenv("ANTHROPIC_API_KEY", "").strip()


def anthropic_headers() -> Dict[str, str]:
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY가 없습니다")
    return {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }


def pdf_to_base64(file_bytes: bytes) -> str:
    return base64.b64encode(file_bytes).decode("utf-8")


def safe_decode_text(file_bytes: bytes) -> str:
    for enc in ("utf-8", "cp949", "euc-kr", "utf-16"):
        try:
            return file_bytes.decode(enc)
        except Exception:
            continue
    return file_bytes.decode("utf-8", errors="ignore")


def extract_marked_block(raw: str, marker: str, next_marker: Optional[str]) -> str:
    start = raw.find(marker)
    if start == -1:
        return ""
    content_start = start + len(marker)
    end = raw.find(next_marker, content_start) if next_marker else -1
    if end == -1:
        end = len(raw)
    return raw[content_start:end].strip()


def parse_directions(raw: str) -> Dict[str, str]:
    result = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line or ": " not in line:
            continue
        key, value = line.split(": ", 1)
        result[key.strip()] = value.strip()
    return result


def make_uploaded_content(uploaded_file, instruction: str) -> List[Dict[str, Any]]:
    name = uploaded_file.name.lower()
    file_bytes = uploaded_file.getvalue()

    if name.endswith(".pdf"):
        return [
            {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": pdf_to_base64(file_bytes),
                },
            },
            {"type": "text", "text": instruction},
        ]

    text = safe_decode_text(file_bytes)
    return [
        {"type": "text", "text": instruction + "\n\n---\n" + text[:15000]}
    ]


def call_claude(
    system: str,
    messages: List[Dict[str, Any]],
    max_tokens: int = 4000,
    use_web_search: bool = False,
    model: str = DEFAULT_MODEL,
) -> Dict[str, Any]:
    body: Dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "system": system,
        "messages": messages,
    }

    # 안정성을 위해 기본 웹 검색 도구 사용
    if use_web_search:
        body["tools"] = [
            {
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 5,
            }
        ]

    try:
        response = requests.post(
            API_URL,
            headers=anthropic_headers(),
            json=body,
            timeout=300,
        )
    except requests.RequestException as e:
        raise RuntimeError(f"네트워크 오류: {e}") from e

    if response.status_code >= 400:
        try:
            err = response.json()
            raise RuntimeError(f"API 오류 {response.status_code}: {err}")
        except Exception:
            raise RuntimeError(f"API 오류 {response.status_code}: {response.text}")

    return response.json()


def call_claude_text(
    system: str,
    messages: List[Dict[str, Any]],
    max_tokens: int = 4000,
    use_web_search: bool = False,
    model: str = DEFAULT_MODEL,
) -> str:
    current_messages = messages[:]

    for _ in range(3):
        data = call_claude(
            system=system,
            messages=current_messages,
            max_tokens=max_tokens,
            use_web_search=use_web_search,
            model=model,
        )

        content = data.get("content", [])
        text_parts = [
            block.get("text", "")
            for block in content
            if block.get("type") == "text" and block.get("text")
        ]
        final_text = "\n".join(text_parts).strip()

        if data.get("stop_reason") == "pause_turn":
            current_messages = current_messages + [
                {"role": "assistant", "content": content}
            ]
            continue

        if final_text:
            return final_text

        raise RuntimeError("Claude 응답 텍스트가 비어 있습니다")

    raise RuntimeError("응답이 pause_turn 상태로 반복되어 완료되지 않았습니다")


def analyze_rfp(uploaded_file, use_web_search: bool) -> Dict[str, Any]:
    instruction = """위 RFP 문서를 STSI 발주 의도 역설계 방식으로 분석하여 아래 형식으로 정확히 응답하세요.

핵심 분석 관점:
- "무엇을 하라는가?"(X) → "왜 지금 이 과제를 내는가? 발주자의 고민은 무엇인가?"(O)
- 이 사업의 구조적 병목(bottleneck)은 무엇인가?
- 어떤 정책 리스크가 존재하는가?

##TITLE##
(과제명을 한 줄로)

##SUMMARY##
(발주 의도 역설계 관점의 핵심 분석 300자 이내)

##SECTIONS##
(제안서 작성 목차 항목들, 한 줄에 하나씩. 없으면 STSI 표준 목차 사용)

##DIRECTIONS##
(목차 항목명): (발주 의도·병목·정책 리스크 관점에서의 작성 방향 2~3문장)
"""

    content = make_uploaded_content(uploaded_file, instruction)

    raw = call_claude_text(
        system="당신은 STSI 과제수주 전략 전문가입니다. 요청된 마커 형식으로만 응답하세요.",
        messages=[{"role": "user", "content": content}],
        max_tokens=4000,
        use_web_search=use_web_search,
    )

    title = extract_marked_block(raw, "##TITLE##", "##SUMMARY##")
    summary = extract_marked_block(raw, "##SUMMARY##", "##SECTIONS##")
    sections_raw = extract_marked_block(raw, "##SECTIONS##", "##DIRECTIONS##")
    directions_raw = extract_marked_block(raw, "##DIRECTIONS##", None)

    sections = [s.strip() for s in sections_raw.splitlines() if s.strip()] or DEFAULT_SECTIONS
    directions = parse_directions(directions_raw)

    result = {
        "title": title.strip(),
        "summary": summary.strip(),
        "sections": sections,
        "directions": directions,
        "document_block": None,
        "text_context": "",
    }

    if uploaded_file.name.lower().endswith(".pdf"):
        result["document_block"] = content[0]
    else:
        joined_text = ""
        if content and content[0].get("type") == "text":
            joined_text = content[0].get("text", "")
        result["text_context"] = joined_text[:15000]

    return result


def analyze_form(uploaded_file, use_web_search: bool) -> Dict[str, Any]:
    instruction = """위 연구계획서 양식을 분석하여 아래 형식으로 정확히 응답하세요.

##SUMMARY##
(양식 구조 설명 100자 이내)

##SECTIONS##
(양식에 있는 작성 항목들, 한 줄에 하나씩)
"""

    content = make_uploaded_content(uploaded_file, instruction)

    raw = call_claude_text(
        system="연구계획서 양식 분석 전문가. 요청된 마커 형식으로만 응답하세요.",
        messages=[{"role": "user", "content": content}],
        max_tokens=2500,
        use_web_search=use_web_search,
    )

    summary = extract_marked_block(raw, "##SUMMARY##", "##SECTIONS##")
    sections_raw = extract_marked_block(raw, "##SECTIONS##", None)
    sections = [s.strip() for s in sections_raw.splitlines() if s.strip()]

    result = {
        "summary": summary.strip(),
        "sections": sections,
        "document_block": None,
        "text_context": "",
    }

    if uploaded_file.name.lower().endswith(".pdf"):
        result["document_block"] = content[0]
    else:
        joined_text = ""
        if content and content[0].get("type") == "text":
            joined_text = content[0].get("text", "")
        result["text_context"] = joined_text[:15000]

    return result


def generate_section(
    section_name: str,
    direction: str,
    title: str,
    rfp_summary: str,
    section_list: List[str],
    form_data: Optional[Dict[str, Any]],
    rfp_data: Optional[Dict[str, Any]],
    use_web_search: bool,
) -> str:
    volume_guide = """
## 분량 기준
- 이 섹션 단독으로 A4 기준 5페이지 이상 작성
- □ 블록 6개 이상 작성
- □ 블록 1개당 ○ 논점 3개 이상
- ○ 논점 1개당 * 설명 3개 이상
- □ 블록 1개당 출처 1개 이상
- 절대 요약·생략하지 말고 최대한 구체적으로 서술
"""

    extra_context_parts = []

    if rfp_data and rfp_data.get("text_context"):
        extra_context_parts.append("## RFP 원문 일부\n" + rfp_data["text_context"])

    if form_data and form_data.get("text_context"):
        extra_context_parts.append("## 양식 원문 일부\n" + form_data["text_context"])

    extra_context = "\n\n".join(extra_context_parts)

    prompt = f"""
## 과제 기본정보
- 과제명: {title}

## RFP 핵심 내용
{rfp_summary}

## 전체 목차
{chr(10).join(section_list)}

## 지금 작성할 섹션
{section_name}

작성 방향
{direction or "RFP와 STSI 원칙에 따라 자동 판단"}

{volume_guide}

{extra_context}

위 섹션만 작성하십시오.
## 헤더로 시작하고 STSI 병목 중심 서술, 필살기 4문장, 6종 표준 도표, 명사형 종결 문체를 준수하십시오.
"""

    content_blocks: List[Dict[str, Any]] = []

    if form_data and form_data.get("document_block"):
        content_blocks.append(form_data["document_block"])

    if rfp_data and rfp_data.get("document_block"):
        content_blocks.append(rfp_data["document_block"])

    content_blocks.append({"type": "text", "text": prompt})

    return call_claude_text(
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content_blocks}],
        max_tokens=12000,
        use_web_search=use_web_search,
    )


st.set_page_config(page_title="연구제안서 AI 작성 도우미", layout="wide")
st.title("연구제안서 AI 작성 도우미")
st.caption("RFP와 양식을 업로드하면 제안서 초안을 생성")

if "rfp_data" not in st.session_state:
    st.session_state.rfp_data = None
if "form_data" not in st.session_state:
    st.session_state.form_data = None
if "generated_text" not in st.session_state:
    st.session_state.generated_text = ""
if "section_directions" not in st.session_state:
    st.session_state.section_directions = {}

api_key = get_api_key()
api_ready = bool(api_key)

with st.sidebar:
    st.subheader("설정")
    if api_ready:
        st.success("API 키 확인 완료")
    else:
        st.warning("API 키 없음")
        st.caption("앱 화면은 열리지만 분석·생성 기능은 동작하지 않음")
        st.caption("Streamlit Cloud의 App settings > Secrets에 ANTHROPIC_API_KEY를 추가하면 사용 가능")

    use_web_search = st.checkbox(
        "웹 검색 사용",
        value=False,
        help="추가 비용이 발생할 수 있으며, Anthropic Console에서 웹 검색이 활성화되어 있어야 함",
    )

    if st.button("초기화"):
        st.session_state.rfp_data = None
        st.session_state.form_data = None
        st.session_state.generated_text = ""
        st.session_state.section_directions = {}
        st.rerun()

if not api_ready:
    st.info("현재는 화면만 열리는 상태입니다. API 키를 넣기 전까지 분석·생성 버튼은 비활성화됩니다.")

col1, col2 = st.columns(2)

with col1:
    rfp_file = st.file_uploader("① RFP / 공모 문서", type=["pdf", "txt"], key="rfp")
    if st.button("RFP 분석", disabled=(not api_ready or rfp_file is None)):
        with st.spinner("RFP 분석 중"):
            try:
                st.session_state.rfp_data = analyze_rfp(rfp_file, use_web_search=use_web_search)
                st.session_state.generated_text = ""
                st.success("RFP 분석 완료")
            except Exception as e:
                st.error(f"RFP 분석 오류: {e}")

with col2:
    form_file = st.file_uploader("② 연구계획서 양식", type=["pdf", "txt"], key="form")
    if st.button("양식 분석", disabled=(not api_ready or form_file is None)):
        with st.spinner("양식 분석 중"):
            try:
                st.session_state.form_data = analyze_form(form_file, use_web_search=use_web_search)
                st.session_state.generated_text = ""
                st.success("양식 분석 완료")
            except Exception as e:
                st.error(f"양식 분석 오류: {e}")

rfp_data = st.session_state.rfp_data
form_data = st.session_state.form_data

title_default = ""
if rfp_data and rfp_data.get("title"):
    title_default = rfp_data["title"]

title = st.text_input("과제명", value=title_default)

if rfp_data and rfp_data.get("summary"):
    st.info(f"RFP 요약: {rfp_data['summary']}")

default_sections = DEFAULT_SECTIONS
if form_data and form_data.get("sections"):
    default_sections = form_data["sections"]
elif rfp_data and rfp_data.get("sections"):
    default_sections = rfp_data["sections"]

sections_text = st.text_area(
    "목차 항목",
    value="\n".join(default_sections),
    height=180
)
section_list = [s.strip() for s in sections_text.splitlines() if s.strip()]

st.subheader("목차별 방향성")
section_directions = {}
for sec in section_list:
    default_dir = ""
    if rfp_data and sec in rfp_data.get("directions", {}):
        default_dir = rfp_data["directions"][sec]
    section_directions[sec] = st.text_area(
        sec,
        value=default_dir,
        height=80,
        key=f"dir_{sec}"
    )

generate_disabled = (not api_ready) or (not title.strip()) or (len(section_list) == 0)

if st.button("제안서 생성", type="primary", disabled=generate_disabled):
    full_text = ""
    progress = st.progress(0)
    status = st.empty()

    for idx, sec in enumerate(section_list, start=1):
        status.write(f"[{idx}/{len(section_list)}] {sec} 생성 중")
        try:
            part = generate_section(
                section_name=sec,
                direction=section_directions.get(sec, ""),
                title=title,
                rfp_summary=rfp_data["summary"] if rfp_data else "",
                section_list=section_list,
                form_data=form_data,
                rfp_data=rfp_data,
                use_web_search=use_web_search,
            )
            full_text += ("\n\n" if full_text else "") + part
            st.session_state.generated_text = full_text
            progress.progress(idx / len(section_list))
        except Exception as e:
            st.error(f"{sec} 생성 오류: {e}")
            break

    status.write("완료")

if st.session_state.generated_text:
    st.subheader("생성 결과")
    st.text_area(
        "결과 텍스트",
        value=st.session_state.generated_text,
        height=600
    )
    st.download_button(
        label="TXT 다운로드",
        data=st.session_state.generated_text.encode("utf-8"),
        file_name="proposal_output.txt",
        mime="text/plain",
    )
