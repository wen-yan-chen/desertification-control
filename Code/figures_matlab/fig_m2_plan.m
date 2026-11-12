function fig_m2_plan()
%FIG_M2_PLAN Paper Fig. "Optimal 15-year trajectories of the four Task 2 decisions".
%   (a) New treated area a_t, belt stock A_t & operating PV P_t^{op},
%   (b) Ecological water replenishment Q_t (with May cap note) & labour L_t,
%   (c) Three annual spending streams vs 12 M cap & PV revenue R_t,
%   (d) Investment allocation ratios (f_t^b, f_t^o, f_t^p).
%   Data: Results/v7/model2/{annual.csv, monthly.csv, model2_results.json}
S = paper_style(); c = S.c;
a  = readtable(fullfile(S.res2, 'annual.csv'));
mo = readtable(fullfile(S.res2, 'monthly.csv'));
js = jsondecode(fileread(fullfile(S.res2, 'model2_results.json')));
cfg = js.config;
y = a.year;
xl = [0.3 15.7];

fig = new_figure(S.textW, 8.6);
tl = tiledlayout(fig, 2, 2, 'TileSpacing', 'compact', 'Padding', 'compact');

% (a) Area a_t, belt stock A_t (left) and operating PV P_t^{op} (right)
ax = nexttile(tl); style_axes(ax, S, 'y');
yyaxis(ax, 'left');
ax.YColor = c.veg;
b1 = bar(ax, y, a.new_area_ha, 0.58, 'FaceColor', c.vegMid, 'EdgeColor', 'none');
l1 = plot(ax, y, a.eco_area_ha, '-o', 'Color', c.veg, 'LineWidth', 1.3, ...
    'MarkerSize', 3.2, 'MarkerFaceColor', 'w', 'MarkerEdgeColor', c.veg);
ylim(ax, [0 375]); yticks(ax, 0:100:300); ylabel(ax, 'Area (ha)', 'Color', c.veg);

yyaxis(ax, 'right');
ax.YColor = c.pvDark;
l2 = plot(ax, y, a.pv_operating_kw / 1e3, '--s', 'Color', c.pvDark, 'LineWidth', 1.25, ...
    'MarkerSize', 3.1, 'MarkerFaceColor', c.accent, 'MarkerEdgeColor', c.pvDark);
ylim(ax, [0 12.5]); yticks(ax, 0:4:12); ylabel(ax, 'Operating PV (MW)', 'Color', c.pvDark);

yyaxis(ax, 'left');
xlim(ax, xl); xticks(ax, 1:2:15); ax.XTickLabel = [];
lg = legend(ax, [b1 l1 l2], {'New area {\ita_t} (150 ha, yrs 1–2)', ...
    'Belt stock {\itA_t} (300 ha)', 'Operating PV {\itP_t}^{op} (9.5 MW)'}, ...
    'Location', 'southeast', 'FontName', S.font, 'FontSize', S.fs.note - 0.3, 'Box', 'off');
lg.ItemTokenSize = [10 5];
panel_title(ax, '(a) Newly treated area and PV trajectory', S);
plot(ax, xl([1 2]), [375 375], '-', 'Color', S.c.axis, 'LineWidth', 0.6, 'HandleVisibility', 'off');

% (b) Water replenishment Q_t (left) and labour input L_t (right)
ax = nexttile(tl); style_axes(ax, S, 'y');
yyaxis(ax, 'left');
ax.YColor = c.water;
acap = cfg.annual_water_cap_m3 / 1e4;
plot(ax, xl, [acap acap], '--', 'Color', c.limit, 'LineWidth', 0.9, 'HandleVisibility', 'off');
text(ax, 15.3, acap + 4, 'annual water cap 150', 'FontName', S.font, ...
    'FontSize', S.fs.note - 0.5, 'Color', c.limit, 'HorizontalAlignment', 'right', 'VerticalAlignment', 'bottom');
bw = bar(ax, y, a.water_m3 / 1e4, 0.58, 'FaceColor', c.waterMid, 'EdgeColor', 'none');
sub8 = sortrows(mo(mo.year == 8, :), 'month');
may_pct = 100 * sub8.gross_water_m3(5) / sub8.cap_m3(5);
text(ax, 15.3, 114, sprintf('70%% yr cap (May: %.0f%% mo cap)', may_pct), ...
    'FontName', S.font, 'FontSize', S.fs.note - 0.4, 'Color', c.water, ...
    'FontWeight', 'bold', 'HorizontalAlignment', 'right');
