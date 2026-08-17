<!DOCTYPE html>
<html lang="bg">
<head>
<meta charset="UTF-8">
<style>
  body {
    background-color: #121212;
    color: #fff;
    font-family: Arial, sans-serif;
    padding: 20px;
    max-width: 400px;
    margin: 0 auto;
  }

  .km-display-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    text-align: center;
    margin-bottom: 15px;
  }

  .km-box-lbl {
    font-size: 10px;
    color: #aaa;
    margin-bottom: 4px;
  }

  .km-box-val {
    font-size: 16px;
    font-weight: bold;
  }

  .km-box-val span {
    font-size: 10px;
  }

  .progress-bar-bg {
    background-color: #333;
    height: 8px;
    border-radius: 4px;
    overflow: hidden;
    margin-bottom: 20px;
  }

  .progress-bar-fill {
    height: 100%;
    background: linear-gradient(90deg, #00f2fe, #4facfe);
    width: 0%;
    transition: width 0.3s ease;
  }

  .gauge-card {
    background-color: #1e1e1e;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    margin-bottom: 20px;
    box-shadow: 0 0 20px #ff4b4b22, inset 0 0 15px rgba(0,0,0,0.8);
  }

  .gauge-value {
    font-size: 36px;
    font-weight: bold;
    color: #ff4b4b;
    text-shadow: 0 0 10px #ff4b4b;
  }

  .gauge-unit {
    font-size: 12px;
    color: #aaa;
  }

  .dashboard-footer-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
  }

  .dash-subcard {
    background-color: #1e1e1e;
    padding: 12px;
    border-radius: 8px;
  }

  /* Форма за въвеждане на данни */
  .inputs-card {
    background-color: #1e1e1e;
    padding: 15px;
    border-radius: 8px;
    margin-top: 20px;
  }

  .input-group {
    margin-bottom: 10px;
  }

  .input-group label {
    display: block;
    font-size: 12px;
    color: #aaa;
    margin-bottom: 4px;
  }

  .input-group input {
    width: 100%;
    padding: 8px;
    border-radius: 4px;
    border: 1px solid #444;
    background-color: #2a2a2a;
    color: #fff;
    box-sizing: border-box;
  }
</style>
</head>
<body>

<div class="km-display-grid">
    <div>
        <div class="km-box-lbl">СТАРТ</div>
        <div class="km-box-val"><span id="display-start">130749</span> <span style="font-size:10px;">км</span></div>
    </div>
    <div>
        <div class="km-box-lbl">ИЗМИНАТИ</div>
        <div class="km-box-val" style="color:#00f2fe;"><span id="display-distance">200</span> <span style="font-size:10px;">км</span></div>
    </div>
    <div>
        <div class="km-box-lbl">КРАЙНИ</div>
        <div class="km-box-val"><span id="display-end">130949</span> <span style="font-size:10px;">км</span></div>
    </div>
</div>

<div class="progress-bar-bg">
    <div id="progress-fill" class="progress-bar-fill" style="width: 100%;"></div>
</div>

<div class="gauge-card">
    <div id="display-consumption" class="gauge-value">16.0</div>
    <div class="gauge-unit">л / 100 км</div>
    <div style="font-size: 8px; color: #666; margin-top: 4px; text-transform:uppercase;">Финал</div>
</div>

<div class="dashboard-footer-grid">
    <div class="dash-subcard">
        <div style="font-size:10px; color:#aaa;">💧 ЗАРЕДЕНО ГОРИВО</div>
        <div style="font-size:14px; font-weight:bold; color:#fff;"><span id="display-fuel">32.0</span> л</div>
    </div>
    <div class="dash-subcard">
        <div style="font-size:10px; color:#aaa;">💰 ОБЩО ТРАНСПОРТ</div>
        <div style="font-size:14px; font-weight:bold; color:#00ffcc;"><span id="display-cost">50.00</span> EUR</div>
    </div>
</div>

<!-- Полета за калкулация -->
<div class="inputs-card">
    <div class="input-group">
        <label>Начален километраж (км):</label>
        <input type="number" id="input-start" value="130749" oninput="calculate()">
    </div>
    <div class="input-group">
        <label>Изминати километри (км):</label>
        <input type="number" id="input-distance" value="200" oninput="calculate()">
    </div>
    <div class="input-group">
        <label>Заредено гориво (литри):</label>
        <input type="number" step="0.1" id="input-fuel" value="32" oninput="calculate()">
    </div>
    <div class="input-group">
        <label>Общо цена (EUR):</label>
        <input type="number" step="0.01" id="input-cost" value="50" oninput="calculate()">
    </div>
</div>

<script>
function calculate() {
    const startKm = parseFloat(document.getElementById('input-start').value) || 0;
    const distance = parseFloat(document.getElementById('input-distance').value) || 0;
    const fuel = parseFloat(document.getElementById('input-fuel').value) || 0;
    const cost = parseFloat(document.getElementById('input-cost').value) || 0;

    const endKm = startKm + distance;
    const consumption = distance > 0 ? ((fuel / distance) * 100) : 0;

    document.getElementById('display-start').innerText = startKm;
    document.getElementById('display-distance').innerText = distance;
    document.getElementById('display-end').innerText = endKm;
    document.getElementById('display-fuel').innerText = fuel.toFixed(1);
    document.getElementById('display-cost').innerText = cost.toFixed(2);
    document.getElementById('display-consumption').innerText = consumption.toFixed(1);
    
    // Актуализиране на прогреса (примерно до 1000 км за пълен бак/пробег)
    const progress = Math.min((distance / 1000) * 100, 100);
    document.getElementById('progress-fill').style.width = progress + '%';
}
</script>

</body>
</html>
