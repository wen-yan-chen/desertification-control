function fig_m2_sensitivity()
%FIG_M2_SENSITIVITY Paper Fig. "Sensitivity of investment structure (PV, O&M and key drivers)".
%   Compact single-block 3-panel layout focused directly on Task 2's investment
%   sensitivity question at fixed ecological target H >= 1,258.2 eff. ha-yr.
%   Data: Results/v7/model2/{scenario_summary.csv, scenario_annual.csv, model2_results.json}
S = paper_style(); c = S.c;
ss = readtable(fullfile(S.res2, 'scenario_summary.csv'), 'TextType', 'string', 'VariableNamingRule', 'preserve');
sa = readtable(fullfile(S.res2, 'scenario_annual.csv'), 'TextType', 'string', 'VariableNamingRule', 'preserve');
js = jsondecode(fileread(fullfile(S.res2, 'model2_results.json')));
baseN = ss.net_present_cost_cny(ss.("case") == "base") / 1e6;
Btot  = js.config.total_budget_cny / 1e6;

cases = ["base", "no_pv", "pv_price_low", "pv_price_high", ...
         "pv_capex_low", "pv_capex_high", "pv_share_min_30pct", ...
         "om_low", "om_high", "eco_capex_low", "eco_capex_high", ...
         "water_low", "initial_cover_low", "initial_cover_high"];
labs  = ["Base (300 ha, 9.5 MW)", "No PV allowed", "PV tariff 0.15 CNY/kWh", ...
         "PV tariff 0.40 CNY/kWh", sprintf('PV capex %s25%% (2,250/kW)', char(8722)), ...
         "PV capex +25% (3,750/kW)", "PV spending share \geq 30%", ...
         sprintf('O&M unit costs %s50%%', char(8722)), "O&M unit costs +50%", ...
         sprintf('Planting capex %s25%%', char(8722)), "Planting capex +25%", ...
         sprintf('Water caps %s20%% (350 ha)', char(8722)), ...
         "Initial cover {\itV}_0 = 1% (400 ha)", "Initial cover {\itV}_0 = 4% (200 ha)"];

n = numel(cases);
yv = (n:-1:1)';
sub = table();
for k = 1:n, sub = [sub; ss(ss.("case") == cases(k), :)]; end %#ok<AGROW>
N   = sub.net_present_cost_cny / 1e6;
PV  = sub.pv_installed_final_kw / 1e3;
Sp  = zeros(n, 3);
for k = 1:n
    ak = sa(sa.("case") == cases(k), :);
    Sp(k, :) = [sum(ak.construction_cny), sum(ak.om_cny), sum(ak.pv_facilities_cny)] / 1e6;
end

fig = new_figure(S.textW, 6.3);
tl = tiledlayout(fig, 1, 3, 'TileSpacing', 'compact', 'Padding', 'compact');

% (a) Net present cost N (M CNY)
ax = nexttile(tl); style_axes(ax, S, 'x');
zebra(ax, n, [10.5 36.5], c.grid);
xline(ax, baseN, '--', 'Color', c.greyDark, 'LineWidth', 0.85, 'HandleVisibility', 'off');
yline(ax, 3.5, ':', 'Color', c.grey, 'LineWidth', 0.7, 'HandleVisibility', 'off');
for k = 1:n
    col = c.plum;
    if k > 11, col = c.water; end
    plot(ax, [baseN N(k)], [yv(k) yv(k)], '-', 'Color', c.grey, 'LineWidth', 1.3);
    plot(ax, N(k), yv(k), 'o', 'MarkerSize', 4.1, 'MarkerFaceColor', col, ...
        'MarkerEdgeColor', 'w', 'LineWidth', 0.5);
    dx = 0.55; ha = 'left';
    if N(k) < baseN - 0.1, dx = -0.55; ha = 'right'; end
    text(ax, N(k) + dx, yv(k), sprintf('%.1f', N(k)), 'FontName', S.font, ...
        'FontSize', S.fs.note - 0.6, 'Color', c.ink, 'HorizontalAlignment', ha);
end
xlim(ax, [10.5 36.5]); ylim(ax, [0.4 n + 0.6]);
yticks(ax, 1:n); yticklabels(ax, flip(labs));
ax.YAxis.TickLength = [0 0]; ax.YAxis.FontSize = S.fs.note - 0.3;
xlabel(ax, 'Net present cost {\itN} (M CNY)');
panel_title(ax, '(a) Net present cost', S);
frame_axes(ax, S);

% (b) Final PV installed (MW)
ax = nexttile(tl); style_axes(ax, S, 'x');
zebra(ax, n, [0 12.4], c.grid);
yline(ax, 3.5, ':', 'Color', c.grey, 'LineWidth', 0.7, 'HandleVisibility', 'off');
barh(ax, yv, PV, 0.60, 'FaceColor', c.accent, 'EdgeColor', 'none');
for k = 1:n
    text(ax, PV(k) + 0.25, yv(k), fmt_mw(PV(k)), 'FontName', S.font, ...
        'FontSize', S.fs.note - 0.6, 'Color', c.pvDark, 'HorizontalAlignment', 'left');
end
xlim(ax, [0 12.4]); xticks(ax, 0:5:10); ylim(ax, [0.4 n + 0.6]);
yticks(ax, 1:n); ax.YTickLabel = []; ax.YAxis.TickLength = [0 0];
xlabel(ax, 'PV installed (MW)');
panel_title(ax, '(b) Optimal PV scale', S);
frame_axes(ax, S);

% (c) 15-yr undiscounted investment structure (M CNY)
ax = nexttile(tl); style_axes(ax, S, 'x');
zebra(ax, n, [0 86], c.grid);
yline(ax, 3.5, ':', 'Color', c.grey, 'LineWidth', 0.7, 'HandleVisibility', 'off');
xline(ax, Btot, '--', 'Color', c.limit, 'LineWidth', 0.9, 'HandleVisibility', 'off');
text(ax, Btot - 1.5, 12.5, 'budget 80 M', 'FontName', S.font, ...
    'FontSize', S.fs.note - 0.6, 'Color', c.limit, 'HorizontalAlignment', 'right');
bh = barh(ax, yv, Sp, 0.60, 'stacked', 'EdgeColor', 'w', 'LineWidth', 0.35);
bh(1).FaceColor = c.vegMid; bh(2).FaceColor = c.plum; bh(3).FaceColor = c.accent;
xlim(ax, [0 86]); xticks(ax, 0:20:80); ylim(ax, [0.4 n + 0.6]);
yticks(ax, 1:n); ax.YTickLabel = []; ax.YAxis.TickLength = [0 0];
xlabel(ax, '15-yr gross spending (M CNY)');
lg = legend(ax, bh, {'Construction', 'O&M + water', 'PV capex'}, 'Orientation', 'horizontal', ...
    'Location', 'northoutside', 'FontName', S.font, 'FontSize', S.fs.note - 0.4, 'Box', 'off');
lg.ItemTokenSize = [10 5];
lg.Layout.Tile = 'south';
panel_title(ax, '(c) 15-year investment mix', S);
frame_axes(ax, S);

save_fig(fig, 'm2_sensitivity', S);
end

function zebra(ax, nrows, xl, col)
for r = 2:2:nrows
    patch(ax, xl([1 2 2 1]), r + [-0.5 -0.5 0.5 0.5], col, ...
        'EdgeColor', 'none', 'FaceAlpha', 0.55, 'HandleVisibility', 'off');
end
end

function s = fmt_mw(v)
if abs(v - round(v)) < 0.05, s = sprintf('%.0f', v); else, s = sprintf('%.1f', v); end
end
