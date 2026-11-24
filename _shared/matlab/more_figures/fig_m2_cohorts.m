function fig_m2_cohorts()
%FIG_M2_COHORTS Paper Fig. "Cohort vegetation, irrigation, storage and effective area" (left half).
%   Data: Results/v7/model2/{cohorts.csv, annual.csv, model2_results.json}
S = paper_style(); c = S.c;
co = readtable(fullfile(S.res2, 'cohorts.csv'), 'TextType', 'string');
an = readtable(fullfile(S.res2, 'annual.csv'));
js = jsondecode(fileread(fullfile(S.res2, 'model2_results.json')));
K = js.m1_parameters.K_section_pct;
Ccap = js.m1_parameters.water.capacity_mm;

ids  = ["eco_y1_100_to_300_after_3", "eco_y1_ramp_100_300_600", "eco_y2_100_to_300_after_3"];
labs = ["A: yr 1, 100 ha (100\rightarrow300)", ...
        "B: yr 1, 50 ha (100\rightarrow300\rightarrow600)", ...
        "C: yr 2, 150 ha (100\rightarrow300)"];
cols = [c.vegMid; c.veg; c.water];
xl = [0.3 16.3];

fig = new_figure(S.halfW, 12.2);
tl = tiledlayout(fig, 4, 1, 'TileSpacing', 'compact', 'Padding', 'compact');
h = gobjects(1, 3);

% 1. Start-of-year cover proxy V_start (%)
ax = nexttile(tl); style_axes(ax, S, 'y');
plot(ax, xl, [K K], '--', 'Color', c.limit, 'LineWidth', 0.9, 'HandleVisibility', 'off');
text(ax, 0.7, K - 1.2, sprintf('ceiling {\\itK} = %.1f%%', K), 'FontName', S.font, ...
    'FontSize', S.fs.note - 0.5, 'Color', c.limit, 'VerticalAlignment', 'top');
for j = [1 3 2]
    s = sortrows(co(co.cohort_id == ids(j), :), 'year');
    if j == 2, s = s(s.year >= 7, :); end
    h(j) = plot(ax, s.year, s.V_start_pct, '-o', 'Color', cols(j, :), 'LineWidth', 1.3, ...
        'MarkerSize', 2.6, 'MarkerFaceColor', 'w', 'MarkerEdgeColor', cols(j, :));
end
sB = co(co.cohort_id == ids(2) & co.year == 15, :);
sA = co(co.cohort_id == ids(1) & co.year == 15, :);
text(ax, 15.25, sB.V_start_pct, sprintf('%.1f', sB.V_start_pct), 'FontName', S.font, ...
    'FontSize', S.fs.note - 0.3, 'Color', cols(2, :), 'FontWeight', 'bold');
text(ax, 15.25, sA.V_start_pct, sprintf('%.1f', sA.V_start_pct), 'FontName', S.font, ...
    'FontSize', S.fs.note - 0.3, 'Color', cols(1, :), 'FontWeight', 'bold');
xlim(ax, xl); xticks(ax, 1:2:15); ax.XTickLabel = [];
ylim(ax, [0 42]); yticks(ax, 0:10:30);
ylabel(ax, '%');
panel_title(ax, 'Start-of-year cover {\itV}_{start}', S);
frame_axes(ax, S);

% 2. Scheduled irrigation quota (mm/yr)
ax = nexttile(tl); style_axes(ax, S, 'y');
for j = [1 3 2]
    s = sortrows(co(co.cohort_id == ids(j), :), 'year');
    if j == 2, s = s(s.year >= 7, :); end
    stairs(ax, [s.year; s.year(end) + 0.6] - 0.3, [s.irrigation_mm_yr; s.irrigation_mm_yr(end)], ...
        '-', 'Color', cols(j, :), 'LineWidth', 1.35);
end
xlim(ax, xl); xticks(ax, 1:2:15); ax.XTickLabel = [];
ylim(ax, [0 690]); yticks(ax, [0 100 300 600]);
ylabel(ax, 'mm/yr');
panel_title(ax, 'Scheduled irrigation quota {\itq}_{{\itp},{\ith}}', S);
frame_axes(ax, S);

% 3. Year-end root-zone storage M (mm)
ax = nexttile(tl); style_axes(ax, S, 'y');
plot(ax, xl, [Ccap Ccap], '--', 'Color', c.limit, 'LineWidth', 0.9, 'HandleVisibility', 'off');
text(ax, 15.9, Ccap - 2, 'capacity {\itC} = 75 mm', 'FontName', S.font, ...
    'FontSize', S.fs.note - 0.5, 'Color', c.limit, 'HorizontalAlignment', 'right', 'VerticalAlignment', 'top');
for j = [1 3 2]
    s = sortrows(co(co.cohort_id == ids(j), :), 'year');
    if j == 2, s = s(s.year >= 7, :); end
    plot(ax, s.year, s.M_end_mm, '-', 'Color', cols(j, :), 'LineWidth', 1.3);
end
xlim(ax, xl); xticks(ax, 1:2:15); ax.XTickLabel = [];
ylim(ax, [0 86]); yticks(ax, 0:25:75);
ylabel(ax, 'mm');
panel_title(ax, 'Year-end soil store {\itM}', S);
frame_axes(ax, S);

% 4. Stacked effective area contribution (ha * V_start / K)
ax = nexttile(tl); style_axes(ax, S, 'y');
yrs = (1:15)';
Emat = zeros(15, 3);
for j = 1:3
    s = co(co.cohort_id == ids(j), :);
    [~, loc] = ismember(s.year, yrs);
    Emat(loc, j) = s.area_ha .* s.V_start_pct / K;
end
assert(max(abs(sum(Emat, 2) - an.effective_ha)) < 1e-6, 'Effective ha mismatch');
bs = bar(ax, yrs, Emat, 0.64, 'stacked', 'EdgeColor', 'w', 'LineWidth', 0.35);
for j = 1:3, bs(j).FaceColor = cols(j, :); end
text(ax, 0.8, 146, sprintf('15-yr sum {\\itH} = %.0f eff. ha\\cdotyr', sum(Emat, 'all')), ...
    'FontName', S.font, 'FontSize', S.fs.note, 'Color', c.ink, 'VerticalAlignment', 'top');
xlim(ax, xl); xticks(ax, 1:2:15);
ylim(ax, [0 162]); yticks(ax, 0:50:150);
xlabel(ax, 'Project year'); ylabel(ax, 'eff. ha');
panel_title(ax, 'Effective cover \Sigma {\ita}_{{\its},{\itp}} {\itV}_{start}/{\itK}', S);
frame_axes(ax, S);

lg = legend(h, labs, 'FontName', S.font, 'FontSize', S.fs.note - 0.4, ...
    'Box', 'off', 'NumColumns', 1);
lg.ItemTokenSize = [12 6];
lg.Layout.Tile = 'south';

save_fig(fig, 'm2_cohorts', S);
end