ylim(ax, [0 228]); yticks(ax, 0:50:150); ylabel(ax, 'Water {\itQ_t} (10^4 m^3/yr)', 'Color', c.water);

yyaxis(ax, 'right');
ax.YColor = c.sand;
ll = plot(ax, y, a.labor_person_days / 1e3, '-o', 'Color', c.sand, 'LineWidth', 1.25, ...
    'MarkerSize', 3.1, 'MarkerFaceColor', 'w', 'MarkerEdgeColor', c.sand);
ylim(ax, [0 17.1]); yticks(ax, 0:4:12); ylabel(ax, 'Labour {\itL_t} (10^3 p-d/yr)', 'Color', c.sand);

yyaxis(ax, 'left');
xlim(ax, xl); xticks(ax, 1:2:15); ax.XTickLabel = [];
lg = legend(ax, [bw ll], {'Water {\itQ_t} (all cohorts)', 'Labour {\itL_t} (peak 5,522 p-d)'}, ...
    'Location', 'northwest', 'FontName', S.font, 'FontSize', S.fs.note - 0.5, 'Box', 'off');
lg.ItemTokenSize = [9 5];
panel_title(ax, '(b) Ecological water and labour scheduling', S);
plot(ax, xl([1 2]), [228 228], '-', 'Color', S.c.axis, 'LineWidth', 0.6, 'HandleVisibility', 'off');

% (c) Stacked annual spending streams vs PV revenue and 12 M cap
ax = nexttile(tl); style_axes(ax, S, 'y');
ann_cap = cfg.annual_budget_cny / 1e6;
plot(ax, xl, [ann_cap ann_cap], '--', 'Color', c.limit, 'LineWidth', 0.9, 'HandleVisibility', 'off');
text(ax, 15.4, ann_cap + 0.35, 'annual budget cap 12 M (scenario)', 'FontName', S.font, ...
    'FontSize', S.fs.note - 0.5, 'Color', c.limit, 'HorizontalAlignment', 'right', 'VerticalAlignment', 'bottom');
Smat = [a.construction_cny, a.om_cny, a.pv_facilities_cny] / 1e6;
bs = bar(ax, y, Smat, 0.64, 'stacked', 'EdgeColor', 'w', 'LineWidth', 0.4);
bs(1).FaceColor = c.vegMid;
bs(2).FaceColor = c.plum;
bs(3).FaceColor = c.accent;
lr = plot(ax, y, a.revenue_cny / 1e6, '-d', 'Color', c.ink, 'LineWidth', 1.25, ...
    'MarkerSize', 3.4, 'MarkerFaceColor', 'w', 'MarkerEdgeColor', c.ink);
xlim(ax, xl); xticks(ax, 1:2:15);
ylim(ax, [0 14.5]); yticks(ax, 0:4:12);
xlabel(ax, 'Project year'); ylabel(ax, 'million CNY');
lg = legend(ax, [bs(1) bs(2) bs(3) lr], {'Planting {\itC_t^b}', 'O&M+water {\itC_t^o}', ...
    'PV capex {\itC_t^p}', 'PV revenue {\itR_t}'}, 'Location', 'east', 'NumColumns', 2, ...
    'FontName', S.font, 'FontSize', S.fs.note - 0.5, 'Box', 'off');
lg.ItemTokenSize = [9 5];
panel_title(ax, '(c) Spending streams and PV revenue', S);
frame_axes(ax, S);

% (d) Spending share composition (%)
ax = nexttile(tl); style_axes(ax, S, 'y');
Fmat = [a.construction_fund_share, a.om_fund_share, a.pv_facilities_fund_share] * 100;
Fmat(isnan(Fmat)) = 0;
bf = bar(ax, y, Fmat, 0.64, 'stacked', 'EdgeColor', 'w', 'LineWidth', 0.4);
bf(1).FaceColor = c.vegMid;
bf(2).FaceColor = c.plum;
bf(3).FaceColor = c.accent;
text(ax, 10, 54, '100% O&M (yrs 5–15)', 'FontName', S.font, 'FontSize', S.fs.note - 0.3, ...
    'Color', c.plum, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', ...
    'BackgroundColor', 'w', 'EdgeColor', c.plum, 'Margin', 2);
xlim(ax, xl); xticks(ax, 1:2:15);
ylim(ax, [0 109]); yticks(ax, 0:25:100);
xlabel(ax, 'Project year'); ylabel(ax, 'Allocation ratio (%)');
panel_title(ax, '(d) Investment allocation ratios ({\itf_t^b}, {\itf_t^o}, {\itf_t^p})', S);
frame_axes(ax, S);

save_fig(fig, 'm2_plan', S);
end
