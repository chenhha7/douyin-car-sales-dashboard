(() => {
  const $ = (id) => document.getElementById(id);
  const number = new Intl.NumberFormat("zh-CN");
  const escapeHtml = (value) => String(value ?? "—").replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", "\"": "&quot;",
  }[character]));
  const count = (value) => value == null ? "—" : number.format(value);
  const percent = (value) => value == null ? "—" : `${(value * 100).toFixed(1)}%`;
  const signedCount = (value) => value == null ? "—" : `${value >= 0 ? "+" : ""}${number.format(value)}`;
  const formatValue = (value, type) => type === "rate" ? percent(value) : count(value);
  const dateRange = ({ start, end }) => `${start} 至 ${end}`;

  function renderTree(rows) {
    $("weeklyTreeRows").innerHTML = rows.map((row) => `
      <tr>
        <td>${escapeHtml(row.label)}</td>
        <td class="num">${formatValue(row.previous, row.type)}</td>
        <td class="num">${formatValue(row.current, row.type)}</td>
        <td class="num ${row.contribution < 0 ? "danger" : row.contribution > 0 ? "good" : "muted"}">${signedCount(row.contribution)} 条</td>
      </tr>`).join("") || '<tr><td colspan="4" class="empty">暂无拆解结果</td></tr>';
  }

  function renderDimension(analysis) {
    const rows = analysis.rows || [];
    $("weeklyDimensionLabel").textContent = analysis.dimension_label || "维度";
    $("weeklyDimensionDescription").textContent = `按${analysis.dimension_label || "维度"}比较${analysis.primary_factor === "open_rate" ? "创开率" : "核心因子"}，按估算影响排序`;
    $("weeklyDimensionRows").innerHTML = rows.slice(0, 8).map((row) => `
      <tr>
        <td>${escapeHtml(row.value)}</td>
        <td class="num">${percent(row.primary_factor_previous)}</td>
        <td class="num">${percent(row.primary_factor_current)}</td>
        <td class="num ${(row.estimated_factor_impact || 0) < 0 ? "danger" : (row.estimated_factor_impact || 0) > 0 ? "good" : "muted"}">${signedCount(row.estimated_factor_impact)} 条</td>
        <td class="num ${(row.target_delta || 0) < 0 ? "danger" : (row.target_delta || 0) > 0 ? "good" : "muted"}">${signedCount(row.target_delta)} 条</td>
      </tr>`).join("") || '<tr><td colspan="5" class="empty">暂无多维定位结果</td></tr>';
  }

  function renderDrilldown(drilldown) {
    const records = drilldown.records || [];
    $("weeklyDrillTitle").textContent = drilldown.label || "明细下钻";
    $("weeklyDrillNote").textContent = `展示 ${records.length} 条满足规则的合成记录，供业务复核，不自动生成任务。`;
    $("weeklyDrillRows").innerHTML = records.map((record) => `
      <tr>
        <td>${escapeHtml(record.user_id)}</td>
        <td>${escapeHtml(record.opportunity_id)}</td>
        <td>${escapeHtml(record.service_provider)}</td>
        <td>${escapeHtml(record.source_label)}${record.live_room ? `<br><span class="muted">${escapeHtml(record.live_room)}</span>` : ""}</td>
        <td>${escapeHtml(record.region)}<br><span class="muted">${escapeHtml(record.store)}</span></td>
        <td>${escapeHtml(record.cohort_date)}</td>
        <td>${escapeHtml(record.current_stage)}</td>
        <td class="num">${record.create_to_open_hours == null ? "未开启" : `${Number(record.create_to_open_hours).toFixed(1)} 小时`}</td>
        <td>${escapeHtml(record.reason)}</td>
      </tr>`).join("") || '<tr><td colspan="9" class="empty">当前周没有满足下钻规则的记录</td></tr>';
  }

  function render(payload) {
    const { metadata, week_comparison: weeks, anomaly, tree, dimension_analysis: dimension, drilldown, verification } = payload;
    const driver = anomaly.primary_driver || {};
    const topDimension = (dimension.rows || [])[0] || {};
    const records = drilldown.records || [];
    const movement = `${anomaly.label} ${count(anomaly.previous_value)} → ${count(anomaly.current_value)} 条（${signedCount(anomaly.delta)} 条）`;
    const driverText = `${driver.label || "核心因子"} ${formatValue(driver.previous, driver.type)} → ${formatValue(driver.current, driver.type)}，估算影响 ${signedCount(driver.contribution)} 条`;
    const dimensionText = `${dimension.dimension_label || "维度"}：${topDimension.value || "—"}`;

    $("weeklyDataNote").textContent = `比较口径：本周 ${dateRange(weeks.current)}，前一完整周 ${dateRange(weeks.previous)}。${metadata.note || ""}`;
    $("weeklyDiscover").textContent = `${movement}，作为本周优先诊断对象。`;
    $("weeklyDecompose").textContent = `按“${tree.formula || "—"}”拆解，${driver.label || "核心因子"}贡献最大。`;
    $("weeklyLocate").textContent = `${dimensionText}的估算影响最大，优先复核其分母和环节时效。`;
    $("weeklyDrill").textContent = `${records.length} 条记录满足下钻规则，可回看具体状态与创建→开启时长。`;
    $("weeklyConfirm").textContent = "当前结果是待验证假设；需结合业务记录确认后，才讨论责任归属或策略。";

    $("weeklyMetric").textContent = `${count(anomaly.current_value)} 条`;
    $("weeklyMetricNote").textContent = `${anomaly.label}：前一周 ${count(anomaly.previous_value)} 条，变化 ${signedCount(anomaly.delta)} 条。`;
    $("weeklyDriver").textContent = driver.label || "—";
    $("weeklyDriverNote").textContent = driverText;
    $("weeklyDimension").textContent = topDimension.value || "—";
    $("weeklyDimensionNote").textContent = `${dimension.dimension_label || "维度"}层级的最大估算影响：${signedCount(topDimension.estimated_factor_impact)} 条。`;
    $("weeklyAffected").textContent = `${records.length} 条`;
    $("weeklyAffectedNote").textContent = `满足“${drilldown.label || "明细下钻"}”规则的待核验合成记录。`;
    $("weeklyFormula").textContent = tree.formula || "—";

    $("weeklyVerificationTitle").textContent = verification.title || "待业务确认";
    $("weeklyVerificationFocus").textContent = `${verification.focus_dimension?.type || "—"}：${verification.focus_dimension?.value || "—"}`;
    $("weeklyVerificationQuestion").textContent = verification.question || "—";
    $("weeklyVerificationEvidence").textContent = verification.evidence || "—";
    $("weeklyVerificationNote").textContent = verification.note || "—";

    renderTree(tree.rows || []);
    renderDimension(dimension);
    renderDrilldown(drilldown);
  }

  fetch("./data/demo/weekly_attribution_result.json")
    .then((response) => {
      if (!response.ok) throw new Error("无法加载周度归因结果");
      return response.json();
    })
    .then((payload) => {
      if (!payload.metadata?.is_synthetic) throw new Error("公开页面只允许加载合成归因数据");
      render(payload);
    })
    .catch((error) => {
      $("weeklyDataNote").textContent = `周度归因结果加载失败：${error.message}。请通过 GitHub Pages 或本地 HTTP 服务打开页面。`;
    });
})();
