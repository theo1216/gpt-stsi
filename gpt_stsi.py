import os
import base64
from io import BytesIO
from typing import Optional, Dict, List

import requests
import streamlit as st
from pypdf import PdfReader

API_KEY = os.getenv("ANTHROPIC_API_KEY")
API_URL = "https://api.anthropic.com/v1/messages"

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

### 필살기 4문장 패턴 (각 □ 블록에 반드시 반영)
각 □ 블록 서술은 아래 4개 축을 모두 포함:
1. "본 과제의 핵심 병목은 A이며, 원인은 B임"
2. "따라서 해결전략은 C(제도)·D(기술)·E(산업) 3축으로 설계"
3. "성과는 F지표로 측정하며, 데이터는 G에서 확보"
4. "정책 실패 리스크 H를 방지하기 위해 I 거버넌스 설계"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 4. STSI 표준 목차 프레임 (RFP 목차 없을 시 기본 적용)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1) 구조 진단(Structure Diagnosis): 정책환경·이해관계자 지도·산업·기술·재정 제약·핵심 병목
2) 목표·전략체계(Strategy Architecture): 비전→목표→전략(결정 축)→실행과제 트리구조. "정책문장"이 아닌 "의사결정 구조"
3) 실행 설계(Implementation Design): 단계별 로드맵·과제패키지·거버넌스(역할/의사결정 흐름)·운영체계
4) 성과·평가체계(Impact): KPI+측정방법+데이터소스·재정 지속가능성·리스크 레지스터
5) 수행방법론(Method & QA): 연구방법·검증루프·품질관리

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 5. 6종 표준 도표 (최소 4개 이상 반드시 삽입)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
① 문제-목표-수단 트리
② 이해관계자/기관 맵
③ 로드맵 타임라인
④ 거버넌스 구조도
⑤ 예산·재정 구조
⑥ TRL 매트릭스

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 6. 문체 규칙 (반드시 준수)
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
## 8. 출처 표기 규칙 (반드시 준수)
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


def anthropic_headers() -> Dict[str, str]:
    if not API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY 환경변수가 없습니다.")
    return {
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }


def pdf_to_base64(file_bytes: bytes) -> str:
    return base64.b64encode(file_bytes).decode("utf-8")


def try_extract_pdf_text(file_bytes: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(file_bytes))
        texts = []
        for page in reader.pages:
            txt = page.extract_text() or ""
            if txt.strip():
                texts.append(txt)
        return "\n".join(texts)
    except Exception:
        return ""


def call_claude(
    system: str,
    messages: List[Dict],
    search: bool = False,
    max_tokens: int = 4000,
    model: str = "claude-sonnet-4-20250514",
) -> Dict:
    body = {
        "model": model,
        "max_tokens": max_tokens,
        "system": system,
        "messages": messages,
    }

    if search:
        body["tools"] = [
            {
                "type": "web_search_20250305",
                "name": "web_search",
            }
        ]

    res = requests.post(API_URL, headers=anthropic_headers(), json=body, timeout=300)
    if res.status_code >= 400:
        raise RuntimeError(f"API 오류 {res.status_code}: {res.text}")
    return res.json()


def claude_with_search(system: str, user_content, max_tokens: int = 6000) -> str:
    messages = [{"role": "user", "content": user_content}]
    final_text = ""

    for _ in range(10):
        data = call_claude(system=system, messages=messages, search=True, max_tokens=max_tokens)
        content = data.get("content", [])
        text = "\n".join(block.get("text", "") for block in content if block.get("type") == "text").strip()
        if text:
            final_text = text

        stop_reason = data.get("stop_reason")
        if stop_reason == "end_turn":
            break

        if stop_reason == "tool_use":
            tool_results = []
            for block in content:
                if block.get("type") == "tool_use":
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block["id"],
                        "content": []
                    })
            messages = messages + [
                {"role": "assistant", "content": content},
                {"role": "user", "content": tool_results},
            ]
            continue

        break

    if not final_text:
        raise RuntimeError("Claude 응답 텍스트를 받지 못했습니다.")
    return final_text


def extract_marked_block(raw: str, marker: str, next_marker: Optional[str]) -> str:
    start = raw.find(marker)
    if start == -1:
        return ""
    content_start = start + len(marker)
    if next_marker:
        end = raw.find(next_marker, content_start)
        if end == -1:
            end = len(raw)
    else:
        end = len(raw)
    return raw[content_start:end].strip()


def analyze_rfp(file_name: str, file_bytes: bytes):
    base64_pdf = pdf_to_base64(file_bytes)

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
(목차 항목명): (작성 방향 2~3문장)
"""

    user_content = [
        {
            "type": "document",
            "source": {
                "type": "base64",
                "media_type": "application/pdf",
                "data": base64_pdf,
            },
        },
        {"type": "text", "text": instruction},
    ]

    data = call_claude(
        system="당신은 STSI 과제수주 전략 전문가입니다. 요청된 마커 형식으로만 응답하세요.",
        messages=[{"role": "user", "content": user_content}],
        max_tokens=4000,
        search=False,
    )

    raw = "\n".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text").strip()
    if not raw:
        raise RuntimeError("RFP 분석 결과가 비어 있습니다.")

    title = extract_marked_block(raw, "##TITLE##", "##SUMMARY##")
    summary = extract_marked_block(raw, "##SUMMARY##", "##SECTIONS##")
    sections_raw = extract_marked_block(raw, "##SECTIONS##", "##DIRECTIONS##")
    directions_raw = extract_marked_block(raw, "##DIRECTIONS##", None)

    sections = [line.strip() for line in sections_raw.splitlines() if line.strip()] if sections_raw else DEFAULT_SECTIONS
    directions = {}

    for line in directions_raw.splitlines():
        if ": " in line:
            key, val = line.split(": ", 1)
            directions[key.strip()] = val.strip()

    return {
        "title": title.strip(),
        "summary": summary.strip(),
        "sections": sections,
        "directions": directions,
        "base64": base64_pdf,
        "text_preview": try_extract_pdf_text(file_bytes)[:2000],
    }


def analyze_form(file_bytes: bytes):
    base64_pdf = pdf_to_base64(file_bytes)

    instruction = """위 연구계획서 양식을 분석하여 아래 형식으로 정확히 응답하세요.

