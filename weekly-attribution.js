(() => {
  const $ = (id) => document.getElementById(id);
  const number = new Intl.NumberFormat("zh-CN");
  const escapeHtml = (value) => String(value ?? "—").replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", "\"": "&quot;",
  }[character]));
  const count = (value) => value == null ? "—" : number.format(value);
  const percent = (value) => value == null ? "—" : `${(value * 100).toFixed(1)}%`;
  const signedCount = (value) => value == null ? "—" : `${value >= 0 ? "+" : ""}${number.format(value)}`;
  const signedPp = (value) => value == null ? "—" : `${value >= 0 ? "+" : ""}${(value * 100).toFixed(1)} pp`;
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
    $("weeklyDrillNote").textContent = `展示 ${records.length} 条满足规则的合成记录，可直接作为跟进清单。`;
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

  function renderStrategy(effect) {
    const before = effect.before || {};
    const after = effect.after || {};
    $("weeklyStrategyPeriod").textContent = `前组 ${effect.pre_period?.join(" 至 ") || "—"}；后组 ${effect.post_period?.join(" 至 ") || "—"}。`;
    $("weeklyStrategyOpen").textContent = `${percent(before.d3_open_rate)} → ${percent(after.d3_open_rate)}（${signedPp(effect.d3_open_rate_delta)}）`;
    $("weeklyStrategyDeal").textContent = `${percent(before.mature_deal_rate)} → ${percent(after.mature_deal_rate)}（${signedPp(effect.mature_deal_rate_delta)}）`;
    $("weeklyStrategyNote").textContent = `${effect.note || ""} 前后创建销售机会分别为 ${count(before.created)} 和 ${count(after.created)} 条。`;
  }

  function render(payload) {
    const { metadata, week_comparison: weeks, anomaly, tree, dimension_analysis: dimension, drilldown, task, strategy_effect: effect } = payload;
    const driver = anomaly.primary_driver || {};
    const topDimension = (dimension.rows || [])[0] || {};
    const currentWeek = weeks.current;
    const previousWeek = weeks.previous;
    const movement = `${anomaly.label} ${count(anomaly.previous_value)} → ${count(anomaly.current_value)} 条（${signedCount(anomaly.delta)} 条）`;
    const driverText = `${driver.label || "核心因子"} ${formatValue(driver.previous, driver.type)} → ${formatValue(driver.current, driver.type)}，估算影响 ${signedCount(driver.contribution)} 条`;
    const dimensionText = `${dimension.dimension_label || "维度"}：${topDimension.value || "—"}`;

    $("weeklyDataNote").textContent = `比较口径：本周 ${dateRange(currentWeek)}，前一完整周 ${dateRange(previousWeek)}。${metadata.note || ""}`;
    $("weeklyDiscover").textContent = `${movement}，作为本周优先诊断对象。`;
    $("weeklyLocate").textContent = `${driver.label || "核心因子"}是最大驱动；优先落到${dimensionText}。`;
    $("weeklyAssign").textContent = `${task.owner_role || "—"}在 ${task.deadline || "—"} 前处理 ${task.affected_records ?? 0} 条待跟进记录。`;
    $("weeklyPlan").textContent = `围绕“${task.issue || "—"}”制定门店承接与分单时效优化动作。`;
    $("weeklyExecute").textContent = `按任务清单追踪处理进度，并持续监控创开率及创建→开启时长。`;
    $("weeklyEvaluate").textContent = `使用前后同期用户组回看 3 日创开率和 30 日内锁单率。`;

    $("weeklyMetric").textContent = `${count(anomaly.current_value)} 条`;
    $("weeklyMetricNote").textContent = `${anomaly.label}：前一周 ${count(anomaly.previous_value)} 条，变化 ${signedCount(anomaly.delta)} 条。`;
    $("weeklyDriver").textContent = driver.label || "—";
    $("weeklyDriverNote").textContent = driverText;
    $("weeklyDimension").textContent = topDimension.value || "—";
    $("weeklyDimensionNote").textContent = `${dimension.dimension_label || "维度"}层级的最大估算影响：${signedCount(topDimension.estimated_factor_impact)} 条。`;
    $("weeklyAffected").textContent = `${task.affected_records ?? 0} 条`;
    $("weeklyAffectedNote").textContent = `符合“${drilldown.label || "明细下钻"}”规则的合成记录。`;
    $("weeklyFormula").textContent = tree.formula || "—";

    $("weeklyTaskStatus").textContent = task.status || "—";
    $("weeklyTaskOwner").textContent = task.owner_role || "—";
    $("weeklyTaskFocus").textContent = `${task.focus_dimension?.type || "—"}：${task.focus_dimension?.value || "—"}`;
    $("weeklyTaskDeadline").textContent = task.deadline || "—";
    $("weeklyTaskAction").textContent = task.action || "—";

    renderTree(tree.rows || []);
    renderDimension(dimension);
    renderDrilldown(drilldown);
    renderStrategy(effect);
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
