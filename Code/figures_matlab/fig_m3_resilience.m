function fig_m3_resilience()
%FIG_M3_RESILIENCE Paper Fig. "50-year post-construction resilience dynamics".
%   (a) Inherited M2 cohorts A, B, C cover trajectories & 5-95% path bands,
%   (b) First-passage ever-hit area vs currently low-cover area (recovery wedge),
%   (c) Non-stationary vs stationary vs no-random-disaster risk and H_eco(t),
%   (d) Conditional monthly water request, rationing & caps (normal vs drought).
%   Data: Results/v7/model3/{cohort_annual.csv, project_annual.csv, resources.csv, model3_results.json}
S = paper_style(); c = S.c;
js = check_m3_hashes(S);
ca = readtable(fullfile(S.res3, 'cohort_annual.csv'), 'TextType', 'string', 'VariableNamingRule', 'preserve');
pa = readtable(fullfile(S.res3, 'project_annual.csv'), 'TextType', 'string', 'VariableNamingRule', 'preserve');
rs = readtable(fullfile(S.res3, 'resources.csv'), 'TextType', 'string', 'VariableNamingRule', 'preserve');

K    = js.m1_parameters.K_section_pct;
crit = js.config.failure_cover_fraction_K * K; % 0.30 K = 11.423%
xl   = [0 50];

fig = new_figure(S.textW, 9.6);
tl  = tiledlayout(fig, 2, 2, 'TileSpacing', 'compact', 'Padding', 'loose');

% ==================== (a) Cohort cover trajectories & path spread ====================
ax = nexttile(tl); style_axes(ax, S, 'y');
cb = ca(ca.("case") == "base_nonstationary", :);
gA = sortrows(cb(cb.cohort_id == "eco_y1_100_to_300_after_3", :), 'post_year');
gB = sortrows(cb(cb.cohort_id == "eco_y1_ramp_100_300_600", :), 'post_year');
gC = sortrows(cb(cb.cohort_id == "eco_y2_100_to_300_after_3", :), 'post_year');
t  = gA.post_year;

% 5-95% path percentile bands (B and C)
pBandB = fill(ax, [t; flipud(t)], [gB.V_p05_pct; flipud(gB.V_p95_pct)], c.waterMid, ...
    'FaceAlpha', 0.17, 'EdgeColor', 'none');
pBandC = fill(ax, [t; flipud(t)], [gC.V_p05_pct; flipud(gC.V_p95_pct)], c.vegMid, ...
    'FaceAlpha', 0.18, 'EdgeColor', 'none');

% Diagnostic threshold 0.30 K = 11.423%
plot(ax, xl, [crit crit], '--', 'Color', c.limit, 'LineWidth', 0.95, 'HandleVisibility', 'off');
text(ax, 30.0, crit + 0.20, '0.30{\itK}', ...
    'FontName', S.font, 'FontSize', S.fs.note - 0.4, 'Color', c.limit, ...
    'HorizontalAlignment', 'left', 'VerticalAlignment', 'bottom');

lB = plot(ax, t, gB.V_mean_pct, '-',  'Color', c.water, 'LineWidth', 1.45);
lA = plot(ax, t, gA.V_mean_pct, '--', 'Color', c.sand,  'LineWidth', 1.25);
lC = plot(ax, t, gC.V_mean_pct, '-',  'Color', c.veg,   'LineWidth', 1.30);

xlim(ax, xl); xticks(ax, 0:10:50);
ylim(ax, [0 37]); yticks(ax, 0:10:30);
ylabel(ax, 'Cover proxy {\itV} (%)');
lg = legend(ax, [lB lC lA pBandB], {'B: 600 mm/yr', 'C: 300 mm/yr', 'A: 300 mm/yr', ...
    '5–95% range (B, C)'}, 'Location', 'north', 'NumColumns', 2, ...
    'FontName', S.font, 'FontSize', S.fs.note - 0.5, 'Box', 'off');