##SUMMARY##
(양식 구조 설명 100자 이내)

##SECTIONS##
(양식에 있는 작성 항목들, 한 줄에 하나씩)
"""

    user_content = [
        {
            "type": "document",
            "source": {
                "type": "base64",
                "media_type": "application/pdf",
                "data": base64_pdf,
            },
        },
        {"type": "text", "text": instruction},
    ]

    data = call_claude(
        system="연구계획서 양식 분석 전문가. 요청된 마커 형식으로만 응답하세요.",
        messages=[{"role": "user", "content": user_content}],
        max_tokens=3000,
        search=False,
    )

    raw = "\n".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text").strip()
    if not raw:
        raise RuntimeError("양식 분석 결과가 비어 있습니다.")

    summary = extract_marked_block(raw, "##SUMMARY##", "##SECTIONS##")
    sections_raw = extract_marked_block(raw, "##SECTIONS##", None)
    sections = [line.strip() for line in sections_raw.splitlines() if line.strip()] if sections_raw else []

    return {
        "summary": summary.strip(),
        "sections": sections,
        "base64": base64_pdf,
    }


def generate_section(
    section_name: str,
    direction: str,
    title: str,
    rfp_summary: str,
    section_list: List[str],
    form_base64: Optional[str] = None,
    rfp_base64: Optional[str] = None,
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

    section_prompt = f"""
## 과제 기본정보
- 과제명: {title}

## RFP 핵심 내용
{rfp_summary}

## 전체 목차
{chr(10).join(section_list)}

## 지금 작성할 섹션
{section_name}

작성 방향:
{direction or "RFP와 STSI 원칙에 따라 자동 판단"}

{volume_guide}

위 섹션만 작성하십시오.
## 헤더로 시작하고 STSI 병목 중심 서술, 필살기 4문장, 6종 표준 도표, 명사형 종결 문체를 준수하십시오.
"""

    content_blocks = []

    if form_base64:
        content_blocks.append({
            "type": "document",
            "source": {
                "type": "base64",
                "media_type": "application/pdf",
                "data": form_base64,
            },
        })

    if rfp_base64:
        content_blocks.append({
            "type": "document",
            "source": {
                "type": "base64",
                "media_type": "application/pdf",
                "data": rfp_base64,
            },
        })

    content_blocks.append({"type": "text", "text": section_prompt})

    return claude_with_search(SYSTEM_PROMPT, content_blocks, max_tokens=12000)


st.set_page_config(page_title="연구제안서 AI 작성 도우미", layout="wide")
st.title("연구제안서 AI 작성 도우미")
st.caption("RFP와 양식을 업로드하면 제안서를 생성")

if "rfp_data" not in st.session_state:
    st.session_state.rfp_data = None
if "form_data" not in st.session_state:
    st.session_state.form_data = None
if "generated_text" not in st.session_state:
    st.session_state.generated_text = ""
if "section_directions" not in st.session_state:
    st.session_state.section_directions = {}

with st.sidebar:
    st.subheader("설정")
    if not API_KEY:
        st.error("ANTHROPIC_API_KEY가 없습니다")
    else:
        st.success("API 키 확인 완료")

col1, col2 = st.columns(2)

with col1:
    rfp_file = st.file_uploader("① RFP / 공모 문서", type=["pdf"], key="rfp")
    if rfp_file and st.button("RFP 분석"):
        with st.spinner("RFP 분석 중"):
            st.session_state.rfp_data = analyze_rfp(rfp_file.name, rfp_file.read())
            st.session_state.generated_text = ""
        st.success("RFP 분석 완료")

with col2:
    form_file = st.file_uploader("② 연구계획서 양식", type=["pdf"], key="form")
    if form_file and st.button("양식 분석"):
        with st.spinner("양식 분석 중"):
            st.session_state.form_data = analyze_form(form_file.read())
            st.session_state.generated_text = ""
        st.success("양식 분석 완료")

rfp_data = st.session_state.rfp_data
form_data = st.session_state.form_data

title = st.text_input(
    "과제명",
    value=(rfp_data["title"] if rfp_data and rfp_data.get("title") else "")
)

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

if st.button("제안서 생성", type="primary"):
    if not title.strip():
        st.error("과제명이 필요합니다")
    elif not section_list:
        st.error("목차가 필요합니다")
    else:
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
                    form_base64=form_data["base64"] if form_data else None,
                    rfp_base64=rfp_data["base64"] if rfp_data else None,
                )
                full_text += ("\n\n" if full_text else "") + part
                st.session_state.generated_text = full_text
            except Exception as e:
                st.error(f"{sec} 생성 오류: {e}")
                break
            progress.progress(idx / len(section_list))

        status.write("완료")

if st.session_state.generated_text:
    st.subheader("생성 결과")
    st.text_area("결과 텍스트", value=st.session_state.generated_text, height=600)
    st.download_button(
        label="TXT 다운로드",
        data=st.session_state.generated_text.encode("utf-8"),
        file_name="proposal_output.txt",
        mime="text/plain",

    )
