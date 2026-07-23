import time
from flask import Flask, Response, jsonify, render_template_string, request
import state
from hazard_zones import get_confirmed_zones
from coss import upload_data, GPS_CNT

app = Flask(__name__)

PAGE = r"""
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta
    name="viewport"
    content="width=device-width, initial-scale=1"
  >
  <title>AI 보행 보조 모니터링</title>

  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link
    href="https://fonts.googleapis.com/css2?family=Manrope:wght@500;700;800&family=Noto+Sans+KR:wght@400;500;700;800;900&display=swap"
    rel="stylesheet"
  >

  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

  <style>
    :root {
      --page-bg-1: #d9e2ec;
      --page-bg-2: #cbd6e3;

      --surface: rgba(247, 250, 253, 0.96);
      --surface-strong: #ffffff;
      --surface-soft: #eef3f8;

      --ink-900: #172942;
      --ink-700: #41526a;
      --ink-500: #6e7e91;
      --ink-300: #aab6c4;

      --line: #d6e0ea;
      --line-strong: #bdcad8;

      --blue-700: #173f8f;
      --blue-600: #245bbd;
      --blue-500: #3572d4;
      --blue-200: #dbe8fb;
      --blue-100: #eef5ff;

      --green: #16a36c;
      --danger: #dc2626;
      --danger-dark: #b91c1c;
      --danger-soft: #fef1f1;

      --shadow:
        0 22px 60px rgba(53, 73, 99, 0.16);

      --card-shadow:
        0 8px 22px rgba(49, 70, 96, 0.08);

      --radius-xl: 28px;
      --radius-lg: 22px;
      --radius-md: 16px;
    }

    * {
      box-sizing: border-box;
    }

    html,
    body {
      margin: 0;
      min-height: 100%;
    }

    body {
      padding: 24px;

      color: var(--ink-900);

      font-family:
        "Noto Sans KR",
        "Manrope",
        sans-serif;

      background:
        radial-gradient(
          circle at 14% 10%,
          rgba(255, 255, 255, 0.92),
          transparent 28%
        ),
        radial-gradient(
          circle at 88% 88%,
          rgba(181, 198, 218, 0.55),
          transparent 34%
        ),
        linear-gradient(
          145deg,
          var(--page-bg-1),
          var(--page-bg-2)
        );
    }

    .dashboard {
      width: min(1780px, 100%);
      margin: 0 auto;
      padding: 30px;

      border:
        1px solid rgba(255, 255, 255, 0.78);

      border-radius: var(--radius-xl);

      background:
        linear-gradient(
          145deg,
          rgba(255, 255, 255, 0.92),
          rgba(240, 245, 250, 0.94)
        );

      box-shadow: var(--shadow);
      backdrop-filter: blur(18px);
    }

    .header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 24px;
      margin-bottom: 24px;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 18px;
    }

    .brand-icon {
      width: 74px;
      height: 64px;

      display: grid;
      place-items: center;

      color: var(--blue-700);

      border: 1px solid var(--line);
      border-radius: 21px;

      background:
        linear-gradient(
          145deg,
          #ffffff,
          #e8eef5
        );

      box-shadow: var(--card-shadow);
    }

    .brand-icon svg {
      width: 48px;
      height: 48px;
    }

    .brand-copy h1 {
      margin: 0;

      font-size: clamp(30px, 3vw, 48px);
      line-height: 1.08;
      letter-spacing: -0.045em;
    }

    .brand-copy p {
      margin: 9px 0 0;

      color: var(--ink-500);
      font-size: clamp(15px, 1.2vw, 20px);
    }

    .live-badge {
      min-height: 60px;
      padding: 0 22px;

      display: flex;
      align-items: center;
      gap: 16px;

      border: 1px solid var(--line);
      border-radius: 19px;

      background: rgba(255, 255, 255, 0.88);
      box-shadow: var(--card-shadow);
    }

    .live-main {
      display: flex;
      align-items: center;
      gap: 9px;

      color: var(--blue-700);
      font-size: 19px;
      font-weight: 900;
    }

    .live-dot {
      width: 12px;
      height: 12px;

      border-radius: 50%;

      background: var(--blue-600);

      box-shadow:
        0 0 0 6px rgba(36, 91, 189, 0.1);
    }

    .live-divider {
      width: 1px;
      height: 26px;
      background: var(--line);
    }

    .live-status {
      color: var(--ink-700);
      font-weight: 700;
    }

    .main-shell {
      padding: 20px;

      border: 1px solid var(--line);
      border-radius: 24px;

      background: rgba(248, 251, 254, 0.9);
    }

    .content-grid {
      display: grid;
      grid-template-columns:
        minmax(0, 1.4fr)
        minmax(340px, 1fr);

      align-items: stretch;

      gap: 24px;
    }

    .camera-column,
    .map-column {
      display: flex;
      flex-direction: column;

      height: 100%;
    }

    .section-title {
      min-height: 42px;

      display: flex;
      align-items: center;
      gap: 11px;

      margin-bottom: 14px;

      font-size: 20px;
      font-weight: 900;
    }

    .section-icon {
      width: 38px;
      height: 38px;

      display: grid;
      place-items: center;

      color: var(--blue-600);

      border-radius: 12px;
      background: var(--blue-100);
    }

    .section-icon svg {
      width: 22px;
      height: 22px;
    }

    .camera-card,
    .map-card {
      flex: 1;

      display: flex;
      flex-direction: column;

      padding: 11px;

      border: 1px solid var(--line);
      border-radius: var(--radius-lg);

      background: var(--surface-strong);
      box-shadow: var(--card-shadow);
    }

    .camera-frame,
    .map-frame {
      position: relative;

      flex: 1;
      width: 100%;
      min-height: 320px;

      overflow: hidden;

      border-radius: 15px;
      background: #101a28;
    }

    .camera-frame img {
      width: 100%;
      height: 100%;

      display: block;

      object-fit: contain;
      background: #0d1420;
    }

    .map-frame #map {
      width: 100%;
      height: 100%;
      min-height: 320px;
    }

    .map-info {
      position: absolute;
      top: 14px;
      left: 14px;
      right: 14px;
      z-index: 500;

      display: flex;
      justify-content: center;

      pointer-events: none;
    }

    .map-info-chip {
      padding: 8px 16px;

      color: #ffffff;

      border-radius: 12px;
      background: rgba(16, 31, 52, 0.86);

      font-size: 13px;
      font-weight: 700;

      box-shadow: 0 8px 22px rgba(0, 0, 0, 0.2);
      backdrop-filter: blur(12px);
    }

    .camera-overlay {
      position: absolute;
      top: 14px;
      left: 14px;
      right: 14px;

      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;

      pointer-events: none;
    }

    .overlay-group {
      display: flex;
      gap: 9px;
    }

    .overlay-chip {
      min-height: 44px;
      padding: 0 14px;

      display: flex;
      align-items: center;
      gap: 8px;

      color: #ffffff;

      border:
        1px solid rgba(255, 255, 255, 0.1);

      border-radius: 12px;

      background: rgba(16, 31, 52, 0.86);

      box-shadow:
        0 8px 22px rgba(0, 0, 0, 0.2);

      backdrop-filter: blur(12px);
    }

    .overlay-chip svg {
      width: 19px;
      height: 19px;
    }

    .overlay-muted {
      color: rgba(255, 255, 255, 0.72);
      font-size: 13px;
    }

    .overlay-value {
      font-weight: 900;
    }

    .overlay-normal {
      color: #66d6ad;
      font-weight: 900;
    }

    .camera-corner {
      position: absolute;

      width: 30px;
      height: 30px;

      border-style: solid;
      border-color: rgba(255, 255, 255, 0.86);
    }

    .corner-tl {
      top: 14px;
      left: 14px;
      border-width: 2px 0 0 2px;
    }

    .corner-tr {
      top: 14px;
      right: 14px;
      border-width: 2px 2px 0 0;
    }

    .corner-bl {
      bottom: 14px;
      left: 14px;
      border-width: 0 0 2px 2px;
    }

    .corner-br {
      right: 14px;
      bottom: 14px;
      border-width: 0 2px 2px 0;
    }

    .distance-section {
      margin-top: 24px;
    }

    .distance-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 15px;
    }

    .distance-card {
      display: grid;
      grid-template-columns: 88px 1fr;
      align-items: center;
      gap: 18px;

      padding: 21px;

      border: 1px solid var(--line);
      border-radius: var(--radius-lg);

      background: var(--surface-strong);
      box-shadow: var(--card-shadow);

      transition:
        border-color 0.18s ease,
        box-shadow 0.18s ease;
    }

    .distance-card.active {
      border-color: var(--danger);
      background: var(--surface-strong);

      box-shadow:
        0 12px 28px rgba(220, 38, 38, 0.16),
        inset 0 0 0 1px rgba(220, 38, 38, 0.1);
    }

    .direction-icon {
      width: 82px;
      height: 82px;

      display: grid;
      place-items: center;

      color: var(--ink-900);

      border: 1px solid var(--line);
      border-radius: 50%;

      background:
        linear-gradient(
          145deg,
          #f7f9fc,
          #e3eaf2
        );
    }

    .distance-card.active .direction-icon {
      color: #ffffff;

      border-color: var(--danger-dark);

      background:
        linear-gradient(
          145deg,
          var(--danger),
          var(--danger-dark)
        );

      box-shadow:
        0 9px 20px rgba(220, 38, 38, 0.3);
    }

    .direction-icon svg {
      width: 44px;
      height: 44px;
    }

    .distance-label {
      margin-bottom: 8px;

      font-size: 21px;
      font-weight: 900;
    }

    .distance-card.active .distance-label {
      color: var(--danger);
    }

    .distance-value-row {
      min-height: 58px;

      display: flex;
      align-items: baseline;
      gap: 8px;
    }

    .distance-value {
      font-family: "Manrope", sans-serif;
      font-size: clamp(42px, 4vw, 58px);
      line-height: 1;
      font-weight: 800;
      letter-spacing: -0.05em;
    }

    .distance-card.active .distance-value {
      color: var(--danger);
    }

    .distance-value.unavailable {
      color: var(--ink-500);
      font-size: 24px;
      letter-spacing: -0.03em;
    }

    .distance-unit {
      font-size: 18px;
      font-weight: 800;
    }

    .distance-progress {
      width: 100%;
      height: 7px;

      margin-top: 12px;

      overflow: hidden;

      border-radius: 999px;
      background: #e4eaf1;
    }

    .distance-progress-fill {
      width: 0;
      height: 100%;

      border-radius: inherit;

      background:
        linear-gradient(
          90deg,
          #4c89eb,
          #245bbd
        );

      transition: width 0.22s ease;
    }

    .distance-card.active .distance-progress-fill {
      background:
        linear-gradient(
          90deg,
          var(--danger),
          var(--danger-dark)
        );
    }

    .distance-scale {
      display: flex;
      justify-content: space-between;

      margin-top: 7px;

      color: var(--ink-300);
      font-size: 12px;
    }

    .card-warning {
      display: none;
      align-items: center;
      gap: 10px;

      margin-top: 12px;
      padding: 12px 15px;

      border-radius: 10px;

      background: var(--danger-soft);
      color: var(--danger);

      font-size: 18px;
      font-weight: 800;
      line-height: 1.35;
    }

    .card-warning.show {
      display: flex;
    }

    .card-warning svg {
      width: 22px;
      height: 22px;
      flex-shrink: 0;
    }

    .status-panel {
      margin-top: 20px;
      padding: 22px 26px;

      display: grid;
      grid-template-columns: repeat(3, 1fr);

      border: 1px solid var(--line);
      border-radius: var(--radius-lg);

      background: rgba(255, 255, 255, 0.86);
      box-shadow: var(--card-shadow);
    }

    .status-item {
      min-width: 0;

      display: flex;
      align-items: center;
      gap: 16px;

      padding: 0 24px;
    }

    .status-item:first-child {
      padding-left: 0;
    }

    .status-item:last-child {
      padding-right: 0;
    }

    .status-item + .status-item {
      border-left: 1px solid var(--line);
    }

    .status-icon {
      flex-shrink: 0;

      width: 62px;
      height: 62px;

      display: grid;
      place-items: center;

      color: var(--blue-700);

      border-radius: 50%;

      background:
        linear-gradient(
          145deg,
          #edf3fa,
          #dbe6f2
        );
    }

    .status-icon svg {
      width: 30px;
      height: 30px;
    }

    .status-title {
      margin-bottom: 8px;

      font-size: 20px;
      font-weight: 900;
    }

    .status-value {
      display: flex;
      align-items: center;
      gap: 9px;

      color: var(--ink-500);
      font-size: 19px;
    }

    .status-dot {
      width: 11px;
      height: 11px;

      border-radius: 50%;
      background: var(--green);
    }

    .status-dot.off {
      background: #9aa8b8;
    }

    .summary-overlay {
      display: none;
      position: fixed;
      inset: 0;
      z-index: 2000;

      align-items: center;
      justify-content: center;

      padding: 24px;

      background: rgba(23, 41, 66, 0.6);
      backdrop-filter: blur(5px);
    }

    .summary-overlay.show {
      display: flex;
    }

    .summary-modal {
      width: min(720px, 96vw);
      max-height: 88vh;

      padding: 52px 48px;

      display: flex;
      flex-direction: column;
      align-items: center;

      text-align: center;

      border-radius: var(--radius-xl);
      background: var(--surface-strong);

      box-shadow: var(--shadow);

      overflow-y: auto;
    }

    .summary-icon {
      width: 96px;
      height: 96px;
      margin: 0 auto 24px;

      display: grid;
      place-items: center;

      color: var(--blue-600);
      background: var(--blue-100);
      border-radius: 50%;
    }

    .summary-icon svg {
      width: 52px;
      height: 52px;
    }

    .summary-modal h2 {
      margin: 0 0 26px;
      font-size: 34px;
      font-weight: 900;
    }

    .summary-modal p {
      margin: 0 0 36px;

      width: 100%;

      color: var(--ink-700);
      font-size: 21px;
      line-height: 2;
      text-align: center;
      white-space: pre-line;
    }

    .summary-modal button {
      padding: 17px 52px;

      color: #fff;
      border: none;
      border-radius: 15px;
      background: var(--blue-600);

      font-size: 19px;
      font-weight: 800;
      cursor: pointer;
    }

    .summary-modal button:hover {
      background: var(--blue-700);
    }

    @media (max-width: 1080px) {
      .content-grid {
        grid-template-columns: 1fr;
      }

      .camera-column,
      .map-column {
        height: auto;
      }

      .distance-grid {
        grid-template-columns: 1fr;
      }
    }

    @media (max-width: 800px) {
      body {
        padding: 12px;
      }

      .dashboard {
        padding: 18px;
      }

      .header {
        align-items: flex-start;
        flex-direction: column;
      }

      .live-badge {
        width: 100%;
        justify-content: center;
      }

      .distance-card {
        grid-template-columns: 78px 1fr;
        text-align: left;
      }

      .direction-icon {
        width: 72px;
        height: 72px;
      }

      .status-panel {
        grid-template-columns: 1fr;
      }

      .status-item {
        padding: 16px 0;
      }

      .status-item + .status-item {
        border-top: 1px solid var(--line);
        border-left: 0;
      }

      .summary-modal {
        padding: 32px 24px;
      }

      .summary-modal h2 {
        font-size: 26px;
      }

      .summary-modal p {
        font-size: 18px;
      }
    }
  </style>
</head>

<body>
  <main class="dashboard">

    <header class="header">
      <div class="brand">
        <div class="brand-icon">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M4 14.5V9.8a5.8 5.8 0 0 1 5.8-5.8h2.8A7.4 7.4 0 0 1 20 11.4v3.1"></path>
            <path d="M4 14.5h16"></path>
            <path d="M4 14.5 2.8 18h15.4L20 14.5"></path>
            <circle cx="12" cy="9" r="2.1"></circle>
          </svg>
        </div>

        <div class="brand-copy">
          <h1>AI 보행 보조 모니터링</h1>
          <p>실시간 카메라 화면 및 위험구간 지도</p>
        </div>
      </div>

      <div class="live-badge">
        <div class="live-main">
          <span class="live-dot"></span>
          <span>LIVE</span>
        </div>

        <span class="live-divider"></span>

        <span
          class="live-status"
          id="systemStatus"
        >
          시스템 정상 작동 중
        </span>
      </div>
    </header>

    <section class="main-shell">

      <div class="content-grid">

        <section class="camera-column">
          <div class="section-title">
            <span class="section-icon">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path d="M14.5 7H5a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h9.5a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2Z"></path>
                <path d="m16.5 11 4-2v8l-4-2"></path>
              </svg>
            </span>

            <span>실시간 카메라 화면</span>
          </div>

          <div class="camera-card">
            <div class="camera-frame">

              <img
                src="/stream"
                id="cameraStream"
                alt="실시간 카메라 화면"
              >

              <div class="camera-overlay">
                <div class="overlay-group">

                  <div class="overlay-chip">
                    <svg
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                    >
                      <circle cx="12" cy="12" r="3"></circle>
                      <path d="M12 2v3"></path>
                      <path d="M12 19v3"></path>
                      <path d="M2 12h3"></path>
                      <path d="M19 12h3"></path>
                    </svg>

                    <span class="overlay-muted">현재 방향</span>

                    <span
                      class="overlay-value"
                      id="currentDirection"
                    >
                      FRONT
                    </span>
                  </div>

                  <div class="overlay-chip">
                    <svg
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                    >
                      <path d="M5 12.55a11 11 0 0 1 14.08 0"></path>
                      <path d="M1.42 9a16 16 0 0 1 21.16 0"></path>
                      <path d="M8.53 16.11a6 6 0 0 1 6.95 0"></path>
                      <circle cx="12" cy="20" r="1"></circle>
                    </svg>

                    <span class="overlay-muted">연결 상태</span>

                    <span class="overlay-normal">정상</span>
                  </div>
                </div>

                <div class="overlay-chip">
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                  >
                    <circle cx="12" cy="12" r="9"></circle>
                    <path d="M12 7v5l3 2"></path>
                  </svg>

                  <span
                    class="overlay-value"
                    id="currentTime"
                  >
                    --:--:--
                  </span>
                </div>
              </div>

              <span class="camera-corner corner-tl"></span>
              <span class="camera-corner corner-tr"></span>
              <span class="camera-corner corner-bl"></span>
              <span class="camera-corner corner-br"></span>
            </div>
          </div>
        </section>

        <section class="map-column">
          <div class="section-title">
            <span class="section-icon">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path d="M9 20l-5.447-2.724A1 1 0 0 1 3 16.382V5.618a1 1 0 0 1 1.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0 0 21 18.382V7.618a1 1 0 0 0-.553-.894L15 4m0 13V4m0 0L9 7"></path>
              </svg>
            </span>

            <span>위험구간 지도</span>
          </div>

          <div class="map-card">
            <div class="map-frame">
              <div id="map"></div>

              <div class="map-info">
                <span class="map-info-chip" id="mapInfoChip">위치 확인 중...</span>
              </div>
            </div>
          </div>
        </section>

      </div>

      <div class="distance-section">
        <div class="section-title">
          <span class="section-icon">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path d="M8.5 16.5a6 6 0 0 1 0-9"></path>
              <path d="M5.5 19.5a10 10 0 0 1 0-15"></path>
              <path d="M15.5 7.5a6 6 0 0 1 0 9"></path>
              <path d="M18.5 4.5a10 10 0 0 1 0 15"></path>
              <circle cx="12" cy="12" r="1.5"></circle>
            </svg>
          </span>

          <span>ToF 거리 정보 (cm)</span>
        </div>

        <div class="distance-grid">

          <article
            class="distance-card"
            id="card-left"
          >
            <div class="direction-icon">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2.4"
              >
                <path d="m11 18-6-6 6-6"></path>
                <path d="M5 12h14"></path>
              </svg>
            </div>

            <div>
              <div class="distance-label">왼쪽 거리</div>

              <div class="distance-value-row">
                <span
                  class="distance-value"
                  id="leftValue"
                >
                  --
                </span>

                <span
                  class="distance-unit"
                  id="leftUnit"
                >
                  cm
                </span>
              </div>

              <div class="distance-progress">
                <div
                  class="distance-progress-fill"
                  id="leftProgress"
                ></div>
              </div>

              <div class="distance-scale">
                <span>0</span>
                <span>60</span>
                <span>150</span>
                <span>200+</span>
              </div>

              <div class="card-warning" id="leftWarning">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"></path>
                  <path d="M13.7 21a2 2 0 0 1-3.4 0"></path>
                </svg>
                <span id="leftWarningText"></span>
              </div>
            </div>
          </article>

          <article
            class="distance-card"
            id="card-front"
          >
            <div class="direction-icon">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2.4"
                style="transform: rotate(90deg);"
              >
                <path d="m11 18-6-6 6-6"></path>
                <path d="M5 12h14"></path>
              </svg>
            </div>

            <div>
              <div class="distance-label">정면 거리</div>

              <div class="distance-value-row">
                <span
                  class="distance-value"
                  id="frontValue"
                >
                  --
                </span>

                <span
                  class="distance-unit"
                  id="frontUnit"
                >
                  cm
                </span>
              </div>

              <div class="distance-progress">
                <div
                  class="distance-progress-fill"
                  id="frontProgress"
                ></div>
              </div>

              <div class="distance-scale">
                <span>0</span>
                <span>60</span>
                <span>150</span>
                <span>200+</span>
              </div>

              <div class="card-warning" id="frontWarning">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"></path>
                  <path d="M13.7 21a2 2 0 0 1-3.4 0"></path>
                </svg>
                <span id="frontWarningText"></span>
              </div>
            </div>
          </article>

          <article
            class="distance-card"
            id="card-right"
          >
            <div class="direction-icon">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2.4"
                style="transform: rotate(180deg);"
              >
                <path d="m11 18-6-6 6-6"></path>
                <path d="M5 12h14"></path>
              </svg>
            </div>

            <div>
              <div class="distance-label">오른쪽 거리</div>

              <div class="distance-value-row">
                <span
                  class="distance-value"
                  id="rightValue"
                >
                  --
                </span>

                <span
                  class="distance-unit"
                  id="rightUnit"
                >
                  cm
                </span>
              </div>

              <div class="distance-progress">
                <div
                  class="distance-progress-fill"
                  id="rightProgress"
                ></div>
              </div>

              <div class="distance-scale">
                <span>0</span>
                <span>60</span>
                <span>150</span>
                <span>200+</span>
              </div>

              <div class="card-warning" id="rightWarning">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"></path>
                  <path d="M13.7 21a2 2 0 0 1-3.4 0"></path>
                </svg>
                <span id="rightWarningText"></span>
              </div>
            </div>
          </article>

        </div>
      </div>

      <footer class="status-panel">

        <div class="status-item">
          <div class="status-icon">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path d="M5 12.55a11 11 0 0 1 14.08 0"></path>
              <path d="M1.42 9a16 16 0 0 1 21.16 0"></path>
              <path d="M8.53 16.11a6 6 0 0 1 6.95 0"></path>
              <circle cx="12" cy="20" r="1"></circle>
            </svg>
          </div>

          <div>
            <div class="status-title">ToF 센서 상태</div>

            <div class="status-value">
              <span
                class="status-dot"
                id="tofDot"
              ></span>

              <span id="tofStatus">연결 확인 중</span>
            </div>
          </div>
        </div>

        <div class="status-item">
          <div class="status-icon">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <rect x="3" y="6" width="14" height="12" rx="2"></rect>
              <path d="m17 10 4-2v8l-4-2"></path>
              <circle cx="10" cy="12" r="2.5"></circle>
            </svg>
          </div>

          <div>
            <div class="status-title">카메라 상태</div>

            <div class="status-value">
              <span class="status-dot"></span>
              <span>정상 연결</span>
            </div>
          </div>
        </div>

        <div class="status-item">
          <div class="status-icon">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <circle cx="12" cy="12" r="9"></circle>
              <path d="M12 7v5l3 2"></path>
            </svg>
          </div>

          <div>
            <div class="status-title">마지막 데이터 갱신</div>

            <div
              class="status-value"
              id="lastUpdate"
            >
              아직 수신된 데이터가 없습니다
            </div>
          </div>
        </div>

      </footer>
    </section>
  </main>

  <div class="summary-overlay" id="summaryOverlay">
    <div class="summary-modal">
      <div class="summary-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="9"></circle>
          <path d="M9 12l2 2 4-4"></path>
        </svg>
      </div>
      <h2>보행 리포트</h2>
      <p id="summaryText"></p>
      <button id="summaryCloseBtn">확인</button>
    </div>
  </div>

  <script>
    const THRESHOLD_CM = 100;
    const MAX_DISTANCE_CM = 200;
    const REFRESH_INTERVAL_MS = 1000;
    const HAZARD_REFRESH_MS = 5000;
    const SUMMARY_REFRESH_MS = 3000;

    function normalizeNumber(value) {
      const number = Number(value);

      if (!Number.isFinite(number)) {
        return null;
      }

      return number;
    }

    function normalizeDirection(value) {
      const direction = String(value || "")
        .trim()
        .toUpperCase();

      if (direction === "LEFT" || direction === "L") {
        return "LEFT";
      }

      if (
        direction === "FRONT" ||
        direction === "CENTER" ||
        direction === "MID" ||
        direction === "M"
      ) {
        return "FRONT";
      }

      if (direction === "RIGHT" || direction === "R") {
        return "RIGHT";
      }

      return null;
    }

    function getDirectionFromData(data, entries) {
      const directDirection = normalizeDirection(
        data.camera_direction ||
        data.direction ||
        data.current_direction
      );

      if (directDirection) {
        return directDirection;
      }

      const validEntries = entries.filter(function (entry) {
        return entry.value !== null && entry.value > 0;
      });

      if (!validEntries.length) {
        return "FRONT";
      }

      return validEntries.reduce(function (a, b) {
        return a.value <= b.value ? a : b;
      }).direction;
    }

    function updateDistance(
      key,
      rawValue
    ) {
      const valueElement =
        document.getElementById(key + "Value");

      const unitElement =
        document.getElementById(key + "Unit");

      const progressElement =
        document.getElementById(key + "Progress");

      const value = normalizeNumber(rawValue);

      if (
        value === null ||
        value <= 0
      ) {
        valueElement.textContent = "측정 불가";
        valueElement.classList.add("unavailable");

        unitElement.style.display = "none";
        progressElement.style.width = "0%";

        return;
      }

      valueElement.textContent =
        Number.isInteger(value)
          ? value
          : value.toFixed(1);

      valueElement.classList.remove("unavailable");

      unitElement.style.display = "";
      unitElement.textContent = "cm";

      const percent = Math.min(
        Math.max(
          (value / MAX_DISTANCE_CM) * 100,
          2
        ),
        100
      );

      progressElement.style.width =
        percent + "%";
    }

    function updateActiveDirection(direction, entries) {
      const normalized =
        normalizeDirection(direction) || "FRONT";

      const cards = {
        LEFT: document.getElementById("card-left"),
        FRONT: document.getElementById("card-front"),
        RIGHT: document.getElementById("card-right")
      };

      Object.values(cards).forEach(function (card) {
        card.classList.remove("active");
      });

      const matchedEntry = entries.find(function (entry) {
        return entry.direction === normalized;
      });

      const isWithinThreshold =
        matchedEntry &&
        matchedEntry.value !== null &&
        matchedEntry.value <= THRESHOLD_CM;

      if (isWithinThreshold) {
        cards[normalized].classList.add("active");
      }

      document.getElementById(
        "currentDirection"
      ).textContent = normalized;
    }

    function updateClock() {
      const now = new Date();

      document.getElementById(
        "currentTime"
      ).textContent =
        now.toLocaleTimeString(
          "ko-KR",
          {
            hour12: false,
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit"
          }
        );
    }

    function formatDateTime(date) {
      const year = date.getFullYear();
      const month = String(
        date.getMonth() + 1
      ).padStart(2, "0");
      const day = String(
        date.getDate()
      ).padStart(2, "0");
      const hour = String(
        date.getHours()
      ).padStart(2, "0");
      const minute = String(
        date.getMinutes()
      ).padStart(2, "0");
      const second = String(
        date.getSeconds()
      ).padStart(2, "0");

      return (
        year + "-" +
        month + "-" +
        day + " " +
        hour + ":" +
        minute + ":" +
        second
      );
    }

    const map = L.map('map').setView([37.5665, 126.9780], 17);

    setTimeout(function () {
      map.invalidateSize();
    }, 300);

    window.addEventListener('resize', function () {
      map.invalidateSize();
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap'
    }).addTo(map);

    let userMarker = null;
    let hazardMarkers = [];
    let mapCentered = false;

    const hazardIcon = L.divIcon({
      className: '',
      html: '<div style="background:#dc2626;color:white;border-radius:50%;width:24px;height:24px;display:flex;align-items:center;justify-content:center;font-weight:900;border:2px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.3);font-size:14px;">!</div>',
      iconSize: [24, 24],
      iconAnchor: [12, 12]
    });

    const userIcon = L.divIcon({
      className: '',
      html: '<div style="background:#245bbd;border-radius:50%;width:16px;height:16px;border:3px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.3);"></div>',
      iconSize: [28, 28],
      iconAnchor: [14, 14]
    });

    async function refreshHazards() {
      try {
        const res = await fetch('/hazards', { cache: 'no-store' });
        const zones = await res.json();

        hazardMarkers.forEach(function (marker) {
          map.removeLayer(marker);
        });
        hazardMarkers = [];

        zones.forEach(function (zone) {
          const marker = L.marker([zone.lat, zone.lon], { icon: hazardIcon })
            .addTo(map)
            .bindPopup('감지 횟수: ' + zone.count + '회');

          hazardMarkers.push(marker);
        });
      } catch (error) {
        console.error('위험구간 로딩 실패:', error);
      }
    }

    function updateMapLocation(lat, lon) {
      if (lat === null || lon === null || lat === undefined || lon === undefined) {
        document.getElementById('mapInfoChip').textContent = 'GPS 신호 대기 중...';
        return;
      }

      const latlng = [lat, lon];

      if (userMarker) {
        userMarker.setLatLng(latlng);
      } else {
        userMarker = L.marker(latlng, { icon: userIcon }).addTo(map);
      }

      if (!mapCentered) {
        map.setView(latlng, 18);
        mapCentered = true;
      }

      document.getElementById('mapInfoChip').textContent =
        '현재 위치: ' + lat.toFixed(5) + ', ' + lon.toFixed(5);
    }

    async function refreshStatus() {
      try {
        const response = await fetch(
          "/status",
          {
            cache: "no-store"
          }
        );

        if (!response.ok) {
          throw new Error(
            "HTTP " + response.status
          );
        }

        const data = await response.json();

        const entries = [
          {
            key: "left",
            direction: "LEFT",
            value: normalizeNumber(data.left)
          },
          {
            key: "front",
            direction: "FRONT",
            value: normalizeNumber(
              data.front !== undefined
                ? data.front
                : data.center
            )
          },
          {
            key: "right",
            direction: "RIGHT",
            value: normalizeNumber(data.right)
          }
        ];

        entries.forEach(function (entry) {
          updateDistance(
            entry.key,
            entry.value
          );
        });

        const cameraDirection =
          getDirectionFromData(
            data,
            entries
          );

        updateActiveDirection(
          cameraDirection,
          entries
        );

        const warning =
          data.warning &&
          data.warning !== "-"
            ? String(data.warning)
            : null;

        ["left", "front", "right"].forEach(function (key) {
          const box = document.getElementById(key + "Warning");
          const text = document.getElementById(key + "WarningText");
          const isTarget = warning && key === cameraDirection.toLowerCase();

          if (isTarget) {
            text.textContent = warning;
            box.classList.add("show");
          } else {
            box.classList.remove("show");
          }
        });

        document.getElementById(
          "tofDot"
        ).classList.remove("off");

        document.getElementById(
          "tofStatus"
        ).textContent = "정상 연결";

	const liveDot = document.querySelector(".live-dot");
	const isWalking = data.walk_active === true;

	if (isWalking) {
  	  liveDot.style.background = "#16a36c";  // 초록색: 보행 중
  	  document.getElementById("systemStatus").textContent = "보행 중";
	} else {
  	  liveDot.style.background = "#9aa8b8";  // 회색: 대기 중
  	  document.getElementById("systemStatus").textContent = "대기 중";
	}

        document.getElementById(
          "lastUpdate"
        ).textContent =
          formatDateTime(new Date());

        updateMapLocation(
          normalizeNumber(data.lat),
          normalizeNumber(data.lon)
        );
      } catch (error) {
        console.error(
          "상태 데이터 수신 실패:",
          error
        );

        document.getElementById(
          "tofDot"
        ).classList.add("off");

        document.getElementById(
          "tofStatus"
        ).textContent = "연결 끊김";

        document.getElementById(
          "systemStatus"
        ).textContent =
          "데이터 연결 확인 필요";
      }
    }

    async function checkWalkSummary() {
      try {
        const res = await fetch('/walk_summary', { cache: 'no-store' });
        const summary = await res.json();

        if (summary && summary.text) {
          document.getElementById('summaryText').textContent = summary.text;
          document.getElementById('summaryOverlay').classList.add('show');
        }
      } catch (error) {
        console.error('보행 요약 로딩 실패:', error);
      }
    }

    document.getElementById('summaryCloseBtn').addEventListener('click', async function () {
      document.getElementById('summaryOverlay').classList.remove('show');

      try {
        await fetch('/walk_summary/dismiss', { method: 'POST' });
      } catch (error) {
        console.error('요약 닫기 실패:', error);
      }
    });

    updateClock();
    refreshStatus();
    refreshHazards();
    checkWalkSummary();

    setInterval(
      updateClock,
      1000
    );

    setInterval(
      refreshStatus,
      REFRESH_INTERVAL_MS
    );

    setInterval(
      refreshHazards,
      HAZARD_REFRESH_MS
    );

    setInterval(
      checkWalkSummary,
      SUMMARY_REFRESH_MS
    );
  </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(PAGE)


@app.route("/stream")
def stream():
    def generate():
        while True:
            frame = state.get_frame()

            if frame is not None:
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n"
                    + frame
                    + b"\r\n"
                )

            time.sleep(0.1)

    return Response(
        generate(),
        mimetype=(
            "multipart/x-mixed-replace; "
            "boundary=frame"
        )
    )


@app.route("/status")
def status():
    data = state.get_distances()

    if not isinstance(data, dict):
        data = {}

    loc = state.get_location()

    result = {
        "left": data.get("left"),
        "front": data.get(
            "front",
            data.get("center")
        ),
        "right": data.get("right"),
        "warning": state.get_warning(),
        "lat": loc.get("lat"),
        "lon": loc.get("lon"),
        "walk_active": state.get_walk_active()
    }

    get_direction = getattr(
        state,
        "get_camera_direction",
        None
    )

    if callable(get_direction):
        try:
            result["camera_direction"] = (
                get_direction()
            )
        except Exception:
            pass

    return jsonify(result)


@app.route("/gps", methods=["POST"])
def receive_gps():
    data = request.get_json(force=True)
    loc_str = data["loc"]
    lat_str, lon_str = loc_str.split(",")
    lat = float(lat_str)
    lon = float(lon_str)

    gps_data = {
        "lat": lat,
        "lon": lon,
        "measured_at": time.time()
    }

    upload_data(GPS_CNT, gps_data)

    print(f"GPS 수신: {lat}, {lon}")
    return jsonify({"status": "ok"})


@app.route("/hazards")
def hazards():
    return jsonify(get_confirmed_zones())


@app.route("/walk_summary")
def walk_summary():
    summary = state.get_walk_summary()
    return jsonify(summary)


@app.route("/walk_summary/dismiss", methods=["POST"])
def dismiss_walk_summary():
    state.clear_walk_summary()
    return jsonify({"status": "ok"})


def run_dashboard():
    app.run(
        host="0.0.0.0",
        port=5000,
        threaded=True
    )