lg.ItemTokenSize = [10 5];
panel_title(ax, '(a) Cohort cover and uncertainty', S);
frame_axes(ax, S);

% ==================== (b) First-passage memory vs physical recovery ====================
ax = nexttile(tl); style_axes(ax, S, 'y');
pb = sortrows(pa(pa.("case") == "base_nonstationary", :), 'post_year');
tp = pb.post_year;
everA = pb.expected_ever_failed_area_ha;
currA = pb.expected_current_failed_area_ha;

plot(ax, xl, [300 300], '--', 'Color', c.limit, 'LineWidth', 0.85, 'HandleVisibility', 'off');
text(ax, 1.2, 304, 'Total belt: 300 ha', 'FontName', S.font, ...
    'FontSize', S.fs.note - 0.5, 'Color', c.limit, 'VerticalAlignment', 'bottom');

wRec = fill(ax, [tp; flipud(tp)], [currA; flipud(everA)], c.vegMid, ...
    'FaceAlpha', 0.24, 'EdgeColor', 'none');
lEver = plot(ax, tp, everA, '-', 'Color', c.plum,   'LineWidth', 1.45);
lCurr = plot(ax, tp, currA, '-', 'Color', c.pvDark, 'LineWidth', 1.45);

% Annotate year-50 recovery gap (299.45 vs 200.22 ha)
plot(ax, [50 50], [currA(end) everA(end)], '-', 'Color', c.veg, 'LineWidth', 1.1, 'HandleVisibility', 'off');
text(ax, 48.5, 0.5 * (currA(end) + everA(end)), sprintf('Recovered\n99.2 ha'), ...
    'FontName', S.font, 'FontSize', S.fs.note - 0.3, 'FontWeight', 'bold', ...
    'Color', c.veg, 'HorizontalAlignment', 'right');

xlim(ax, xl); xticks(ax, 0:10:50);
ylim(ax, [0 345]); yticks(ax, 0:100:300);
ylabel(ax, 'Expected belt area (ha)');
lg = legend(ax, [lEver lCurr wRec], {'Ever below warning', 'Currently below warning', 'Recovered area'}, ...
    'Location', 'southeast', 'FontName', S.font, 'FontSize', S.fs.note - 0.5, 'Box', 'off');
lg.ItemTokenSize = [10 5];
panel_title(ax, '(b) Cover loss and recovery', S);
frame_axes(ax, S);

% ==================== (c) Drift & random shocks: risk vs cumulative benefit ====================
ax = nexttile(tl); style_axes(ax, S, 'y');
ps = sortrows(pa(pa.("case") == "stationary_reference", :), 'post_year');
pn = sortrows(pa(pa.("case") == "no_random_disasters", :), 'post_year');

yyaxis(ax, 'left');
ax.YColor = c.plum;
fill(ax, [tp; flipud(tp)], [pb.ci95_low; flipud(pb.ci95_high)] * 100, c.plum, ...
    'FaceAlpha', 0.18, 'EdgeColor', 'none', 'HandleVisibility', 'off');
rBase = plot(ax, tp, pb.project_failure_probability * 100, '-',  'Color', c.plum, 'LineWidth', 1.4);
rStat = plot(ax, ps.post_year, ps.project_failure_probability * 100, '--', 'Color', c.plum, 'LineWidth', 1.1);
ylim(ax, [0 150]); yticks(ax, 0:25:100);
ylabel(ax, 'First-hit probability (%)', 'Color', c.plum);
% Keep the left label inside the figure margin on this dual-axis panel.
ax.YAxis(1).Label.Units = 'normalized';
ax.YAxis(1).Label.Position = [-0.10 0.5 0];

yyaxis(ax, 'right');
ax.YColor = c.veg;
fill(ax, [tp; flipud(tp)], [pb.cumulative_cover_ha_year_p05; flipud(pb.cumulative_cover_ha_year_p95)] / 1e3, ...
    c.vegMid, 'FaceAlpha', 0.16, 'EdgeColor', 'none', 'HandleVisibility', 'off');
