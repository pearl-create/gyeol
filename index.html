<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>실시간 비속어 감지 미니 데모</title>

  <!-- p5.js & ml5.js -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.4.0/p5.min.js"></script>
  <script src="https://unpkg.com/ml5@latest/dist/ml5.min.js"></script>

  <style>
    :root { --card-w: 380px; }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      height: 100svh;
      display: grid;
      place-items: center;
      font-family: system-ui, -apple-system, "Pretendard", "Noto Sans KR", sans-serif;
      color: #fff;
      background: url('https://ssl.gstatic.com/meet/backgrounds/hills.jpg') center/cover no-repeat fixed;
      backdrop-filter: blur(14px);
    }
    .glass {
      width: min(92vw, var(--card-w));
      padding: 24px 28px;
      border-radius: 20px;
      background: rgba(0,0,0,.45);
      box-shadow: 0 10px 30px rgba(0,0,0,.35);
    }
    h2 { margin: 0 0 6px; font-weight: 700; font-size: 22px; }
    .hint { opacity: .9; margin: 0 0 16px; font-size: 14px; }
    .meter { background: rgba(255,255,255,.15); border-radius: 10px; overflow: hidden; height: 22px; margin: 8px 0; }
    .bar   { height: 100%; width: 0%; background: linear-gradient(90deg,#66d,#aaf); color: #000; font-weight: 700;
             font-size: 13px; padding-left: 8px; line-height: 22px; white-space: nowrap; }
    .row { display: grid; grid-template-columns: 1fr; gap: 4px; }
    .footer { margin-top: 12px; font-size: 12px; opacity: .8; }
    button {
      margin-top: 10px; width: 100%; height: 40px; border-radius: 10px; border: none; cursor: pointer;
      font-weight: 700;
    }
  </style>
</head>
<body>
  <main class="glass">
    <h2>🎙️ 실시간 감지 데모</h2>
    <p class="hint">마이크 사용을 허용해주세요.</p>

    <div id="output" class="row"></div>
    <button id="reinit">🔄 마이크 다시 연결</button>

    <p class="footer">Model: <code>gSHOySjax</code> (Teachable Machine · ml5.js)</p>
  </main>

  <script>
    // ====== 설정 ======
    const MODEL_URL = "https://teachablemachine.withgoogle.com/models/gSHOySjax/model.json";
    const LABELS = ["깔라만씨","배경 소음","수박씨","아이씨"];  // 모델의 클래스명에 맞게
    let classifier, mic;
    const bars = {};

    // UI 구성
    const output = document.getElementById("output");
    function buildUI() {
      output.innerHTML = "";
      LABELS.forEach(label => {
        const meter = document.createElement("div");
        meter.className = "meter";
        const bar = document.createElement("div");
        bar.className = "bar";
        bar.textContent = `${label}: 0%`;
        meter.appendChild(bar);
        output.appendChild(meter);
        bars[label] = bar;
      });
    }

    // 모델/마이크 초기화
    async function init() {
      buildUI();
      try {
        // p5 마이크 준비(권한 트리거)
        mic = new p5.AudioIn();
        await new Promise(res => mic.start(res));

        // 모델 로드
        classifier = await ml5.soundClassifier(MODEL_URL, { probabilityThreshold: 0 }, () => {
          console.log("✅ model ready");
          classifier.classify(gotResult);
        });
      } catch (e) {
        console.error(e);
        alert("마이크 권한 또는 모델 로드에 문제가 있어요. 브라우저 주소창의 권한 설정을 확인해주세요.");
      }
    }

    function gotResult(err, results) {
      if (err || !results) return;
      results.forEach(r => {
        const label = r.label;
        const conf = Math.min(100, Math.max(0, r.confidence * 100));
        if (bars[label]) {
          bars[label].style.width = conf.toFixed(1) + "%";
          bars[label].textContent = `${label}: ${conf.toFixed(1)}%`;
        }
      });
    }

    document.getElementById("reinit").addEventListener("click", init);
    init();
  </script>
</body>
</html>
