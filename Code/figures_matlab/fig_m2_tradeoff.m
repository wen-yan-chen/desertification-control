function fig_m2_tradeoff()
%FIG_M2_TRADEOFF Paper Fig. "Ecology-cost trade-off across six solved targets".
%   (a) 6 unconnected solved points (net present cost vs ecological score),
%   (b) shelterbelt area built, (c) final PV installed, (d) MIP optimality gap.
%   Data: Results/v7/model2/{scenario_summary.csv, model2_results.json}
S = paper_style(); c = S.c;
ss = readtable(fullfile(S.res2, 'scenario_summary.csv'), 'TextType', 'string', 'VariableNamingRule', 'preserve');
js = jsondecode(fileread(fullfile(S.res2, 'model2_results.json')));
f = ss(ss.group == "frontier", :);
pct = [0 20 40 60 80 100]';
H = f.ecological_ha_year;
N = f.net_present_cost_cny / 1e6;

fig = new_figure(S.textW, 7.2);
tl = tiledlayout(fig, 3, 5, 'TileSpacing', 'compact', 'Padding', 'compact');

% (a) Left 3 columns x 3 rows: unconnected solved trade-off points
ax = nexttile(tl, 1, [3 3]); style_axes(ax, S, 'xy');
yline(ax, 0, ':', 'Color', c.greyDark, 'LineWidth', 0.8, 'HandleVisibility', 'off');
% Marginal slope guide annotations (without connecting into a fake continuous curve)
mc = diff(N) * 1e3 ./ diff(H); % k CNY per eff. ha-yr
plot(ax, H, N, 'o', 'MarkerSize', 5.8, 'MarkerFaceColor', c.plum, ...
    'MarkerEdgeColor', 'w', 'LineWidth', 0.7);
% Highlight 60% base case
ib = 4;
plot(ax, H(ib), N(ib), 'o', 'MarkerSize', 10.2, 'MarkerFaceColor', 'none', ...
    'MarkerEdgeColor', c.ink, 'LineWidth', 1.2);

dx = [ 55,  55,  55, -55, -55, -55];
dy = [ 1.5, 2.2, 2.2, 3.6, 3.2, -1.2];
ha = {'left','left','left','right','right','right'};
for k = 1:6
    tag = sprintf('%d%%: %.1f M', pct(k), N(k));
    if pct(k) == 60, tag = '60% (base): 25.3 M'; end
    if pct(k) == 0,  tag = sprintf('0%%: %s4.9 M', char(8722)); end
    fw = 'normal'; col = c.ink;
    if pct(k) == 60, fw = 'bold'; col = c.plum; end
    text(ax, H(k) + dx(k), N(k) + dy(k), tag, 'FontName', S.font, ...
        'FontSize', S.fs.note, 'FontWeight', fw, 'Color', col, 'HorizontalAlignment', ha{k});
end
text(ax, 2190, -12.5, sprintf(['Separate MILP solves (unconnected)\n' ...
    'Marginal \\Delta{\\itN}/\\Delta{\\itH}: %.1f \\rightarrow %.1f \\rightarrow %.1f k CNY / eff. ha\\cdotyr'], ...
    mc(1), mc(3), mc(5)), 'FontName', S.font, 'FontSize', S.fs.note - 0.4, ...
    'Color', c.greyDark, 'HorizontalAlignment', 'right', 'VerticalAlignment', 'bottom');

xlim(ax, [-150 2260]); xticks(ax, 0:500:2000);
ylim(ax, [-15 73]); yticks(ax, -10:20:70);
xlabel(ax, '15-year ecological score {\itH} (effective ha\cdotyr)');
ylabel(ax, 'Net present cost {\itN} (million CNY)');
panel_title(ax, '(a) Six solved cost–ecology points (lower {\itN} is cheaper)', S);
frame_axes(ax, S);

% (b) Shelterbelt area built (ha)
ax = nexttile(tl, 4, [1 2]); style_axes(ax, S, 'y');
bar(ax, pct, f.new_area_total_ha, 0.56, 'FaceColor', c.vegMid, 'EdgeColor', 'none');
for k = 1:6
    text(ax, pct(k), f.new_area_total_ha(k) + 35, sprintf('%.0f', f.new_area_total_ha(k)), ...
        'FontName', S.font, 'FontSize', S.fs.note - 0.5, 'Color', c.veg, ...
        'HorizontalAlignment', 'center', 'VerticalAlignment', 'bottom');
end
xlim(ax, [-12 112]); xticks(ax, pct); ax.XTickLabel = [];
ylim(ax, [0 1090]); yticks(ax, [0 500 900]);
ylabel(ax, 'ha');
panel_title(ax, '(b) Shelterbelt planted', S);
frame_axes(ax, S);

% (c) Final PV installed (MW)
ax = nexttile(tl, 9, [1 2]); style_axes(ax, S, 'y');
bar(ax, pct, f.pv_installed_final_kw / 1e3, 0.56, 'FaceColor', c.accent, 'EdgeColor', 'none');
for k = 1:6
    v = f.pv_installed_final_kw(k) / 1e3;
    if abs(v - round(v)) < 0.05, vs = sprintf('%.0f', v); else, vs = sprintf('%.1f', v); end
    text(ax, pct(k), v + 0.45, vs, 'FontName', S.font, ...
        'FontSize', S.fs.note - 0.5, 'Color', c.pvDark, ...
        'HorizontalAlignment', 'center', 'VerticalAlignment', 'bottom');
end
xlim(ax, [-12 112]); xticks(ax, pct); ax.XTickLabel = [];
ylim(ax, [0 12.4]); yticks(ax, [0 5 10]);
ylabel(ax, 'MW');
panel_title(ax, '(c) PV installed by year 15', S);
frame_axes(ax, S);

% (d) MIP optimality gap (%)
ax = nexttile(tl, 14, [1 2]); style_axes(ax, S, 'y');
tol = 100 * js.config.solver_relative_gap;
plot(ax, [-12 112], [tol tol], '--', 'Color', c.limit, 'LineWidth', 0.9);
text(ax, -9, tol + 0.015, 'tolerance 0.20%', 'FontName', S.font, ...
    'FontSize', S.fs.note - 0.6, 'Color', c.limit, 'VerticalAlignment', 'bottom');
plot(ax, pct, 100 * f.mip_gap, 'o', 'MarkerSize', 4.2, 'MarkerFaceColor', c.axis, ...
    'MarkerEdgeColor', 'w', 'LineWidth', 0.5);
xlim(ax, [-12 112]); xticks(ax, pct);
ylim(ax, [-0.03 0.28]); yticks(ax, [0 0.1 0.2]);
xlabel(ax, 'Target \phi (% of {\itH}_{max})');
ylabel(ax, '%');
panel_title(ax, '(d) MIP optimality gap', S);
frame_axes(ax, S);

save_fig(fig, 'm2_tradeoff', S);
end