hNoD  = plot(ax, pn.post_year, pn.cumulative_cover_ha_year_mean / 1e3, ':',  'Color', c.veg, 'LineWidth', 1.45);
% Omit the near-duplicate stationary benefit curve; retain stationary risk.
hBase = plot(ax, tp,           pb.cumulative_cover_ha_year_mean / 1e3, '-',  'Color', c.veg, 'LineWidth', 1.45);
ylim(ax, [0 11.25]); yticks(ax, 0:2:8);
ylabel(ax, '{\itH}_{eco} (10^3 eff. ha\cdotyr)', 'Color', c.veg);

yyaxis(ax, 'left');
xlim(ax, xl); xticks(ax, 0:10:50);
xlabel(ax, 'Post-construction year');
lg = legend(ax, [rBase rStat hBase hNoD], {'First-hit (base)', ...
    'First-hit (stationary)', '{\itH}_{eco} (base)', ...
    '{\itH}_{eco} (no shocks)'}, 'Location', 'north', 'NumColumns', 2, ...
    'FontName', S.font, 'FontSize', S.fs.note - 0.6, 'Box', 'off');
lg.ItemTokenSize = [9 5];
panel_title(ax, '(c) Risk and cumulative benefit', S);
plot(ax, xl([1 2]), [150 150], '-', 'Color', S.c.axis, 'LineWidth', 0.6, 'HandleVisibility', 'off');

% ==================== (d) Conditional monthly canal rationing (post-year 1) ====================
ax = nexttile(tl); style_axes(ax, S, 'y');
r1 = rs(rs.("case") == "base_nonstationary" & rs.post_year == 1, :);
rWet = sortrows(r1(strcmpi(string(r1.drought), "false"), :), 'month');
rDry = sortrows(r1(strcmpi(string(r1.drought), "true"),  :), 'month');
m = rWet.month;

% Grouped bars: Ecological request (= normal delivery) vs Drought rationed delivery
bMat = [rWet.requested_eco_m3, rDry.delivered_eco_m3] / 1e4;
bg = bar(ax, m, bMat, 0.78, 'grouped', 'EdgeColor', 'none');
bg(1).FaceColor = c.waterMid;
bg(2).FaceColor = c.water;

cWet = plot(ax, m, rWet.cap_m3 / 1e4, '--', 'Color', c.greyDark, 'LineWidth', 0.9);
cDry = plot(ax, m, rDry.cap_m3 / 1e4, '--o', 'Color', c.limit, 'LineWidth', 1.0, ...
    'MarkerSize', 2.6, 'MarkerFaceColor', 'w', 'MarkerEdgeColor', c.limit);

text(ax, 10.0, 26.0, 'May: -26%', 'FontName', S.font, ...
    'FontSize', S.fs.note - 0.5, 'FontWeight', 'bold', 'Color', c.limit, 'HorizontalAlignment', 'center');

xlim(ax, [0.4 12.6]); xticks(ax, 1:12);
xticklabels(ax, {'J','F','M','A','M','J','J','A','S','O','N','D'});
ylim(ax, [0 40]); yticks(ax, 0:6:24);
xlabel(ax, 'Month');
ylabel(ax, 'Water volume (10^4 m^3/mo)');
lg = legend(ax, [bg(1) bg(2) cWet cDry], {'Normal delivery', 'Drought delivery', 'Normal cap', 'Drought cap'}, ...
    'Location', 'north', 'NumColumns', 2, 'FontName', S.font, 'FontSize', S.fs.note - 0.6, 'Box', 'off');
lg.ItemTokenSize = [9 5];
panel_title(ax, '(d) Monthly water supply and caps', S);
frame_axes(ax, S);

tl.Units = 'normalized';
tl.OuterPosition = [0.025 0.025 0.95 0.95];
save_fig(fig, 'm3_resilience', S);
end
